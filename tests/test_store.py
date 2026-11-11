import pytest

from pushpull.store import Record, VersionedStore


def test_local_write_increments_version():
    s = VersionedStore()
    assert s.local_write("task1", "open", writer=0).version == 1
    assert s.local_write("task1", "done", writer=0).version == 2


def test_only_designated_writer_can_write():
    s = VersionedStore()
    s.local_write("task1", "open", writer=0)
    with pytest.raises(PermissionError):
        s.local_write("task1", "done", writer=1)


def test_apply_rejects_stale_and_duplicate():
    s = VersionedStore()
    assert s.apply(Record("k", "v2", 2, 0))
    assert not s.apply(Record("k", "v2", 2, 0))  # duplicate
    assert not s.apply(Record("k", "v1", 1, 0))  # stale
    assert s.get("k").value == "v2"


def test_newer_than_returns_only_newer_records():
    s = VersionedStore()
    s.apply(Record("a", "x", 3, 0))
    s.apply(Record("b", "y", 1, 1))
    newer = s.newer_than({"a": 3, "b": 0})
    assert [r.key for r in newer] == ["b"]
