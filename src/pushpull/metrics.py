"""Metrics from monotonic acceptance/send events on one host.

An acceptance of a newer version satisfies an older update too. Missing samples
are counted explicitly; the reported median/p95 describe observed samples only.
Communication uses a fixed window so push and pull see the same run duration.
"""

from collections import defaultdict
import math
from statistics import median


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def summarize(
    updates: list[dict],
    acceptances: list[dict],
    traffic: list[dict],
    *,
    peers: int,
    start: float,
    convergence_deadline: float,
    idle_start: float,
    end: float,
) -> dict:
    if not start <= convergence_deadline <= idle_start < end:
        raise ValueError("invalid observation windows")
    accepted = defaultdict(list)
    for event in acceptances:
        if start <= event["timestamp"] <= convergence_deadline:
            accepted[event["peer_id"], event["key"]].append(event)

    def reached(peer, update):
        return min((
            event["timestamp"] for event in accepted[peer, update["key"]]
            if event["version"] >= update["version"]
            and event["timestamp"] >= update["timestamp"]
        ), default=None)

    delays = []
    final = {}
    for update in updates:
        if update["key"] not in final or update["version"] > final[update["key"]]["version"]:
            final[update["key"]] = update
        for peer in range(peers):
            timestamp = reached(peer, update)
            if timestamp is not None:
                delays.append(timestamp - update["timestamp"])
    final_times = [reached(peer, update) for update in final.values() for peer in range(peers)]
    converged = all(t is not None for t in final_times)
    last_update = max((u["timestamp"] for u in updates), default=start)
    convergence = (
        max(final_times, default=last_update) - last_update if converged else None
    )
    by_type = defaultdict(lambda: {"messages": 0, "bytes": 0})
    idle_messages = idle_bytes = 0
    for event in traffic:
        if start <= event["timestamp"] < end:
            counts = by_type[event["message_type"]]
            counts["messages"] += 1
            counts["bytes"] += event["bytes"]
            if event["timestamp"] >= idle_start:
                idle_messages += 1
                idle_bytes += event["bytes"]
    expected = len(updates) * peers
    return {
        "converged": converged,
        "propagation_samples": len(delays),
        "expected_propagation_samples": expected,
        "missing_propagation_samples": expected - len(delays),
        "propagation_median_seconds": median(delays) if delays else None,
        "propagation_p95_seconds": percentile(delays, 0.95),
        "final_convergence_seconds": convergence,
        "window_seconds": end - start,
        "messages": sum(c["messages"] for c in by_type.values()),
        "bytes": sum(c["bytes"] for c in by_type.values()),
        "by_message_type": dict(by_type),
        "idle_seconds": end - idle_start,
        "idle_messages": idle_messages,
        "idle_bytes": idle_bytes,
        "idle_messages_per_second": idle_messages / (end - idle_start),
        "idle_bytes_per_second": idle_bytes / (end - idle_start),
    }


def aggregate_results(results: list[dict]) -> list[dict]:
    """Summarize matched, complete repetitions; never hide failed/missing runs.

    Latency fields are means of each run's median/p95, not pooled quantiles.
    Standard deviations are across repetitions, not confidence intervals.
    """
    from statistics import mean, stdev

    if not results:
        raise ValueError("no results")
    groups = defaultdict(list)
    workloads = {}
    source = results[0]["source_sha256"]
    fixed = {k: v for k, v in results[0]["config"].items() if k not in {"mode", "delay_ms", "seed"}}
    for result in results:
        config = result["config"]
        if result["status"] != "converged" or result["metrics"]["missing_propagation_samples"]:
            raise ValueError("cannot compare incomplete runs; inspect raw results")
        if result["source_sha256"] != source:
            raise ValueError("mixed source fingerprints")
        if {k: v for k, v in config.items() if k not in {"mode", "delay_ms", "seed"}} != fixed:
            raise ValueError("mixed fixed experiment parameters")
        seed = config["seed"]
        if seed in workloads and workloads[seed] != result["workload_sha256"]:
            raise ValueError("workloads differ for the same seed")
        workloads[seed] = result["workload_sha256"]
        groups[config["mode"], config["delay_ms"]].append(result)
    seed_sets = []
    for runs in groups.values():
        seeds = [r["config"]["seed"] for r in runs]
        if len(set(seeds)) != len(seeds):
            raise ValueError("duplicate seed within a configuration")
        seed_sets.append(set(seeds))
    if any(seeds != seed_sets[0] for seeds in seed_sets):
        raise ValueError("configuration seed sets differ")
    rows = []
    for (mode, delay), runs in sorted(groups.items()):
        row = {"mode": mode, "delay_ms": delay, "runs": len(runs)}
        for metric, label, scale in (
            ("propagation_median_seconds", "run_median_ms", 1000),
            ("propagation_p95_seconds", "run_p95_ms", 1000),
            ("final_convergence_seconds", "convergence_ms", 1000),
            ("messages", "messages", 1), ("bytes", "bytes", 1),
            ("idle_messages_per_second", "idle_messages_per_second", 1),
            ("idle_bytes_per_second", "idle_bytes_per_second", 1),
        ):
            values = [r["metrics"][metric] * scale for r in runs if r["metrics"][metric] is not None]
            row[f"mean_{label}"] = mean(values) if values else None
            row[f"std_{label}"] = stdev(values) if len(values) > 1 else None
        rows.append(row)
    return rows
