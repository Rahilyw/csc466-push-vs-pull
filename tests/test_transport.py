"""Framing, delay, accounting and failure checks using TCP sockets."""

import asyncio
import json
import struct
import time

import pytest

from pushpull.transport import (
    MAX_MESSAGE_BYTES,
    ProtocolError,
    Traffic,
    Transport,
    encode_message,
    receive_message,
)


def test_fragmented_and_coalesced_frames_over_tcp():
    async def scenario():
        messages = [{"type": "first", "value": "café 🐾"}, {"type": "second"}]
        frames = b"".join(encode_message(m) for m in messages)
        received = asyncio.get_running_loop().create_future()

        async def handle(reader, writer):
            try:
                received.set_result([await receive_message(reader), await receive_message(reader)])
            except Exception as exc:
                received.set_exception(exc)
            finally:
                writer.close()
                await writer.wait_closed()

        async with await asyncio.start_server(handle, "127.0.0.1", 0) as server:
            reader, writer = await asyncio.open_connection(*server.sockets[0].getsockname())
            try:
                # Split the length prefix and payload, then combine the end of
                # the first frame and all of the second in one write.
                for part in (frames[:1], frames[1:3], frames[3:8], frames[8:]):
                    writer.write(part)
                    await writer.drain()
                    await asyncio.sleep(0)
                assert await asyncio.wait_for(received, 2) == messages
                assert await asyncio.wait_for(reader.read(), 2) == b""
            finally:
                writer.close()
                await writer.wait_closed()
        payload = json.dumps(messages[0], ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        frame = encode_message(messages[0])
        assert frame == struct.pack("!I", len(payload)) + payload

    asyncio.run(scenario())


@pytest.mark.parametrize("delay_ms", [0, 100])
def test_delay_and_sender_counters_on_request_and_reply(delay_ms):
    async def scenario():
        sender, responder = Transport(delay_ms=delay_ms), Transport(delay_ms=delay_ms)
        request = {"type": "pull_request", "versions": {"é": 2}}
        reply = {"type": "pull_reply", "records": []}
        handled = asyncio.get_running_loop().create_future()
        request_received_at = []

        async def handle(reader, writer):
            try:
                assert await receive_message(reader) == request
                request_received_at.append(time.monotonic())
                await responder.send_message(writer, reply)
                handled.set_result(None)
            except Exception as exc:
                handled.set_exception(exc)
            finally:
                writer.close()
                await writer.wait_closed()

        async with await asyncio.start_server(handle, "127.0.0.1", 0) as server:
            started = time.monotonic()
            result = await sender.exchange(server.sockets[0].getsockname(), request, reply=True)
            finished = time.monotonic()
            await asyncio.wait_for(handled, 2)
            assert result == reply
            # A lower bound checks both directions apply delay. No upper-bound
            # speed assertion: this is correctness, not a performance result.
            assert request_received_at[0] - started >= delay_ms / 1000
            assert finished - request_received_at[0] >= delay_ms / 1000
            assert sender.sent == {"pull_request": Traffic(1, len(encode_message(request)))}
            assert responder.sent == {"pull_reply": Traffic(1, len(encode_message(reply)))}
            snapshot = sender.sent
            snapshot.clear()
            assert sender.totals == Traffic(1, len(encode_message(request)))

    asyncio.run(scenario())


@pytest.mark.parametrize("frame", [
    b"\x00\x00",  # truncated header
    struct.pack("!I", 12) + b"{}",  # truncated payload
    struct.pack("!I", 0),
    struct.pack("!I", MAX_MESSAGE_BYTES + 1),
    struct.pack("!I", 1) + b"{",  # invalid JSON
    struct.pack("!I", 1) + b"\xff",  # invalid UTF-8
    struct.pack("!I", 2) + b"[]",  # JSON, but not a message object
    struct.pack("!I", 2) + b"{}",  # missing type
])
def test_rejects_malformed_frames_over_tcp(frame):
    async def scenario():
        handled = asyncio.get_running_loop().create_future()

        async def handle(reader, writer):
            try:
                with pytest.raises(ProtocolError):
                    await receive_message(reader)
                handled.set_result(None)
            except BaseException as exc:
                handled.set_exception(exc)
            finally:
                writer.close()
                await writer.wait_closed()

        async with await asyncio.start_server(handle, "127.0.0.1", 0) as server:
            _, writer = await asyncio.open_connection(*server.sockets[0].getsockname())
            writer.write(frame)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            await asyncio.wait_for(handled, 2)

    asyncio.run(scenario())


def test_exchange_timeout_closes_socket_without_counting_a_reply():
    async def scenario():
        finished = asyncio.get_running_loop().create_future()

        async def handle(reader, writer):
            try:
                assert (await receive_message(reader))["type"] == "pull_request"
                assert await reader.read() == b""
                finished.set_result(None)
            except Exception as exc:
                finished.set_exception(exc)
            finally:
                writer.close()
                await writer.wait_closed()

        async with await asyncio.start_server(handle, "127.0.0.1", 0) as server:
            transport = Transport(timeout=0.1)
            with pytest.raises(TimeoutError):
                await transport.exchange(
                    server.sockets[0].getsockname(), {"type": "pull_request", "versions": {}}, reply=True
                )
            await asyncio.wait_for(finished, 2)
            assert transport.totals.messages == 1

    asyncio.run(scenario())
