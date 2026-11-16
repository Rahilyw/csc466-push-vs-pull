"""Four-peer correctness checks over real TCP loopback sockets, not benchmarks."""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import asdict
import time

import pytest

from pushpull.peer import Peer
from pushpull.transport import Traffic, Transport, encode_message


@asynccontextmanager
async def ring(mode, delay_ms):
    peers = [
        Peer(i, mode=mode, delay_ms=delay_ms, pull_interval=0.05)
        for i in range(4)
    ]
    try:
        for peer in peers:
            await peer.start(periodic_pull=False)
        for i, peer in enumerate(peers):
            peer.neighbours = (peers[(i - 1) % 4].address, peers[(i + 1) % 4].address)
        yield peers
    finally:
        await asyncio.gather(*(peer.stop() for peer in peers))


async def eventually(predicate, peers, timeout=8):
    try:
        async with asyncio.timeout(timeout):
            while not predicate():
                assert all(not peer.errors for peer in peers), [p.errors for p in peers]
                await asyncio.sleep(0.01)
    except TimeoutError:
        pytest.fail(f"no convergence: {[p.store.version_vector() for p in peers]}")
    assert all(not peer.errors for peer in peers), [p.errors for p in peers]


def holds(peers, records):
    return all(peer.store.get(key) == record for peer in peers for key, record in records.items())


@pytest.mark.parametrize("mode", ["push", "pull"])
@pytest.mark.parametrize("delay_ms", [0, 100])
def test_four_peer_final_versions(mode, delay_ms):
    async def scenario():
        async with ring(mode, delay_ms) as peers:
            if mode == "pull":
                for peer in peers:
                    peer.start_polling()
            initial = await asyncio.gather(
                *(peer.local_write(f"key-{i}", "initial") for i, peer in enumerate(peers))
            )
            expected = {record.key: record for record in initial}
            await eventually(lambda: holds(peers, expected), peers)

            # A later wave proves the periodic pull loop keeps running. Versions
            # may be skipped en route, so convergence means final record equality.
            await peers[0].local_write("key-0", "intermediate")
            expected["key-0"] = await peers[0].local_write("key-0", "final 🐾")
            expected["key-2"] = await peers[2].local_write("key-2", "final")
            await eventually(lambda: holds(peers, expected), peers)
            finished = time.monotonic()
            for peer in peers:
                events = peer.acceptances
                assert len({(e.key, e.version) for e in events}) == len(events)
                assert [e.timestamp for e in events] == sorted(e.timestamp for e in events)
                assert all(e.peer_id == peer.peer_id and e.timestamp <= finished for e in events)
                for key, record in expected.items():
                    event = next(e for e in events if (e.key, e.version) == (key, record.version))
                    created = next(
                        e for e in peers[record.writer].acceptances
                        if (e.key, e.version) == (key, record.version)
                    )
                    assert event.timestamp >= created.timestamp

    asyncio.run(scenario())


@pytest.mark.parametrize("delay_ms", [0, 100])
def test_push_forwards_once_and_drops_duplicate_and_stale(delay_ms):
    async def scenario():
        async with ring("push", delay_ms) as peers:
            first = await peers[0].local_write("k", "first")
            await eventually(
                lambda: holds(peers, {"k": first})
                and sum(p.transport.totals.messages for p in peers) == 8,
                peers,
            )
            final = await peers[0].local_write("k", "final")
            await eventually(
                lambda: holds(peers, {"k": final})
                and sum(p.transport.totals.messages for p in peers) == 16,
                peers,
            )
            snapshot = [(p.transport.totals, list(p.acceptances)) for p in peers]
            injector = Transport(delay_ms=delay_ms)
            await asyncio.gather(*(
                injector.exchange(p.address, {"type": "push", "record": asdict(record)})
                for p in peers for record in (first, final)
            ))
            # Give any erroneous forwarding multiple delayed hops to show up.
            await asyncio.sleep(0.05 + 3 * delay_ms / 1000)
            assert [(p.transport.totals, p.acceptances) for p in peers] == snapshot
            assert holds(peers, {"k": final})
            frame_bytes = sum(
                len(encode_message({"type": "push", "record": asdict(r)}))
                for r in (first, final)
            )
            for peer in peers:
                assert peer.transport.sent == {"push": Traffic(4, 2 * frame_bytes)}
                assert not peer.errors
            assert injector.totals.messages == 8

    asyncio.run(scenario())


@pytest.mark.parametrize("delay_ms", [0, 100])
def test_pull_poll_one_request_one_reply_per_neighbour(delay_ms):
    async def scenario():
        async with ring("pull", delay_ms) as peers:
            caller, left, opposite, right = peers
            own = await caller.local_write("own", "local")
            old = await left.local_write("left", "old")
            remote = await right.local_write("right", "remote")
            await opposite.local_write("opposite", "two hops away")
            await caller.poll_once()
            assert caller.store.version_vector() == {"own": 1, "left": 1, "right": 1}
            assert all(len(p.acceptances) == (3 if p is caller else 1) for p in peers)
            newer = await left.local_write("left", "newer")

            async def check_poll(reply_records):
                before = [p.transport.totals for p in peers]
                summary = caller.store.version_vector()
                events_before = len(caller.acceptances)
                await caller.poll_once()
                request_size = len(encode_message({"type": "pull_request", "versions": summary}))
                assert caller.transport.totals == Traffic(
                    before[0].messages + 2, before[0].bytes + 2 * request_size
                )
                for peer, index in ((left, 1), (right, 3)):
                    records = reply_records[index]
                    reply_size = len(encode_message({
                        "type": "pull_reply", "records": [asdict(r) for r in records]
                    }))
                    assert peer.transport.totals == Traffic(
                        before[index].messages + 1, before[index].bytes + reply_size
                    )
                assert opposite.transport.totals == before[2] == Traffic()
                assert len(caller.acceptances) == events_before + sum(map(len, reply_records.values()))

            # Only left's newer record is returned; right must send an empty reply.
            await check_poll({1: [newer], 3: []})
            assert holds([caller], {"own": own, "left": newer, "right": remote})
            assert old.version < newer.version
            # An idle poll still sends exactly two requests and two empty replies.
            await check_poll({1: [], 3: []})
            assert caller.transport.sent["pull_request"].messages == 6
            assert left.transport.sent["pull_reply"].messages == 3
            assert right.transport.sent["pull_reply"].messages == 3
            assert all(not p.errors for p in peers)

    asyncio.run(scenario())


def test_stop_closes_pending_frame_and_periodic_poller():
    async def scenario():
        peer = Peer(0, mode="pull")
        await peer.start()
        address = peer.address
        reader, writer = await asyncio.open_connection(*address)
        try:
            writer.write(b"\x00")  # Leave an inbound length prefix incomplete.
            await writer.drain()
            await asyncio.sleep(0.01)
            await asyncio.wait_for(peer.stop(), 1)
            assert await asyncio.wait_for(reader.read(), 1) == b""
            await peer.stop()  # Cleanup is idempotent.
            assert not peer.errors
            with pytest.raises(OSError):
                await asyncio.open_connection(*address)
        finally:
            writer.close()
            await writer.wait_closed()
            await peer.stop()

    asyncio.run(scenario())
