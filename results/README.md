# Push vs pull results

## Longer benchmark · November 19, 2026

The original queue finished at **7:09:36 p.m. Vancouver time on November 19**.
All eight batches matched their manifests. **160 converged**, with **0 timeouts**,
**0 measured errors**, **0 crashes**, and **0 unfinished**. All 58,560 expected
update/peer propagation samples were present, including each update's writer.
The saved workloads and both summary formats matched independent recomputation
from the raw logs.
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
| 8 | 0.2 | 0.5 | 20 | 0 | 0 | 0 | 0 | [Manifest](raw/benchmark-2026-11-19/peers8-rate0.2-pull0.5/manifest.json) · [audit](raw/benchmark-2026-11-19/peers8-rate0.2-pull0.5/audit.json) · [summary](raw/benchmark-2026-11-19/peers8-rate0.2-pull0.5/summary.json) |
| 8 | 0.2 | 2 | 20 | 0 | 0 | 0 | 0 | [Manifest](raw/benchmark-2026-11-19/peers8-rate0.2-pull2/manifest.json) · [audit](raw/benchmark-2026-11-19/peers8-rate0.2-pull2/audit.json) · [summary](raw/benchmark-2026-11-19/peers8-rate0.2-pull2/summary.json) |
| 8 | 0.2 | 5 | 20 | 0 | 0 | 0 | 0 | [Manifest](raw/benchmark-2026-11-19/peers8-rate0.2-pull5/manifest.json) · [audit](raw/benchmark-2026-11-19/peers8-rate0.2-pull5/audit.json) · [summary](raw/benchmark-2026-11-19/peers8-rate0.2-pull5/summary.json) |
| 8 | 1 | 0.5 | 20 | 0 | 0 | 0 | 0 | [Manifest](raw/benchmark-2026-11-19/peers8-rate1-pull0.5/manifest.json) · [audit](raw/benchmark-2026-11-19/peers8-rate1-pull0.5/audit.json) · [summary](raw/benchmark-2026-11-19/peers8-rate1-pull0.5/summary.json) |
| 8 | 1 | 2 | 20 | 0 | 0 | 0 | 0 | [Manifest](raw/benchmark-2026-11-19/peers8-rate1-pull2/manifest.json) · [audit](raw/benchmark-2026-11-19/peers8-rate1-pull2/audit.json) · [summary](raw/benchmark-2026-11-19/peers8-rate1-pull2/summary.json) |
| 8 | 1 | 5 | 20 | 0 | 0 | 0 | 0 | [Manifest](raw/benchmark-2026-11-19/peers8-rate1-pull5/manifest.json) · [audit](raw/benchmark-2026-11-19/peers8-rate1-pull5/audit.json) · [summary](raw/benchmark-2026-11-19/peers8-rate1-pull5/summary.json) |
| 4 | 1 | 0.5 | 20 | 0 | 0 | 0 | 0 | [Manifest](raw/benchmark-2026-11-19/peers4-rate1-pull0.5/manifest.json) · [audit](raw/benchmark-2026-11-19/peers4-rate1-pull0.5/audit.json) · [summary](raw/benchmark-2026-11-19/peers4-rate1-pull0.5/summary.json) |
| 16 | 1 | 0.5 | 20 | 0 | 0 | 0 | 0 | [Manifest](raw/benchmark-2026-11-19/peers16-rate1-pull0.5/manifest.json) · [audit](raw/benchmark-2026-11-19/peers16-rate1-pull0.5/audit.json) · [summary](raw/benchmark-2026-11-19/peers16-rate1-pull0.5/summary.json) |

### Verified measurements

Values are per-run statistics when a row has one seed. With multiple seeds,
values are means ± sample standard deviations. The p50 and p95 columns summarize
the per-run quantiles, which include the writer. Convergence is elapsed time
since the last write. Traffic counts cover the full 105 seconds. The idle rates
are measured during the last 20 seconds. Bytes include application framing.
Timeouts and operational errors have their own rows when measured metrics exist.

| Peers | Updates/s | Pull interval (s) | Added delay (ms) | Mode | Outcome | Seeds | p50 (ms) | p95 (ms) | Convergence (ms) | Messages | Bytes | Idle msg/s | Idle B/s |
|---:|---:|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 8 | 0.2 | 0.5 | 0 | pull | converged | 1, 2, 3, 4, 5 | 171.1 ± 188.8 | 1,034.6 ± 33.7 | 989.2 ± 226.6 | 6,720 ± 0 | 502,037 ± 35,458 | 64.0 ± 0.0 | 5,395.2 ± 539.1 |
| 8 | 0.2 | 0.5 | 0 | push | converged | 1, 2, 3, 4, 5 | 2.8 ± 0.4 | 10.3 ± 4.6 | 6.5 ± 3.2 | 192 ± 0 | 18,144 ± 16 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 8 | 0.2 | 0.5 | 100 | pull | converged | 1, 2, 3, 4, 5 | 753.0 ± 24.7 | 1,746.9 ± 10.7 | 1,793.4 ± 21.6 | 6,713 ± 14 | 500,708 ± 35,023 | 64.0 ± 0.0 | 5,394.4 ± 540.7 |
| 8 | 0.2 | 0.5 | 100 | push | converged | 1, 2, 3, 4, 5 | 203.5 ± 0.2 | 406.9 ± 0.4 | 407.2 ± 2.7 | 192 ± 0 | 18,144 ± 16 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 8 | 0.2 | 2 | 0 | pull | converged | 1, 2, 3, 4, 5 | 1,617.0 ± 532.7 | 4,481.7 ± 503.1 | 4,251.3 ± 1,114.7 | 1,696 ± 0 | 129,584 ± 8,727 | 16.0 ± 0.0 | 1,348.8 ± 134.8 |
| 8 | 0.2 | 2 | 0 | push | converged | 1, 2, 3, 4, 5 | 2.9 ± 0.3 | 7.0 ± 0.9 | 6.0 ± 1.3 | 192 ± 0 | 18,144 ± 16 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 8 | 0.2 | 2 | 100 | pull | converged | 1, 2, 3, 4, 5 | 2,722.0 ± 11.8 | 7,211.5 ± 4.5 | 7,238.2 ± 22.6 | 1,696 ± 0 | 128,899 ± 8,518 | 16.0 ± 0.0 | 1,348.8 ± 134.8 |
| 8 | 0.2 | 2 | 100 | push | converged | 1, 2, 3, 4, 5 | 203.5 ± 0.7 | 406.6 ± 0.9 | 405.7 ± 0.6 | 192 ± 0 | 18,144 ± 16 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 8 | 0.2 | 5 | 0 | pull | converged | 1, 2, 3, 4, 5 | 1,011.7 ± 2,230.9 | 10,005.5 ± 1.0 | 6,012.3 ± 2,234.5 | 672 ± 0 | 53,798 ± 3,225 | 6.4 ± 0.0 | 539.5 ± 53.9 |
| 8 | 0.2 | 5 | 0 | push | converged | 1, 2, 3, 4, 5 | 3.1 ± 1.4 | 8.8 ± 5.5 | 5.0 ± 1.6 | 192 ± 0 | 18,144 ± 16 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 8 | 0.2 | 5 | 100 | pull | converged | 1, 2, 3, 4, 5 | 5,209.4 ± 1.2 | 15,209.7 ± 1.3 | 15,211.2 ± 0.5 | 672 ± 0 | 53,210 ± 3,055 | 6.4 ± 0.0 | 539.5 ± 53.9 |
| 8 | 0.2 | 5 | 100 | push | converged | 1, 2, 3, 4, 5 | 203.3 ± 0.4 | 406.3 ± 0.5 | 405.6 ± 1.1 | 192 ± 0 | 18,144 ± 16 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 8 | 1 | 0.5 | 0 | pull | converged | 1, 2, 3, 4, 5 | 161.5 ± 166.9 | 1,069.8 ± 57.3 | 785.0 ± 277.1 | 6,714 ± 14 | 769,084 ± 13,181 | 64.0 ± 0.0 | 7,808.0 ± 0.0 |
| 8 | 1 | 0.5 | 0 | push | converged | 1, 2, 3, 4, 5 | 2.4 ± 0.2 | 6.4 ± 1.0 | 4.8 ± 1.1 | 960 ± 0 | 91,402 ± 24 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 8 | 1 | 0.5 | 100 | pull | converged | 1, 2, 3, 4, 5 | 744.8 ± 7.7 | 1,758.2 ± 12.3 | 1,781.0 ± 15.7 | 6,720 ± 0 | 768,872 ± 12,268 | 64.0 ± 0.0 | 7,808.0 ± 0.0 |
| 8 | 1 | 0.5 | 100 | push | converged | 1, 2, 3, 4, 5 | 203.1 ± 0.1 | 406.0 ± 0.1 | 406.2 ± 1.8 | 960 ± 0 | 91,402 ± 24 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 8 | 1 | 2 | 0 | pull | converged | 1, 2, 3, 4, 5 | 1,462.3 ± 500.4 | 4,613.7 ± 542.5 | 5,025.0 ± 5.3 | 1,696 ± 0 | 213,035 ± 2,638 | 16.0 ± 0.0 | 1,952.0 ± 0.0 |
| 8 | 1 | 2 | 0 | push | converged | 1, 2, 3, 4, 5 | 2.6 ± 0.2 | 6.6 ± 0.8 | 5.4 ± 0.8 | 960 ± 0 | 91,402 ± 24 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 8 | 1 | 2 | 100 | pull | converged | 1, 2, 3, 4, 5 | 2,738.8 ± 26.2 | 7,209.6 ± 3.1 | 7,246.9 ± 37.0 | 1,696 ± 0 | 212,106 ± 2,552 | 16.0 ± 0.0 | 1,952.0 ± 0.0 |
| 8 | 1 | 2 | 100 | push | converged | 1, 2, 3, 4, 5 | 203.5 ± 0.5 | 407.9 ± 2.8 | 423.8 ± 40.3 | 960 ± 0 | 91,402 ± 24 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 8 | 1 | 5 | 0 | pull | converged | 1, 2, 3, 4, 5 | 4,311.5 ± 445.0 | 12,032.8 ± 687.8 | 11,016.3 ± 3.4 | 672 ± 0 | 96,468 ± 1,105 | 6.4 ± 0.0 | 780.8 ± 0.0 |
| 8 | 1 | 5 | 0 | push | converged | 1, 2, 3, 4, 5 | 2.6 ± 0.2 | 7.8 ± 4.4 | 5.0 ± 0.9 | 960 ± 0 | 91,402 ± 24 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 8 | 1 | 5 | 100 | pull | converged | 1, 2, 3, 4, 5 | 7,210.6 ± 2.0 | 17,291.9 ± 27.2 | 16,216.2 ± 1.9 | 672 ± 0 | 95,835 ± 929 | 6.4 ± 0.0 | 780.8 ± 0.0 |
| 8 | 1 | 5 | 100 | push | converged | 1, 2, 3, 4, 5 | 203.2 ± 0.1 | 406.3 ± 0.3 | 413.0 ± 14.4 | 960 ± 0 | 91,402 ± 24 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 4 | 1 | 0.5 | 0 | pull | converged | 1, 2, 3, 4, 5 | 78.2 ± 82.3 | 555.6 ± 69.4 | 324.0 ± 255.8 | 3,360 ± 0 | 385,556 ± 6,129 | 32.0 ± 0.0 | 3,904.0 ± 0.0 |
| 4 | 1 | 0.5 | 0 | push | converged | 1, 2, 3, 4, 5 | 1.0 ± 0.0 | 2.9 ± 0.3 | 2.4 ± 0.2 | 480 ± 0 | 45,701 ± 12 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 4 | 1 | 0.5 | 100 | pull | converged | 1, 2, 3, 4, 5 | 254.3 ± 38.8 | 759.8 ± 5.5 | 798.0 ± 44.5 | 3,358 ± 4 | 385,239 ± 6,345 | 32.0 ± 0.0 | 3,904.0 ± 0.0 |
| 4 | 1 | 0.5 | 100 | push | converged | 1, 2, 3, 4, 5 | 101.3 ± 0.1 | 203.2 ± 0.3 | 202.8 ± 0.7 | 480 ± 0 | 45,701 ± 12 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 16 | 1 | 0.5 | 0 | pull | converged | 1, 2, 3, 4, 5 | 945.1 ± 181.9 | 2,058.3 ± 57.4 | 1,973.3 ± 198.2 | 13,377 ± 141 | 1,527,736 ± 30,932 | 126.9 ± 2.4 | 15,484.2 ± 294.6 |
| 16 | 1 | 0.5 | 0 | push | converged | 1, 2, 3, 4, 5 | 5.9 ± 0.4 | 14.7 ± 3.8 | 17.6 ± 12.5 | 1,920 ± 0 | 183,526 ± 97 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 16 | 1 | 0.5 | 100 | pull | converged | 1, 2, 3, 4, 5 | 1,755.4 ± 6.3 | 3,730.5 ± 0.8 | 3,794.4 ± 11.3 | 13,440 ± 0 | 1,527,577 ± 24,534 | 128.0 ± 0.0 | 15,616.0 ± 0.0 |
| 16 | 1 | 0.5 | 100 | push | converged | 1, 2, 3, 4, 5 | 407.3 ± 1.2 | 813.7 ± 5.5 | 812.7 ± 2.3 | 1,920 ± 0 | 183,526 ± 97 | 0.0 ± 0.0 | 0.0 ± 0.0 |

Push had lower mean run p95 in all 12 eight-peer settings and sent fewer
messages in 10. Every setting compares its own five matched seeds. The two
exceptions were the 1 update/s runs with a 5 s pull interval. At both loopback
delays, pull averaged 672 messages per run versus 960 for push, while sending
more application bytes. At 100 ms, the means were about 95,835 bytes for pull
and 91,402 bytes for push.

At 0.2 updates/s and 100 ms added loopback delay, changing the pull interval from 0.5 s to 5 s changed mean pull p95 from 1,746.9 to 15,209.7 ms and mean pull messages from 6,713.2 to 672.0 per run.

At 1 update/s and 100 ms added loopback delay, changing the pull interval from 0.5 s to 5 s changed mean pull p95 from 1,758.2 to 17,291.9 ms and mean pull messages from 6,720 to 672 per run.

At a 0.5 s pull interval and 100 ms added loopback delay, raising the rate from 0.2 to 1 update/s changed push messages from 192.0 to 960.0 per run and pull messages from 6,713.2 to 6,720.0.

Each pull interval has a paired push baseline. Those push runs share the same
workload and seeds across the interval batches, so any analysis across intervals
must keep the comparisons separate.

The scaling batches use 1 update/s and a 0.5 s pull interval. With 100 ms
added loopback delay, mean run p95 rose from 203.2 ms at 4 peers to 406.0 ms at
8 and 813.7 ms at 16 for push. For pull it rose from 759.8 ms to 1,758.2 ms and
3,730.5 ms across the same sizes. These measurements describe a single-host
TCP ring with added application delay.

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
| 1 | [Run record](raw/pilot-2026-11-15/push-delay0-seed1/result.json) | [Run record](raw/pilot-2026-11-15/pull-delay0-seed1/result.json) | [Run record](raw/pilot-2026-11-15/push-delay100-seed1/result.json) | [Run record](raw/pilot-2026-11-15/pull-delay100-seed1/result.json) |
| 2 | [Run record](raw/pilot-2026-11-15/push-delay0-seed2/result.json) | [Run record](raw/pilot-2026-11-15/pull-delay0-seed2/result.json) | [Run record](raw/pilot-2026-11-15/push-delay100-seed2/result.json) | [Run record](raw/pilot-2026-11-15/pull-delay100-seed2/result.json) |
| 3 | [Run record](raw/pilot-2026-11-15/push-delay0-seed3/result.json) | [Run record](raw/pilot-2026-11-15/pull-delay0-seed3/result.json) | [Run record](raw/pilot-2026-11-15/push-delay100-seed3/result.json) | [Run record](raw/pilot-2026-11-15/pull-delay100-seed3/result.json) |
| 4 | [Run record](raw/pilot-2026-11-15/push-delay0-seed4/result.json) | [Run record](raw/pilot-2026-11-15/pull-delay0-seed4/result.json) | [Run record](raw/pilot-2026-11-15/push-delay100-seed4/result.json) | [Run record](raw/pilot-2026-11-15/pull-delay100-seed4/result.json) |
| 5 | [Run record](raw/pilot-2026-11-15/push-delay0-seed5/result.json) | [Run record](raw/pilot-2026-11-15/pull-delay0-seed5/result.json) | [Run record](raw/pilot-2026-11-15/push-delay100-seed5/result.json) | [Run record](raw/pilot-2026-11-15/pull-delay100-seed5/result.json) |

## Future work

Peer-outage testing remains future work.
