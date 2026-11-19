# Longer loopback benchmark plan

Recorded November 19, 2026 before measured runs. The source baseline is `58eac1c`.

Each run uses a 60 s workload window, 25 s settling window and 20 s idle window.
The 25 s settling window gives a version time to cross four hops at a 5 s pull
interval plus message delay. The convergence deadline is the start of the idle
window. Application traffic is counted over the same 105 s across all runs.
Each batch uses seeds 1–5, 16 possible keys and both 0 and 100 ms added one-way
loopback delay. The pilot switches push/pull order by seed and writes its full
manifest before starting workers.

Run the six eight-peer batches sequentially, in ascending rate and interval
order, then the 4- and 16-peer scaling batches at 1 update/s and 0.5 s pull.
Each batch has 20 runs, for 160 total. The configured observation time alone is
4 h 40 min. Smoke checks are stored separately under `results/raw/scratch/`.
The three push baselines at a given eight-peer update rate are paired with
their own pull batch. They share seed IDs and workload schedules across pull
intervals, so they will be reported by batch without pooling as independent
observations. Scaling uses the eight-peer 1 update/s, 0.5 s batch as reference.

A convergence timeout is a measured deadline miss with raw CSVs and a result.
Worker or controller failures have their own diagnostics. Planned runs with
no result or failure record are unfinished. Keep all attempts, with their
original seed and configuration, and report coverage before drawing comparisons.

## Reproduce the benchmark

From the repository root, use a new output root for an independent full
reproduction. Run each command in the foreground and wait for it to exit before
starting the next batch. This preserves the planned order and host isolation.

```bash
root=results/raw/benchmark-reproduction
run_batch() {
  python experiments/pilot.py --output "$root/$1" \
    --peers "$2" --rate "$3" --pull-interval "$4" --keys 16 \
    --delay-ms 0 100 --seeds 1 2 3 4 5 --duration 60 --settle 25 --idle 20
}

run_batch peers8-rate0.2-pull0.5 8 0.2 0.5
run_batch peers8-rate0.2-pull2   8 0.2 2
run_batch peers8-rate0.2-pull5   8 0.2 5
run_batch peers8-rate1-pull0.5   8 1   0.5
run_batch peers8-rate1-pull2     8 1   2
run_batch peers8-rate1-pull5     8 1   5
run_batch peers4-rate1-pull0.5   4 1   0.5
run_batch peers16-rate1-pull0.5 16 1   0.5
```

To audit a batch, pass its directory to `experiments/summarize.py`. Use
`--audit` for partial coverage or nonconverged runs. It writes `audit.json`
with outcome counts and verified per-run metrics. The standard invocation
verifies a complete matched batch and writes `summary.csv` and `summary.json`.

```bash
python experiments/summarize.py "$root/peers8-rate0.2-pull0.5" --audit
python experiments/summarize.py "$root/peers8-rate0.2-pull0.5"
```

To continue a stopped batch, pick only the unfinished entries from its manifest
after checking that the original process has exited. Preserve any partial files
outside the batch directory. Run each remaining entry with `experiments/run.py`
using its exact manifest values and output path. For example, if seed 2's push
run at 0 ms never started in the first batch:

```bash
python experiments/run.py --mode push --peers 8 --rate 0.2 --pull-interval 0.5 \
  --keys 16 --delay-ms 0 --seed 2 --duration 60 --settle 25 --idle 20 \
  --output results/raw/benchmark-2026-11-19/peers8-rate0.2-pull0.5/push-delay0-seed2
```

Keep timeouts and error/crash diagnostics in the original batch. For mixed
outcomes, use the audit to report counts and link the raw data. Keep any planned
replication in its own directory.
