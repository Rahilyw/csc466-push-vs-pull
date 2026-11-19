# Push vs pull results

## Longer benchmark · November 19, 2026

Snapshot checked at **2026-11-19 14:33 MST**. **4 converged**,
**0 convergence timeouts**, **0 measured errors**,
**0 crashes**, and **156 unfinished** across 160 planned runs.
The full matrix takes 4 h 40 min of observation time plus process startup and
log collection. See the measurement windows and exact commands in the
[benchmark plan](raw/benchmark-2026-11-19/plan.md).

All measured runs use 60 seconds of workload, 25 seconds of settling, 20 seconds
of idle, and 16 possible keys. Push and pull replay matching workloads within
seed, rate, peer count and delay. Delay is added one way to application messages
over TCP loopback. The host runs the batches sequentially. The original pilot
used shorter windows and is reported separately below.

| Peers | Updates/s | Pull interval (s) | Converged | Timeout | Error | Crash | Unfinished | Verification files |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 8 | 0.2 | 0.5 | 4 | 0 | 0 | 0 | 16 | [Manifest](raw/benchmark-2026-11-19/peers8-rate0.2-pull0.5/manifest.json) · [audit](raw/benchmark-2026-11-19/peers8-rate0.2-pull0.5/audit.json) |
| 8 | 0.2 | 2 | 0 | 0 | 0 | 0 | 20 | Queued |
| 8 | 0.2 | 5 | 0 | 0 | 0 | 0 | 20 | Queued |
| 8 | 1 | 0.5 | 0 | 0 | 0 | 0 | 20 | Queued |
| 8 | 1 | 2 | 0 | 0 | 0 | 0 | 20 | Queued |
| 8 | 1 | 5 | 0 | 0 | 0 | 0 | 20 | Queued |
| 4 | 1 | 0.5 | 0 | 0 | 0 | 0 | 20 | Queued |
| 16 | 1 | 0.5 | 0 | 0 | 0 | 0 | 20 | Queued |

### Verified measurements at this checkpoint

Values are per-run statistics when a row has one seed. With multiple seeds,
values are means ± sample standard deviations. The p50 and p95 columns summarize
the per-run quantiles, which include the writer. Convergence is elapsed time
since the last write. Traffic counts cover the full 105 seconds. The idle rates
are measured during the last 20 seconds. Bytes include application framing.
Timeouts and operational errors have their own rows when measured metrics exist.

| Peers | Updates/s | Pull interval (s) | Added delay (ms) | Mode | Outcome | Seeds | p50 (ms) | p95 (ms) | Convergence (ms) | Messages | Bytes | Idle msg/s | Idle B/s |
|---:|---:|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 8 | 0.2 | 0.5 | 0 | pull | converged | 1 | 80.4 | 1,002.5 | 587.3 | 6,720 | 514,210 | 64.0 | 5,472.0 |
| 8 | 0.2 | 0.5 | 0 | push | converged | 1 | 2.9 | 12.5 | 12.1 | 192 | 18,160 | 0.0 | 0.0 |
| 8 | 0.2 | 0.5 | 100 | pull | converged | 1 | 746.5 | 1,760.4 | 1,787.8 | 6,720 | 513,414 | 64.0 | 5,472.0 |
| 8 | 0.2 | 0.5 | 100 | push | converged | 1 | 203.4 | 406.6 | 406.3 | 192 | 18,160 | 0.0 | 0.0 |

The first seed at 0.2 updates/s and a 0.5 s pull interval showed the same
ordering as the original pilot. Push had lower p50 and p95 at both delays and
sent 192 messages per run versus pull's 6,720. Idle rates were 0 versus
64 messages/s. The pilot used a different update rate and shorter windows.
A measured rate comparison under the same windows, an interval comparison,
and the scaling comparisons are pending. This one-seed checkpoint gives
no estimate of variation across seeds.

Each pull interval has a paired push baseline. Those push runs share the same
workload and seeds across the interval batches, so any analysis across intervals
must keep the comparisons separate. The 4- and 16-peer results use the eight-peer
1 update/s and 0.5 s batch as their reference once all three are available.

## Original eight-peer pilot · November 15, 2026

**Run date: November 15, 2026 · 20/20 converged · 0 missing propagation samples**

These are actual multi-process loopback observations, separate from the automated
correctness tests. The short pilot checks the experiment pipeline and gives an
initial comparison; it is not the completed performance study.

[Summary CSV](raw/pilot-2026-11-15/summary.csv) ·
[Summary JSON](raw/pilot-2026-11-15/summary.json) ·
[Experiment guide](../experiments/README.md) ·
[Source commit `4484d97`](https://github.com/Rahilyw/csc466-push-vs-pull/commit/4484d975d41f721f8f2538412cdf3741312b8ad5)

### Configuration and provenance

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

### Observed propagation and convergence

Values are **mean ± sample standard deviation across five seeds**. Median and
p95 columns average each run's quantile; they are not pooled quantiles. Final
convergence is measured from the last actual write, not from the window boundary.

| Mode | Added one-way delay | Median propagation (ms) | p95 propagation (ms) | Final convergence (ms) |
|---|---:|---:|---:|---:|
| Pull | 0 ms | 232.0 ± 255.3 | 1013.8 ± 54.1 | 832.9 ± 287.5 |
| Push | 0 ms | 4.0 ± 0.9 | 12.3 ± 5.1 | 8.1 ± 3.1 |
| Pull | 100 ms | 709.9 ± 2.4 | 1713.3 ± 2.3 | 1717.8 ± 2.9 |
| Push | 100 ms | 203.4 ± 0.5 | 406.5 ± 0.5 | 405.9 ± 0.6 |

### Observed communication

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

### Reproduce or audit

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

### Raw run index

Each directory contains the workload schedule, actual writes, acceptance events,
send events and result metadata.

**November 18 audit:** all 20 runs passed reanalysis against an explicit
[run manifest](raw/pilot-2026-11-15/manifest.json). It was reconstructed from the
published setup and recorded configurations, with provenance `archived_plan`;
it is not a preregistration. No measurements were rerun or changed. The summary
JSON now records the 20 expected and 20 observed results. New pilots save their
manifests before starting, so missing whole configurations cannot silently pass
as a complete comparison. See the [completeness checks](../experiments/README.md#completeness-checks).

| Seed | Push, 0 ms | Pull, 0 ms | Push, 100 ms | Pull, 100 ms |
|---|---|---|---|---|
| 1 | [raw logs](raw/pilot-2026-11-15/push-delay0-seed1/) | [raw logs](raw/pilot-2026-11-15/pull-delay0-seed1/) | [raw logs](raw/pilot-2026-11-15/push-delay100-seed1/) | [raw logs](raw/pilot-2026-11-15/pull-delay100-seed1/) |
| 2 | [raw logs](raw/pilot-2026-11-15/push-delay0-seed2/) | [raw logs](raw/pilot-2026-11-15/pull-delay0-seed2/) | [raw logs](raw/pilot-2026-11-15/push-delay100-seed2/) | [raw logs](raw/pilot-2026-11-15/pull-delay100-seed2/) |
| 3 | [raw logs](raw/pilot-2026-11-15/push-delay0-seed3/) | [raw logs](raw/pilot-2026-11-15/pull-delay0-seed3/) | [raw logs](raw/pilot-2026-11-15/push-delay100-seed3/) | [raw logs](raw/pilot-2026-11-15/pull-delay100-seed3/) |
| 4 | [raw logs](raw/pilot-2026-11-15/push-delay0-seed4/) | [raw logs](raw/pilot-2026-11-15/pull-delay0-seed4/) | [raw logs](raw/pilot-2026-11-15/push-delay100-seed4/) | [raw logs](raw/pilot-2026-11-15/pull-delay100-seed4/) |
| 5 | [raw logs](raw/pilot-2026-11-15/push-delay0-seed5/) | [raw logs](raw/pilot-2026-11-15/pull-delay0-seed5/) | [raw logs](raw/pilot-2026-11-15/push-delay100-seed5/) | [raw logs](raw/pilot-2026-11-15/pull-delay100-seed5/) |

## Future work

Complete the remaining matched-seed benchmark batches. Peer-outage testing
remains future work. The measurements use application delay on loopback.
