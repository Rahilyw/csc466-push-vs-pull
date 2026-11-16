# Results: first repeated eight-peer pilot

**Run date: November 15, 2026 · 20/20 converged · 0 missing propagation samples**

These are actual multi-process loopback observations, separate from the automated
correctness tests. The short pilot checks the experiment pipeline and gives an
initial comparison; it is not the completed performance study.

[Summary CSV](raw/pilot-2026-11-15/summary.csv) ·
[Summary JSON](raw/pilot-2026-11-15/summary.json) ·
[Experiment guide](../experiments/README.md) ·
[Source commit `4484d97`](https://github.com/Rahilyw/csc466-push-vs-pull/commit/4484d975d41f721f8f2538412cdf3741312b8ad5)

## Configuration and provenance

- 8 independent peer processes in a TCP ring; 16 possible keys, fixed writer per key.
- Both modes at 0 and 100 ms added one-way delay; pull interval 0.5 s.
- Seeds 1–5, replaying the same workload across modes and delay settings.
- Rate 1 update/s for 8 s: 8 updates per run, then 2 s settling and 2 s idle.
- Fixed 12 s communication window per run, independent of convergence speed.
- Every run reached the expected final keys, values, versions and writers.
- All 1,280 update/peer propagation samples were observed before the deadline;
  this includes each update's writer. No worker errors were recorded.
- Python 3.12.14 on one Linux cloud host. Ports are assigned by the OS.
- Source SHA-256: `33b8d6e14a5bf4aa17dc64942fa6a6e167caba618a6419b5c2e001cc194b1a9c`.
  Each run's `result.json` also records workload fingerprints, windows and PIDs.

## Observed propagation and convergence

Values are **mean ± sample standard deviation across five seeds**. Median and
p95 columns average each run's quantile; they are not pooled quantiles. Final
convergence is measured from the last actual write, not from the window boundary.

| Mode | Added one-way delay | Median propagation (ms) | p95 propagation (ms) | Final convergence (ms) |
|---|---:|---:|---:|---:|
| Pull | 0 ms | 232.0 ± 255.3 | 1013.8 ± 54.1 | 832.9 ± 287.5 |
| Push | 0 ms | 4.0 ± 0.9 | 12.3 ± 5.1 | 8.1 ± 3.1 |
| Pull | 100 ms | 709.9 ± 2.4 | 1713.3 ± 2.3 | 1717.8 ± 2.9 |
| Push | 100 ms | 203.4 ± 0.5 | 406.5 ± 0.5 | 405.9 ± 0.6 |

## Observed communication

Means across five runs. Bytes include the four-byte application prefix and JSON,
excluding TCP/IP headers and controller traffic. Exact variation is in the summary CSV.

| Mode | Delay | Messages / run | Application bytes / run | Idle messages / s |
|---|---:|---:|---:|---:|
| Pull | 0 ms | 768 | 51623.8 | 64 |
| Push | 0 ms | 128 | 12073.6 | 0 |
| Pull | 100 ms | 768 | 51178.8 | 64 |
| Push | 100 ms | 128 | 12073.6 | 0 |

Push sent 128 messages in every run: eight updates × eight peers × two neighbours.
Pull sent 768 messages in every run, six times the push count for this workload
and poll interval. Push had no idle synchronization traffic; pull sent 64 messages/s
across the ring while idle. Empty replies are included.

In this pilot, push had lower observed propagation latency at both delay settings.
The 0 ms pull medians varied substantially across seeds, as the standard deviation
shows. Poll timing, the regular write schedule and host scheduling can affect these
short runs; this pilot does not isolate those effects. The observations do not
establish that push is preferable at all update rates or poll intervals.

## Reproduce or audit

From the repository root:

```bash
python experiments/pilot.py --output results/raw/my-reproduction \
  --seeds 1 2 3 4 5 --duration 8 --settle 2 --idle 2
python experiments/summarize.py results/raw/pilot-2026-11-15
```

Use a new output directory; existing run directories are never overwritten.
Reanalysis recomputes every metric from `updates.csv`, `acceptances.csv` and
`traffic.csv`, checks stored summaries, and validates matched workloads, source
fingerprints and seed sets before writing summary files. Timing measurements will
vary on another run. Stored raw logs reproduce the displayed summaries exactly.

## Raw run index

Each directory contains the workload schedule, actual writes, acceptance events,
send events and result metadata.

| Seed | Push, 0 ms | Pull, 0 ms | Push, 100 ms | Pull, 100 ms |
|---|---|---|---|---|
| 1 | [raw logs](raw/pilot-2026-11-15/push-delay0-seed1/) | [raw logs](raw/pilot-2026-11-15/pull-delay0-seed1/) | [raw logs](raw/pilot-2026-11-15/push-delay100-seed1/) | [raw logs](raw/pilot-2026-11-15/pull-delay100-seed1/) |
| 2 | [raw logs](raw/pilot-2026-11-15/push-delay0-seed2/) | [raw logs](raw/pilot-2026-11-15/pull-delay0-seed2/) | [raw logs](raw/pilot-2026-11-15/push-delay100-seed2/) | [raw logs](raw/pilot-2026-11-15/pull-delay100-seed2/) |
| 3 | [raw logs](raw/pilot-2026-11-15/push-delay0-seed3/) | [raw logs](raw/pilot-2026-11-15/pull-delay0-seed3/) | [raw logs](raw/pilot-2026-11-15/push-delay100-seed3/) | [raw logs](raw/pilot-2026-11-15/pull-delay100-seed3/) |
| 4 | [raw logs](raw/pilot-2026-11-15/push-delay0-seed4/) | [raw logs](raw/pilot-2026-11-15/pull-delay0-seed4/) | [raw logs](raw/pilot-2026-11-15/push-delay100-seed4/) | [raw logs](raw/pilot-2026-11-15/pull-delay100-seed4/) |
| 5 | [raw logs](raw/pilot-2026-11-15/push-delay0-seed5/) | [raw logs](raw/pilot-2026-11-15/pull-delay0-seed5/) | [raw logs](raw/pilot-2026-11-15/push-delay100-seed5/) | [raw logs](raw/pilot-2026-11-15/pull-delay100-seed5/) |

## Still to measure

Longer workload and idle windows; low update rate (1/5 s); pull intervals 2 s and
5 s; 4- and 16-peer scaling; and broader repeats on a controlled host. The current
pilot covers one update rate and one pull interval. Added sender delay on loopback
does not reproduce wide-area loss, bandwidth limits or churn. No retry/recovery
protocol, cross-machine clock synchronization, or final report is claimed here.
