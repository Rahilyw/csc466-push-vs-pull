# Push vs Pull: Keeping P2P Data Synchronized

## Project update 3 — Networking and first pilot

**University of Victoria · CSC 466**
**Prepared:** November 15, 2026 · **Scope:** progress after the November 10 midterm status

**Team:** Rahil Wijeyesekera, Hamzah Banday, Prabhnoor Singh, Adithyakrishna Arunkumar
**Implementation contributor:** Adithyakrishna Arunkumar / Adi ([akaAdiArun](https://github.com/akaAdiArun))

## 1. Summary

The project has moved from a versioned-store skeleton to working TCP push/pull
synchronization and a seeded multi-process experiment runner. The final automated
suite has **54 passing tests**. A short eight-peer pilot completed **20/20 runs**
with matching final records and no missing propagation samples. The code is on
[main](https://github.com/Rahilyw/csc466-push-vs-pull); this update records actual
verification and preliminary observations rather than a finished performance study.

## 2. Completed implementation

- **Transport:** four-byte length-prefixed UTF-8 JSON over TCP; configurable one-way delay on every frame; successful-send bytes and messages counted by type. Application framing is included; TCP/IP headers and controller traffic are excluded.
- **Synchronization:** newly accepted push versions go to both ring neighbours; stale/duplicate versions stop. Pull sends one version summary and receives one newer-records reply per neighbour on the same connection, as specified in the midterm update.
- **Runner and evidence:** one spawned process per peer; deterministic seeded writes and designated writers; fixed workload, settling and idle windows; raw schedules, creation/acceptance/send logs, metadata and recomputable metrics.
- **Lifecycle:** peers join their accept loop before closing sockets. Regression tests cover clients stalled in frames and connections arriving during shutdown; workers are joined after controller failures.

## 3. Verification

The existing four store tests were preserved. New tests cover final records on a
four-peer TCP ring in push and pull at both 0 and 100 ms, duplicate/stale suppression,
exact pull request/reply counts and bytes, framing/delay/timeouts, separate worker
PIDs, seeded replay, raw-log metric recomputation and explicit convergence timeouts.

```bash
python -m pytest
# 54 passed in 18.12 s
PYTHONASYNCIODEBUG=1 python -W error -m pytest
# 54 passed in 19.26 s
```

Verification used Python 3.12.14 in a workspace virtual environment. These test
execution times are not synchronization performance measurements.

<!-- pagebreak -->

## 4. First eight-peer pilot: setup

Five matched seeds (1–5) were run in both modes at 0 and 100 ms added one-way
delay: **20 runs total**. Every run used 8 independent processes, a ring with two
neighbours, 16 possible keys, rate 1 update/s and pull interval 0.5 s. Workloads
were identical across modes/delays for each seed; mode order alternated by seed.

Each run had an **8 s workload + 2 s settling + 2 s idle** window, giving a fixed
12 s communication observation. There were eight updates per run. All 20 runs
converged before the deadline, all final values/versions/writers matched, all
**1,280 update/peer propagation samples** were observed, and no worker errors
were recorded. Propagation samples include the update's writer.

## 5. Measured observations

Latency values below are **mean ± sample standard deviation across five seeds**.
Median/p95 columns average per-run quantiles; they are not pooled quantiles.
Convergence is measured from the last actual write until every peer holds all
final versions. Acceptance of a newer version also satisfies an older update.

| Mode | Delay | Median (ms) | p95 (ms) | Convergence (ms) |
|---|---:|---:|---:|---:|
| Pull | 0 ms | 232.0 ± 255.3 | 1013.8 ± 54.1 | 832.9 ± 287.5 |
| Push | 0 ms | 4.0 ± 0.9 | 12.3 ± 5.1 | 8.1 ± 3.1 |
| Pull | 100 ms | 709.9 ± 2.4 | 1713.3 ± 2.3 | 1717.8 ± 2.9 |
| Push | 100 ms | 203.4 ± 0.5 | 406.5 ± 0.5 | 405.9 ± 0.6 |

Communication values are means across five runs, including duplicates and empty
replies. Bytes are serialized application bytes, including the length prefix.

| Mode | Delay | Messages/run | Bytes/run | Idle messages/s |
|---|---:|---:|---:|---:|
| Pull | 0 ms | 768 | 51623.8 | 64 |
| Push | 0 ms | 128 | 12073.6 | 0 |
| Pull | 100 ms | 768 | 51178.8 | 64 |
| Push | 100 ms | 128 | 12073.6 | 0 |

For this workload and poll interval, pull sent six times as many messages as
push (768 versus 128 per run). Push sent no synchronization traffic while idle;
pull continued at 64 messages/s across the ring. Push had lower observed
propagation latency at both tested delays.

## 6. Limits of these findings

This is a short pilot on one Linux cloud host using loopback and sender-side
artificial delay. It does not model wide-area loss, bandwidth limits or churn.
Only one rate and one pull interval were tested. The 0 ms pull medians varied
substantially across seeds; poll phase, regular update timing and host scheduling
may influence these short observations and were not isolated. The results do not
establish that push is preferable under every workload. Longer controlled runs
and the full planned parameter matrix are still needed.

<!-- pagebreak -->

## 7. Contributions and evidence

| Member | Recorded work |
|---|---|
| Adithyakrishna Arunkumar / Adi (`akaAdiArun`) | TCP transport, push/pull, acceptance/send events, correctness/process tests, seeded runner, metrics, pilot and documentation. |
| Rahil Wijeyesekera (`Rahilyw`) | Repository/website setup, original versioned store and four tests, logbook structure and first two updates. |
| Hamzah Banday; Prabhnoor Singh | Project proposal and shared team design. Additional individual work should be recorded by the respective teammate. |

The original store and historical updates were preserved. The previous midterm
status remains a record of its period; it was not rewritten to claim later work.

- [Networking implementation, 1050440](https://github.com/Rahilyw/csc466-push-vs-pull/commit/1050440f60efe8da7351e9b8c59a14325643d3e8)
- [Runner, metrics and final tested source, 4484d97](https://github.com/Rahilyw/csc466-push-vs-pull/commit/4484d975d41f721f8f2538412cdf3741312b8ad5)
- [Findings and raw-run index](https://github.com/Rahilyw/csc466-push-vs-pull/blob/main/results/README.md)
- [Machine-readable summary](https://github.com/Rahilyw/csc466-push-vs-pull/blob/main/results/raw/pilot-2026-11-15/summary.csv)
- [Experiment guide and metric definitions](https://github.com/Rahilyw/csc466-push-vs-pull/blob/main/experiments/README.md)
- [Dated logbook](https://github.com/Rahilyw/csc466-push-vs-pull/blob/main/LOGBOOK.md)

Every run stores configuration, platform/Python version, process IDs, observation
windows, errors and source/workload SHA-256 fingerprints. Raw CSVs contain the
scheduled updates, actual creation timestamps, accepted versions and sent frames.
The summary command recomputes metrics and rejects incomplete or mismatched runs.

## 8. Reproduce and next work

```bash
python experiments/pilot.py --output results/raw/my-reproduction \
  --seeds 1 2 3 4 5 --duration 8 --settle 2 --idle 2
python experiments/summarize.py results/raw/pilot-2026-11-15
```

Use a new output directory. Timing measurements may differ on another run;
reanalysis of the committed raw logs reproduces the displayed summaries exactly.

Next, run longer observation windows with both planned rates (1/5 s and 1/s), all
pull intervals (0.5, 2 and 5 s), matched seeds at each delay, and 4/16-peer scaling
checks. Investigate the observed timing variability on a controlled host before
making broader comparisons. Final analysis, presentation and final report remain
separate deliverables. This PDF has been prepared for the project update; no
course-thread submission is claimed.
