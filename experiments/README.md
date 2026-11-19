# Running experiments

The controller starts independent peer processes with Python's `spawn` method.
Each process owns its store and two TCP ring neighbours. Control pipes carry
configuration, local writes and collected logs; the controller never relays
synchronization records.

## One run

From the repository root, using Python 3.11+:

```bash
python experiments/run.py --mode push --peers 8 --rate 1 \
  --duration 60 --settle 5 --idle 20 --delay-ms 100 --seed 1 \
  --output results/raw/my-push-run
```

Replay with `--mode pull --pull-interval 0.5` and a different output directory.
Keep all workload parameters and the seed unchanged for a paired comparison.
Existing output directories are rejected rather than overwritten. The runner,
metrics and scripts need only the standard library; pytest runs the tests.

| Option | Meaning | Default |
|---|---|---|
| `--mode` | `push` or `pull` | Required |
| `--peers` | Ring size, at least 3 | 8 |
| `--rate` | Updates per second; 0 gives an idle-only run | 1 |
| `--keys` | Number of possible keys | 16 |
| `--seed` | Seed for key/value selection | 1 |
| `--pull-interval` | Poll start-to-start interval, seconds; polls never overlap | 0.5 |
| `--delay-ms` | Added one-way delay on every application frame | 0 |
| `--duration` | Fixed workload window, seconds | 60 |
| `--settle` | Fixed no-write window before the convergence deadline | 5 |
| `--idle` | Fixed no-write measurement window after that deadline | 20 |
| `--output` | New result directory | Timestamped directory under `results/raw` |

Updates are scheduled regularly, starting at offset 0 while offset < duration.
A seeded generator chooses keys and values; key index modulo peer count fixes
its designated writer. Creation timestamps record when writes actually happen,
so controller/worker scheduling delay is not counted as network propagation.

## Matched-seed pilot

```bash
python experiments/pilot.py --output results/raw/my-pilot \
  --seeds 1 2 3 4 5 --duration 8 --settle 2 --idle 2
python experiments/summarize.py results/raw/my-pilot
```

By default the pilot runs 8 peers, both modes, delays 0 and 100 ms, rate 1 update/s
and a 0.5 s pull interval: 20 runs. Mode order alternates by seed. The second command
recomputes every metric from CSV logs before writing the comparison. It rejects
failed/incomplete runs, mismatched workloads, different source fingerprints,
duplicate seeds and unequal seed sets. This short pilot is not the full proposal
matrix of rates, pull intervals, sizes and longer observation windows.

The pilot also accepts `--peers`, `--rate`, `--pull-interval`, `--keys`, and one or
more values for `--delay-ms`. For example, to prepare a paired low-rate comparison:

```bash
python experiments/pilot.py --output results/raw/low-rate-interval2 \
  --seeds 1 2 3 4 5 --peers 8 --rate 0.2 --pull-interval 2 \
  --keys 16 --delay-ms 0 100 --duration 60 --settle 10 --idle 20
```

Each invocation holds the rate, interval, peer/key counts and window lengths
fixed across its runs. Use separate output directories for different setups;
the summary rejects comparisons mixing those fixed settings. Duplicate seeds or
delays and invalid settings are rejected before any output directory or worker
is created. This example is a command for future measurements, not a result.

### Completeness checks

Before starting the first worker, the pilot saves `manifest.json`: the expected
directory and complete configuration for every seed/mode/delay combination,
plus the source fingerprint. The plan remains available if a run fails.

Reanalysis requires every planned result and rejects unexpected result directories,
configuration changes and source mismatches before replacing any summaries. This
also catches a missing *entire mode or delay*, which matching only the surviving
seed sets cannot detect. Metrics are still recomputed from the raw CSV logs.

Older datasets without a manifest require an explicit override:

```bash
python experiments/summarize.py results/raw/older-dataset --allow-legacy
```

That option emits a warning and labels completeness `legacy_unverified` in the
summary; it cannot establish how many runs were originally intended. The published
November 15 pilot now has an `archived_plan` manifest reconstructed on November 18
from its documented 20-run setup and recorded configurations. This is a retrospective
audit, not a claim that the original experiment was preregistered.

For a batch with unfinished runs or measured failures, use `--audit`. This
verifies the available raw CSVs and writes an `audit.json` with a status for every
planned run. An audit records convergence timeouts separately from errors,
crashes, and unfinished runs. Use the standard summary command once all runs
have converged. See the [longer benchmark plan](../results/raw/benchmark-2026-11-19/plan.md).

## What gets saved

| File | Contents |
|---|---|
| Pilot `manifest.json` | Expected run directories/configurations, source fingerprint and plan provenance |
| `workload.csv` | Seeded update schedule, writer, key and value |
| `updates.csv` | Actual local creation timestamps and versions |
| `acceptances.csv` | Timestamp, peer, key and accepted version |
| `traffic.csv` | Successful send timestamp, sender, message type and application bytes |
| `result.json` | Configuration, environment, source/workload SHA-256, windows, process IDs, final state, errors and metrics |
| `failure.txt` | Diagnostic traceback if the controller or a worker fails |
| Pilot `summary.csv/json` | Mean and sample standard deviation across matched repetitions; JSON also records completeness verification |

## Metric definitions and limits

- **Propagation:** for every created version and every peer (including the
  writer), find its first acceptance of that version or a newer one before the
  convergence deadline. Report median/p95 in each run. Missing samples remain
  explicit; a missing final version yields `timeout`, not zero latency.
- **Convergence:** time from the last actual write until every peer holds every
  final version, measured from acceptance logs. Deadline = start + duration +
  settle. `final_state_matches` also checks values and writers when collecting.
- **Overhead:** all successful application sends in `[start, end)`, including
  duplicate pushes and empty pull replies. Count the four-byte prefix plus UTF-8
  JSON; exclude TCP/IP headers and controller traffic.
- **Idle:** sends in `[start + duration + settle, end)` divided by its fixed
  duration. A timeout may still have pending updates during this window; do not
  interpret its traffic as converged idle overhead.

All windows have the same duration across paired runs, independent of convergence.
Monotonic clocks are comparable across processes on this single host. This is
loopback with application delay, not an emulation of a wide-area network.
Source fingerprints cover all `src/pushpull/*.py` files. Summary latency fields
are **means of per-run medians/p95s**, not pooled quantiles; standard deviations
are across seeds, not confidence intervals. Application send counters record
successful drain, not confirmed delivery. Peers have timeouts but no retry or
churn recovery protocol. A nonconverged CLI run exits with status 1 and retains
its result logs; operational failures retain `failure.txt` and raise.
