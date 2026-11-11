# Push vs Pull: Keeping P2P Data Synchronized

**CSC 466 course project, University of Victoria**
Rahil Wijeyesekera · Hamzah Banday · Prabhnoor Singh · Adithyakrishna Arunkumar

We compare two ways of keeping shared data synchronized across a peer-to-peer network:

- **Push**: a peer sends an update to its neighbours as soon as it learns about a change.
- **Pull**: each peer checks its neighbours at a fixed interval and requests anything newer.

Our question: **how does each approach trade update speed for communication overhead as the update rate and network delay change?**

This repository is our project website and logbook. It holds the code, the experiment data, and every update we submit.

---

## Project deliverables

| # | Deliverable | Weight | Status | Link |
|---|-------------|--------|--------|------|
| 0 | Project proposal / outline | 5% | Submitted Oct 10, 2026 | [PDF](docs/proposal/CSC466_Push_vs_Pull_Project_Proposal.pdf) |
| 1 | Bi-weekly update 1 | (log book) | Not started | [draft](docs/updates/update-01.md) |
| 2 | Bi-weekly update 2 (midterm update) | (log book) | Not started | [draft](docs/updates/update-02-midterm.md) |
| 3 | Log book | 5% | Ongoing | [LOGBOOK.md](LOGBOOK.md) |
| 4 | Midterm presentation | 5% | Not started | [docs/presentations](docs/presentations/) |
| 5 | Final presentation | 10% | Not started | [docs/presentations](docs/presentations/) |
| 6 | Project report + code | 30% | Not started | [docs/report](docs/report/), [src](src/) |

When a PDF is submitted, add it next to its draft (for example `docs/updates/update-01.pdf`), link it in this table, and add a line to the [logbook](LOGBOOK.md).

---

## Approach (from the proposal)

- A small P2P key-value store in Python. Each peer runs as its own process on one machine and talks to others over TCP sockets.
- Each key has one designated writer and an increasing version number, so there are no conflicting edits.
- **Topology:** a ring, where each peer talks to its two neighbours. The same topology is used for push and pull.
- **Push:** a new version goes to both neighbours and is forwarded the first time it is received. The version check stops duplicates.
- **Pull:** a peer asks each neighbour for its version list, then requests only the records that are newer.
- **Network sizes:** 8 peers for the main runs, with smaller checks at 4 and 16.
- A separate runner script starts runs, generates updates and collects logs. It never relays sync traffic.

### Experiment parameters

| Parameter | Values |
|-----------|--------|
| Update rate | 1 update / 5 s (low), 1 update / s (high) |
| Pull interval | 0.5 s, 2 s, 5 s |
| Added one-way delay | 0 ms, 100 ms (applied in the messaging layer) |
| Peers | 8 (main), 4 and 16 (scaling checks) |
| Repetitions | ≥ 5 seeds per configuration, same seed replayed for push and pull |
| Idle period | Fixed window with no updates, to measure polling traffic |

### Metrics

| Metric | Definition |
|--------|------------|
| Update propagation delay | Time from creating a version until each peer holds it (or newer). Median and p95. |
| Communication overhead | Serialized application bytes and message count, including requests, replies and duplicates (no TCP/IP headers). |
| Final convergence time | Time from the last update until all peers hold the final version of every key. A run that never converges is recorded as a timeout. |
| Idle traffic | Bytes and messages per second during the idle period. |

---

## Schedule

| Week | Plan | Status |
|------|------|--------|
| 1 | Review prior work; peer connections, record storage, version checks | ☐ |
| 2 | Implement push and pull; final-state correctness on a small network | ☐ |
| 3–4 | Workload generation, delay controls, logging; repeated experiments | ☐ |
| 5 | Analyse results, make plots, investigate unexpected behaviour | ☐ |
| 6 | Final report, demo, presentation | ☐ |

---

## Repository layout

```
LOGBOOK.md            dated project log (newest first)
docs/
  proposal/           submitted proposal PDF
  updates/            bi-weekly updates (Markdown draft + submitted PDF)
  meetings/           team meeting notes
  presentations/      midterm and final slides
  report/             final report
src/pushpull/         Python testbed (peer, store, push, pull, transport)
experiments/          experiment configs and runner
results/raw/          CSV logs from runs
results/plots/        generated figures
tests/                correctness tests
```

## Running the code

Requires Python 3.11 or later.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest
```

The experiment runner (`experiments/run.py`) is a stub for now. This section will be filled in once it works.

---

## How we use this repo

1. **Log as you go.** After a meeting or a meaningful work session, add a dated entry to [LOGBOOK.md](LOGBOOK.md): what was done, by whom, and what's next. The grade covers the log, not only the code.
2. **Meetings.** Copy [docs/meetings/TEMPLATE.md](docs/meetings/TEMPLATE.md) to `docs/meetings/YYYY-MM-DD.md`.
3. **Bi-weekly updates.** Write the update in `docs/updates/`, export it to PDF, commit the PDF, post it to the course project thread, and update the table above.
4. **Code.** Work on a branch and open a pull request into `main`. Keep `main` runnable.
5. **Results.** Commit the CSVs that a figure or the report depends on. Note in the logbook which commit and seed produced them.

## Reference

[1] A. Demers, D. Greene, C. Hauser, W. Irish, J. Larson, S. Shenker, H. Sturgis, D. Swinehart and D. Terry. "Epidemic Algorithms for Replicated Database Maintenance." *Proc. 6th ACM Symposium on Principles of Distributed Computing*, 1987, pp. 1–12. doi:[10.1145/41840.41841](https://doi.org/10.1145/41840.41841)
