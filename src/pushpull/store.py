"""Versioned key-value store held by each peer.

Every key has one designated writer, and each write increases its version number.
A record is accepted only when its version is newer than the one already held.
Push uses that rule to stop forwarding duplicates; pull uses it to decide what to request.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Record:
    key: str
    value: str
    version: int
    writer: int  # peer id that owns this key


class VersionedStore:
    def __init__(self) -> None:
        self._records: dict[str, Record] = {}

    def get(self, key: str) -> Record | None:
        return self._records.get(key)

    def version_of(self, key: str) -> int:
        rec = self._records.get(key)
        return rec.version if rec else 0

    def apply(self, record: Record) -> bool:
        """Store `record` if it is newer than what we hold. Returns True if stored."""
        if record.version <= self.version_of(record.key):
            return False
        self._records[record.key] = record
        return True

    def local_write(self, key: str, value: str, writer: int) -> Record:
        """Create the next version of a key this peer owns."""
        current = self._records.get(key)
        if current is not None and current.writer != writer:
            raise PermissionError(f"peer {writer} is not the writer of {key!r}")
        rec = Record(key, value, self.version_of(key) + 1, writer)
        self._records[key] = rec
        return rec

    def version_vector(self) -> dict[str, int]:
        """Key -> version summary that a pull request sends."""
        return {k: r.version for k, r in self._records.items()}

    def newer_than(self, versions: dict[str, int]) -> list[Record]:
        """Records we hold that are newer than the given summary (answers a pull)."""
        return [r for k, r in self._records.items() if r.version > versions.get(k, 0)]
