# Push vs Pull: Keeping P2P Data Synchronized

**University of Victoria · CSC 466 · Python 3.11+**

Verified locally: **83 automated tests passing** · **20 converged eight-peer pilot runs**

Rahil Wijeyesekera · Hamzah Banday · Prabhnoor Singh · Adithyakrishna Arunkumar

[Latest update PDF](docs/updates/update-03-networking-and-pilot.pdf) ·
[Experiment guide](experiments/README.md) · [Results](results/README.md) ·
[Logbook](LOGBOOK.md) · [Project website](https://rahilyw.github.io/csc466-push-vs-pull/)

A small peer-to-peer key-value store for comparing **update propagation speed**
with **communication overhead**. Peers communicate over TCP in a ring, with two
neighbours each. A key has one designated writer and increasing version numbers.

| Push | Pull |
|---|---|
| Forward a newly accepted version to both neighbours immediately. | Periodically send each neighbour a version summary. |
| Drop stale and duplicate records without forwarding. | Receive only newer records in one reply on the same TCP connection. |
| No periodic synchronization traffic while idle. | Polls continue during idle windows, including empty replies. |

The pull implementation follows the [midterm design](docs/updates/update-02-midterm.md):
one request and one reply per neighbour, replacing the proposal's older two-step
exchange. The experiment controller never relays synchronization records.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install pytest
python -m pytest
```

The runtime, runner and result summaries use Python's standard library. The
broader `requirements.txt` also lists packages planned for data analysis/plots.

Run a short eight-process experiment:

```bash
python experiments/run.py --mode push --peers 8 --rate 1 --seed 1 \
  --duration 8 --settle 2 --idle 2 --delay-ms 100
```

Use `--mode pull --pull-interval 0.5` with the same seed and workload parameters
for the matching pull run. Each invocation creates a new timestamped directory
under `results/raw`. See the [experiment guide](experiments/README.md) for the
paired pilot command, every parameter, output formats and metric definitions.

## What is implemented

| Component | Behaviour and evidence |
|---|---|
| Versioned store | Increasing versions, designated-writer local writes, stale/duplicate rejection; original store tests retained. |
| TCP transport | Four-byte length prefix + UTF-8 JSON; configurable sender delay; exact application bytes/messages by type. |
| Push / pull peers | Forward only accepted push records; periodic one-round-trip pull; monotonic acceptance/send events. |
| Correctness checks | Four real-loopback peers in both modes at 0 and 100 ms; duplicate suppression, exact poll exchanges, framing and cleanup. |
| Experiment runner | One spawned process per peer; seeded writes, independent TCP ring, fixed workload/settling/idle windows, raw CSV/JSON. |
| Metrics | Propagation median/p95, final convergence/timeout, total messages/bytes and idle traffic; raw-log recomputation and planned-run completeness checks. |

For focused checks:

```bash
python -m pytest tests/test_transport.py tests/test_peers.py
python -m pytest tests/test_metrics.py tests/test_experiment.py
PYTHONASYNCIODEBUG=1 python -W error -m pytest
```

Single-process socket tests establish correctness. Multi-process runner tests
also verify separate worker PIDs, deterministic workloads, saved-log metrics,
cleanup after controller failure and explicit convergence timeouts. Performance
observations belong in [results](results/README.md), with their raw evidence and
limitations, rather than being inferred from test execution times.

## Results and next steps

The [results index](results/README.md) documents the first repeated eight-peer
pilot and links every saved run. These short loopback observations are preliminary.
The planned full study still includes both update rates, all three pull intervals,
longer workload/idle windows, and 4/16-peer scaling checks.

| Planned parameter | Values |
|---|---|
| Update rate | 1 update / 5 s; 1 update / s |
| Pull interval | 0.5 s; 2 s; 5 s |
| Added one-way delay | 0 ms; 100 ms per application message |
| Peers | 8 main; 4 and 16 scaling checks |
| Repetitions | At least five matched seeds per configuration |

Peers currently assume a stable ring on one host. There is no churn/recovery
protocol or automatic retry. Byte counts include the four-byte application
prefix and JSON, excluding TCP/IP headers and controller messages. Acceptance
and send events use the shared host monotonic clock; raw logs make the summaries
auditable. The [experiment guide](experiments/README.md) explains deadlines,
missing samples, equal observation windows and quantile aggregation.

## Repository map

```text
src/pushpull/       store, TCP transport, peers, experiment orchestration, metrics
experiments/       command-line runner, matched-seed pilot, log reanalysis guide
tests/             store, socket, metrics and spawned-process checks
results/           findings index, raw run logs and reproducible summaries
LOGBOOK.md         dated contributions, verification and next tasks
docs/              proposal, historical updates, meetings and presentation/report folders
```

## Contributions

The team co-authored the proposal, which describes the TCP ring, the push and
pull comparison, and the experiment plan. [Project proposal](docs/proposal/CSC466_Push_vs_Pull_Project_Proposal.pdf)

- **Rahil Wijeyesekera** set up the repository, GitHub Pages, and the logbook.
  He implemented the original versioned store and its four tests and wrote the
  first two project updates. [Store and project setup](https://github.com/Rahilyw/csc466-push-vs-pull/commit/1cdcead)
- **Hamzah Banday** co-authored the project proposal and contributed to the
  team's study design for comparing push and pull. [Proposal and study design](docs/proposal/CSC466_Push_vs_Pull_Project_Proposal.pdf)
- **Prabhnoor Singh** co-authored the project proposal and contributed to the
  team's study design for comparing push and pull. [Proposal and study design](docs/proposal/CSC466_Push_vs_Pull_Project_Proposal.pdf)
- **Adithyakrishna Arunkumar (Adi)** implemented the TCP push and pull protocols
  and added loopback tests for both. He built the seeded multi-process benchmark
  runner and its propagation, convergence, and traffic metrics, then ran the
  first eight-peer pilot. He later built raw-log verification tools and run
  manifest checks to audit benchmark results. For the longer benchmark, he set
  the measurement windows, ran the first matched set of four eight-peer runs,
  and verified their metrics from the raw logs. That set covered both modes
  at 0 and 100 ms added loopback delay with seed 1, at 0.2 updates/s and a 0.5 s
  pull interval.
  [Implementation history](https://github.com/Rahilyw/csc466-push-vs-pull/compare/1324c57...58eac1c) ·
  [Verified benchmark checkpoint](https://github.com/Rahilyw/csc466-push-vs-pull/blob/d898e0ce5d498ff2fb771f5f09bfe09778ad16fa/results/README.md)

[Project logbook](LOGBOOK.md)

## Course deliverables

| Deliverable | Recorded status | Link |
|---|---|---|
| Proposal | Submitted October 10, 2026 | [PDF](docs/proposal/CSC466_Push_vs_Pull_Project_Proposal.pdf) |
| Bi-weekly update 1 | PDF prepared November 10; course posting not recorded | [Draft](docs/updates/update-01.md) · [PDF](docs/updates/update-01.pdf) |
| Midterm update | PDF prepared November 10; course posting not recorded | [Draft](docs/updates/update-02-midterm.md) · [PDF](docs/updates/update-02-midterm.pdf) |
| Project update 3 | Prepared November 15; not posted to the course thread | [Draft](docs/updates/update-03-networking-and-pilot.md) · [PDF](docs/updates/update-03-networking-and-pilot.pdf) |
| Logbook | Ongoing | [Entries](LOGBOOK.md) |
| Presentations | Pending | [Folder](https://github.com/Rahilyw/csc466-push-vs-pull/tree/main/docs/presentations) |
| Final report | Pending; separate from these implementation changes | [Folder](https://github.com/Rahilyw/csc466-push-vs-pull/tree/main/docs/report) |

The dated updates describe their original periods. New implementation progress
is recorded in the logbook and results index; their PDFs were not rewritten.

## Reference

A. Demers et al., “Epidemic Algorithms for Replicated Database Maintenance,”
*PODC*, 1987, pp. 1–12. [doi:10.1145/41840.41841](https://doi.org/10.1145/41840.41841)
