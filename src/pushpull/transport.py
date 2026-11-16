"""Length-prefixed UTF-8 JSON over TCP, with sender-side delay and counters.

Each frame has a four-byte unsigned big-endian payload length. Byte counters
include this application framing and the JSON payload, excluding TCP/IP headers.
Connections are short-lived: one push frame, or one pull request and one reply.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import math
import struct
import time
from typing import Any

Address = tuple[str, int]
MAX_MESSAGE_BYTES = 16 * 1024 * 1024


class ProtocolError(ValueError):
    """An invalid or incomplete application frame."""


@dataclass(frozen=True)
class Traffic:
    messages: int = 0
    bytes: int = 0


@dataclass(frozen=True)
class SendEvent:
    timestamp: float
    message_type: str
    bytes: int


def encode_message(message: dict[str, Any]) -> bytes:
    """Serialize once; the same bytes are sent and counted."""
    if not isinstance(message, dict) or not isinstance(message.get("type"), str):
        raise ProtocolError("message must be an object with a string type")
    payload = json.dumps(
        message, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    if len(payload) > MAX_MESSAGE_BYTES:
        raise ProtocolError("message exceeds size limit")
    return struct.pack("!I", len(payload)) + payload


async def receive_message(reader: asyncio.StreamReader) -> dict[str, Any]:
    """Read exactly one frame, even if TCP fragments or combines writes."""
    try:
        (size,) = struct.unpack("!I", await reader.readexactly(4))
        if not 0 < size <= MAX_MESSAGE_BYTES:
            raise ProtocolError("invalid message length")
        payload = await reader.readexactly(size)
    except asyncio.IncompleteReadError as exc:
        raise ProtocolError("truncated message") from exc
    try:
        message = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ProtocolError("invalid JSON payload") from exc
    if not isinstance(message, dict) or not isinstance(message.get("type"), str):
        raise ProtocolError("message must be an object with a string type")
    return message


class Transport:
    def __init__(self, *, delay_ms: float = 0, timeout: float = 5) -> None:
        if not math.isfinite(delay_ms) or delay_ms < 0:
            raise ValueError("delay_ms must be finite and nonnegative")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        self.delay_ms = delay_ms
        self.timeout = timeout
        self._sent: dict[str, Traffic] = {}
        self.events: list[SendEvent] = []

    @property
    def sent(self) -> dict[str, Traffic]:
        """Snapshot of successful sends by message type (including duplicates)."""
        return dict(self._sent)

    @property
    def totals(self) -> Traffic:
        return Traffic(
            sum(t.messages for t in self._sent.values()),
            sum(t.bytes for t in self._sent.values()),
        )

    async def send_message(
        self, writer: asyncio.StreamWriter, message: dict[str, Any]
    ) -> None:
        frame = encode_message(message)
        # Delay every frame, including empty pull replies, at its sender only.
        if self.delay_ms:
            await asyncio.sleep(self.delay_ms / 1000)
        writer.write(frame)
        await writer.drain()
        previous = self._sent.get(message["type"], Traffic())
        self._sent[message["type"]] = Traffic(
            previous.messages + 1, previous.bytes + len(frame)
        )
        self.events.append(SendEvent(time.monotonic(), message["type"], len(frame)))

    async def exchange(
        self, address: Address, message: dict[str, Any], *, reply: bool = False
    ) -> dict[str, Any] | None:
        """Send to one neighbour; optionally read one reply on the same socket.

        A send is counted after drain succeeds, not after remote acceptance.
        No automatic retry is made: failed exchanges raise to the caller.
        """
        async with asyncio.timeout(self.timeout):
            reader, writer = await asyncio.open_connection(*address)
            try:
                await self.send_message(writer, message)
                if reply:
                    return await receive_message(reader)
                return None
            finally:
                writer.close()
                await writer.wait_closed()
