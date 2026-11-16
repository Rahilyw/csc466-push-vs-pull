"""Seeded single-host experiment orchestration; sync traffic stays peer-to-peer.

Each spawned process owns one Peer. Pipes carry setup, workload writes and final
logs only; no store records are relayed between peers by the controller. All
processes use the host's shared monotonic clock, rather than wall-clock time.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
import csv
import hashlib
import json
import math
import multiprocessing as mp
from multiprocessing.connection import wait
import os
from pathlib import Path
import platform
import random
import time
import traceback

from pushpull.metrics import summarize
from pushpull.peer import Peer


@dataclass(frozen=True)
class Config:
    mode: str
    peers: int = 8
    rate: float = 1.0
    pull_interval: float = 0.5
    delay_ms: float = 0
    seed: int = 1
    duration: float = 60
    settle: float = 5
    idle: float = 20
    keys: int = 16

    def __post_init__(self):
        if self.mode not in {"push", "pull"}:
            raise ValueError("mode must be push or pull")
        if self.peers < 3 or self.keys < 1:
            raise ValueError("need at least three peers and one key")
        for name in ("rate", "pull_interval", "delay_ms", "duration", "settle", "idle"):
            value = getattr(self, name)
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and nonnegative")
        if min(self.pull_interval, self.duration, self.idle) <= 0:
            raise ValueError("pull_interval, duration and idle must be positive")


def make_workload(config: Config) -> list[dict]:
    """Regular update times; seeded keys/values; one fixed writer per key."""
    rng = random.Random(config.seed)
    updates = []
    for sequence in range(math.ceil(config.duration * config.rate)):
        offset = sequence / config.rate
        if offset >= config.duration:
            break
        key_index = rng.randrange(config.keys)
        updates.append({
            "sequence": sequence,
            "scheduled_offset": offset,
            "writer": key_index % config.peers,
            "key": f"key-{key_index}",
            "value": f"value-{sequence}-{rng.getrandbits(32):08x}",
        })
    return updates


def source_fingerprint() -> str:
    """Content provenance independent of local/unpublished commit IDs."""
    digest = hashlib.sha256()
    root = Path(__file__).resolve().parent
    for path in sorted(root.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


async def _worker_loop(peer_id, config, connection):
    peer = Peer(
        peer_id, mode=config.mode, delay_ms=config.delay_ms,
        pull_interval=config.pull_interval,
    )
    created = []
    starter = None
    try:
        await peer.start(periodic_pull=False)
        connection.send({"event": "ready", "address": peer.address, "pid": os.getpid()})
        while True:
            # Polling keeps control portable across spawn platforms without a
            # blocked executor thread preventing process shutdown.
            if not connection.poll():
                await asyncio.sleep(0.002)
                continue
            command = connection.recv()
            action = command["action"]
            if action == "configure":
                peer.neighbours = tuple(tuple(a) for a in command["neighbours"])
                connection.send({"event": "configured"})
            elif action == "start":
                async def start_at(timestamp):
                    await asyncio.sleep(max(0, timestamp - time.monotonic()))
                    if config.mode == "pull":
                        peer.start_polling()
                starter = asyncio.create_task(start_at(command["timestamp"]))
                connection.send({"event": "started"})
            elif action == "write":
                update = command["update"]
                record = await peer.local_write(update["key"], update["value"])
                event = next(
                    e for e in reversed(peer.acceptances)
                    if e.key == record.key and e.version == record.version
                )
                created.append({**update, "version": record.version, "timestamp": event.timestamp})
            elif action == "finish":
                # Capture before shutdown; cancellations must not become measured
                # synchronization failures. Metrics exclude events after end.
                result = {
                    "event": "finished", "peer_id": peer_id, "pid": os.getpid(),
                    "updates": created,
                    "acceptances": [asdict(e) for e in peer.acceptances],
                    "traffic": [{**asdict(e), "peer_id": peer_id} for e in peer.transport.events],
                    "records": [asdict(r) for r in peer.store.newer_than({})],
                    "errors": [repr(e) for e in peer.errors],
                }
                connection.send(result)
                # Keep serving until the controller has collected every peer.
                # Stopping here would create connection failures in neighbours
                # whose end-of-window snapshot has not been captured yet.
            elif action == "stop":
                return
            else:
                raise ValueError(f"unknown control action: {action}")
    finally:
        if starter is not None:
            starter.cancel()
            await asyncio.gather(starter, return_exceptions=True)
        await peer.stop()


def _worker(peer_id, config, connection):
    try:
        asyncio.run(_worker_loop(peer_id, config, connection))
    except BaseException:
        try:
            connection.send({"event": "error", "detail": traceback.format_exc()})
        except (BrokenPipeError, EOFError, OSError):
            pass
        raise
    finally:
        connection.close()


def _collect(connections, expected, timeout=20):
    pending = {connection: index for index, connection in enumerate(connections)}
    results = [None] * len(connections)
    deadline = time.monotonic() + timeout
    while pending:
        ready = wait(pending, timeout=max(0, deadline - time.monotonic()))
        if not ready:
            raise TimeoutError(f"waiting for {expected} from peers {list(pending.values())}")
        for connection in ready:
            result = connection.recv()
            if result.get("event") != expected:
                raise RuntimeError(f"peer {pending[connection]}: {result}")
            results[pending.pop(connection)] = result
    return results


def _write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_experiment(config: Config, output: Path) -> dict:
    """Run fixed workload/settling/idle windows and persist auditable raw logs.

    Existing result directories are never overwritten. Child failures propagate;
    every exit path joins workers and terminates a worker that cannot shut down.
    """
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    workload = make_workload(config)
    context = mp.get_context("spawn")
    processes, connections = [], []
    try:
        for peer_id in range(config.peers):
            parent, child = context.Pipe()
            process = context.Process(target=_worker, args=(peer_id, config, child))
            try:
                process.start()
            except BaseException:
                parent.close()
                child.close()
                raise
            child.close()
            processes.append(process)
            connections.append(parent)
        ready = _collect(connections, "ready")
        for index, connection in enumerate(connections):
            connection.send({"action": "configure", "neighbours": [
                ready[(index - 1) % config.peers]["address"],
                ready[(index + 1) % config.peers]["address"],
            ]})
        _collect(connections, "configured")
        start = time.monotonic() + 0.5
        for connection in connections:
            connection.send({"action": "start", "timestamp": start})
        _collect(connections, "started")
        if time.monotonic() >= start:
            raise RuntimeError("workers did not acknowledge start before observation window")
        for update in workload:
            time.sleep(max(0, start + update["scheduled_offset"] - time.monotonic()))
            connections[update["writer"]].send({"action": "write", "update": update})
        idle_start = start + config.duration + config.settle
        end = idle_start + config.idle
        time.sleep(max(0, end - time.monotonic()))
        for connection in connections:
            connection.send({"action": "finish"})
        logs = _collect(connections, "finished")
        updates = sorted((u for log in logs for u in log["updates"]), key=lambda u: u["sequence"])
        acceptances = sorted((e for log in logs for e in log["acceptances"]), key=lambda e: e["timestamp"])
        traffic = sorted((e for log in logs for e in log["traffic"]), key=lambda e: e["timestamp"])
        errors = [{"peer_id": log["peer_id"], "error": e} for log in logs for e in log["errors"]]
        if len(updates) != len(workload):
            errors.append({"error": "created update count differs from scheduled workload"})
        metrics = summarize(
            updates, acceptances, traffic, peers=config.peers, start=start,
            convergence_deadline=idle_start, idle_start=idle_start, end=end,
        )
        final_records = {}
        for update in updates:
            final_records[update["key"]] = {k: update[k] for k in ("key", "value", "version", "writer")}
        final_state_matches = all(
            {r["key"]: r for r in log["records"]} == final_records for log in logs
        )
        if metrics["converged"] and not final_state_matches:
            errors.append({"error": "final records do not match the workload at every peer"})
        result = {
            "schema_version": 1,
            "status": "error" if errors else "converged" if metrics["converged"] else "timeout",
            "config": asdict(config),
            "environment": {"python": platform.python_version(), "platform": platform.platform()},
            "source_sha256": source_fingerprint(),
            "workload_sha256": hashlib.sha256(json.dumps(workload, sort_keys=True).encode()).hexdigest(),
            "windows": {"start": start, "workload_end": start + config.duration,
                        "convergence_deadline": idle_start, "idle_start": idle_start, "end": end},
            "metrics": metrics,
            "process_ids": [log["pid"] for log in logs],
            "final_state_matches": final_state_matches,
            "final_records": final_records,
            "errors": errors,
        }
        _write_csv(output / "workload.csv", workload, ["sequence", "scheduled_offset", "writer", "key", "value"])
        _write_csv(output / "updates.csv", updates, ["sequence", "scheduled_offset", "timestamp", "writer", "key", "value", "version"])
        _write_csv(output / "acceptances.csv", acceptances, ["timestamp", "peer_id", "key", "version"])
        _write_csv(output / "traffic.csv", traffic, ["timestamp", "peer_id", "message_type", "bytes"])
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result
    except BaseException:
        (output / "failure.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise
    finally:
        for connection in connections:
            try:
                connection.send({"action": "stop"})
            except (BrokenPipeError, EOFError, OSError):
                pass
        for process in processes:
            process.join(timeout=2)
            if process.is_alive():
                process.terminate()
                process.join(timeout=2)
            if process.is_alive():
                process.kill()
                process.join()
            process.close()
        for connection in connections:
            connection.close()
