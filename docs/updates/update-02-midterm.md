# Push vs Pull: Bi-weekly Update 2 (Midterm Update)

**CSC 466 · University of Victoria**
Rahil Wijeyesekera · Hamzah Banday · Prabhnoor Singh · Adithyakrishna Arunkumar
**Period covered:** 2026-10-25 to 2026-11-10 · **Written:** 2026-11-10
**Project site:** https://rahilyw.github.io/csc466-push-vs-pull/
**Repository:** https://github.com/Rahilyw/csc466-push-vs-pull

This is the midterm update. It still has to be posted on the course thread.

## 1. Summary

The project is behind the schedule in the proposal. On November 10 we put up the repository, the GitHub Pages site, and the logbook. Each peer's versioned store is implemented, and four unit tests pass. Push, pull, TCP messaging, and the experiment runner are not implemented. No network experiment has been run.

## 2. Progress since last update

| Task | Owner | Status | Evidence |
|------|-------|--------|----------|
| Project website, logbook, and testbed skeleton | Rahil | Done | https://rahilyw.github.io/csc466-push-vs-pull/ . Commits `1cdcead` and `605f16b` (2026-11-10). |
| Versioned store: one writer per key, newer version wins | Rahil | Done | `src/pushpull/store.py`, `tests/test_store.py` |
| Push, pull, messaging, delay, metrics, and the experiment runner | Team | Not started | Stubs in `src/pushpull/peer.py`, `src/pushpull/transport.py`, `src/pushpull/metrics.py`, and `experiments/run.py` |

The plan from update 1 was a 4-peer push and pull demo by November 7. Only the store was finished, and it was finished on November 10.

## 3. Results so far

These are local unit tests, not a network run. Command: `python -m pytest`, run on November 10, 2026. Result: 4 passed. There is no seed, peer count, or delay setting, because the peers do not exchange messages yet.

| Check | What it confirms |
|-------|------------------|
| `test_local_write_increments_version` | The first write of a key is version 1. The next write by the same owner is version 2. |
| `test_only_designated_writer_can_write` | After peer 0 writes a key, peer 1's write raises `PermissionError`. |
| `test_apply_rejects_stale_and_duplicate` | Applying version 2 stores it. Applying version 2 again, or version 1, leaves the stored value unchanged. |
| `test_newer_than_returns_only_newer_records` | Given a caller's version summary, the reply includes only records with a higher version. |

No propagation delay, byte count, convergence time, or idle traffic has been measured.

## 4. Problems and changes to the plan

Implementation started about four weeks after the proposal schedule. Both bi-weekly updates are being written on November 10 because they were not posted in their own periods.

One change to the pull exchange, recorded now so the code and the report match. It is not running yet. A peer will send its own version summary, and the neighbour will reply with the newer records. That is one round trip. The proposal said the peer would ask for the neighbour's version list and then request the newer records, which is two round trips. `version_vector` and `newer_than` in `src/pushpull/store.py` are the one-round-trip exchange. At 100 ms of added one-way delay, one round trip is about 200 ms per hop and two round trips are about 400 ms. The question, the ring, the workload, and the four metrics stay as written in the proposal.

## 5. Plan for the next two weeks

| Task | Owner | Target date |
|------|-------|-------------|
| Length-prefixed TCP messages between ring neighbours, with the 0 ms and 100 ms delay and the byte and message counters | Team | 2026-11-17 |
| Push, then pull, using the one-round-trip exchange above | Team | 2026-11-19 |
| Four peers, both modes, same final version of every key | Team | 2026-11-21 |
| Seeded updates and the first 8-peer logs | Team | 2026-11-24 |

## 6. Contributions

| Member | Work this period |
|--------|------------------|
| Rahil Wijeyesekera | Repository, GitHub Pages site, logbook, versioned store, and the four tests. |
| Hamzah Banday | No separate work is recorded in the logbook for this period. |
| Prabhnoor Singh | No separate work is recorded in the logbook for this period. |
| Adithyakrishna Arunkumar | Write access to the repository (GitHub account `akaAdiArun`). No separate implementation is recorded for this period. |

Anyone whose work from these two weeks is missing should add it before the PDF is posted.
