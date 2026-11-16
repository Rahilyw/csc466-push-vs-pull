"""An asyncio TCP peer with push forwarding or periodic one-round-trip pull.

The API runs inside one event loop per process. Tests may run several peers in
one loop; the experiment process launcher and log export remain separate work.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from dataclasses import asdict, dataclass
import math
import socket
import time
from typing import Any

from pushpull.store import Record, VersionedStore
from pushpull.transport import Address, ProtocolError, Transport, receive_message


@dataclass(frozen=True)
class Acceptance:
    timestamp: float  # time.monotonic(), seconds
    peer_id: int
    key: str
    version: int


def _record_from_json(data: Any) -> Record:
    if not isinstance(data, dict) or set(data) != {"key", "value", "version", "writer"}:
        raise ProtocolError("invalid record fields")
    if not isinstance(data["key"], str) or not isinstance(data["value"], str):
        raise ProtocolError("record key and value must be strings")
    if type(data["version"]) is not int or data["version"] <= 0:
        raise ProtocolError("record version must be a positive integer")
    if type(data["writer"]) is not int or data["writer"] < 0:
        raise ProtocolError("record writer must be a nonnegative integer")
    return Record(**data)


class Peer:
    def __init__(
        self,
        peer_id: int,
        *,
        mode: str,
        neighbours: tuple[Address, ...] = (),
        host: str = "127.0.0.1",
        port: int = 0,
        pull_interval: float = 0.5,
        delay_ms: float = 0,
        timeout: float = 5,
    ) -> None:
        if mode not in {"push", "pull"}:
            raise ValueError("mode must be push or pull")
        if not math.isfinite(pull_interval) or pull_interval <= 0:
            raise ValueError("pull_interval must be finite and positive")
        self.peer_id = peer_id
        self.mode = mode
        self.neighbours = neighbours
        self.pull_interval = pull_interval
        self.store = VersionedStore()
        self.transport = Transport(delay_ms=delay_ms, timeout=timeout)
        self.acceptances: list[Acceptance] = []
        # Background failures are retained for the runner/tests, never hidden.
        self.errors: list[Exception] = []
        self._bind_address = (host, port)
        self._listener: socket.socket | None = None
        self._acceptor: asyncio.Task[None] | None = None
        self._poller: asyncio.Task[None] | None = None
        self._handlers: set[asyncio.Task[None]] = set()
        self._poll_lock = asyncio.Lock()

    @property
    def address(self) -> Address:
        if self._listener is None:
            raise RuntimeError("peer is not listening")
        host, port = self._listener.getsockname()[:2]
        return host, port

    async def start(self, *, periodic_pull: bool = True) -> None:
        """Bind TCP (port 0 chooses a free port) and optionally start polling.

        For dynamic rings, start all peers with periodic_pull=False, assign
        their neighbours from peer.address, then call start_polling().
        """
        if self._listener is not None:
            raise RuntimeError("peer is already started")
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.setblocking(False)
            listener.bind(self._bind_address)
            listener.listen(128)
        except BaseException:
            listener.close()
            raise
        self._listener = listener
        self._acceptor = asyncio.create_task(self._accept_loop(listener))
        if periodic_pull and self.mode == "pull":
            self.start_polling()

    def start_polling(self) -> None:
        if self._listener is None or self.mode != "pull":
            raise RuntimeError("polling requires a started pull peer")
        if self._poller is not None:
            raise RuntimeError("polling is already running")
        self._poller = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        """Join the accept loop before closing its socket, then stop handlers."""
        listener, self._listener = self._listener, None
        if self._poller is not None:
            self._poller.cancel()
            await asyncio.gather(self._poller, return_exceptions=True)
            self._poller = None
        if listener is not None:
            # Wake sock_accept rather than cancelling it between accepting a
            # socket and taking ownership. Owning the accept loop also avoids
            # Python 3.12's Server.close/_attach race with pending TCP accepts.
            try:
                if self._acceptor is not None and not self._acceptor.done():
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as wake:
                        wake.setblocking(False)
                        host, port = listener.getsockname()
                        await asyncio.get_running_loop().sock_connect(
                            wake, ("127.0.0.1" if host == "0.0.0.0" else host, port)
                        )
                if self._acceptor is not None:
                    await self._acceptor
            finally:
                listener.close()
                self._acceptor = None
        handlers = list(self._handlers)
        for task in handlers:
            task.cancel()
        await asyncio.gather(*handlers, return_exceptions=True)

    def _log_acceptance(self, record: Record) -> None:
        self.acceptances.append(
            Acceptance(time.monotonic(), self.peer_id, record.key, record.version)
        )

    async def local_write(self, key: str, value: str) -> Record:
        if self._listener is None:
            raise RuntimeError("peer is not started")
        record = self.store.local_write(key, value, writer=self.peer_id)
        self._log_acceptance(record)
        if self.mode == "push":
            await self._forward(record)
        return record

    async def _apply(self, record: Record) -> None:
        # Store mutation and acceptance logging contain no await: duplicate
        # arrivals cannot both accept a version in this event loop.
        if self.store.apply(record):
            self._log_acceptance(record)
            if self.mode == "push":
                await self._forward(record)

    async def _forward(self, record: Record) -> None:
        message = {"type": "push", "record": asdict(record)}
        await self._all_neighbours(
            [self.transport.exchange(address, message) for address in self.neighbours]
        )

    async def _all_neighbours(self, exchanges: list[Awaitable[Any]]) -> None:
        # Join every exchange even if a neighbour fails; none outlive the caller.
        results = await asyncio.gather(*exchanges, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                raise result

    async def poll_once(self) -> None:
        """One summary request and one records reply per neighbour, concurrently."""
        if self.mode != "pull" or self._listener is None:
            raise RuntimeError("polling requires a started pull peer")
        async with self._poll_lock:
            message = {"type": "pull_request", "versions": self.store.version_vector()}

            async def poll(address: Address) -> None:
                response = await self.transport.exchange(address, message, reply=True)
                if response is None or response["type"] != "pull_reply":
                    raise ProtocolError("expected pull_reply")
                records = response.get("records")
                if not isinstance(records, list):
                    raise ProtocolError("pull reply records must be a list")
                for record in [_record_from_json(item) for item in records]:
                    await self._apply(record)

            await self._all_neighbours([poll(address) for address in self.neighbours])

    async def _poll_loop(self) -> None:
        while True:
            started = time.monotonic()
            try:
                await self.poll_once()
            except Exception as exc:
                self.errors.append(exc)
            # No overlapping polls. If a round exceeds the interval, the next
            # starts immediately; otherwise preserve the start-to-start period.
            await asyncio.sleep(max(0, self.pull_interval - (time.monotonic() - started)))

    async def _accept_loop(self, listener: socket.socket) -> None:
        loop = asyncio.get_running_loop()
        while True:
            try:
                client, _ = await loop.sock_accept(listener)
            except OSError as exc:
                self.errors.append(exc)
                return
            if self._listener is None:
                client.close()
                return
            task = asyncio.create_task(self._serve_client(client))
            self._handlers.add(task)

            def finished(task: asyncio.Task[None], client=client) -> None:
                # Even cancellation before the first task step releases the fd.
                client.close()
                self._handlers.discard(task)

            task.add_done_callback(finished)

    async def _serve_client(self, client: socket.socket) -> None:
        try:
            reader, writer = await asyncio.open_connection(sock=client)
            await self._handle(reader, writer)
        except Exception as exc:
            self.errors.append(exc)

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            async with asyncio.timeout(self.transport.timeout):
                message = await receive_message(reader)
                if message["type"] == "push" and self.mode == "push":
                    await self._apply(_record_from_json(message.get("record")))
                elif message["type"] == "pull_request" and self.mode == "pull":
                    versions = message.get("versions")
                    if not isinstance(versions, dict) or any(
                        type(v) is not int or v < 0 for v in versions.values()
                    ):
                        raise ProtocolError("invalid version summary")
                    records = self.store.newer_than(versions)
                    await self.transport.send_message(
                        writer,
                        {"type": "pull_reply", "records": [asdict(r) for r in records]},
                    )
                else:
                    raise ProtocolError("unexpected message type for peer mode")
        except Exception as exc:
            self.errors.append(exc)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError as exc:
                self.errors.append(exc)
