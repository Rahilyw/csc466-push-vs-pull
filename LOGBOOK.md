# Project Logbook

Push vs Pull: Keeping P2P Data Synchronized (CSC 466)

Newest entries first. Each entry covers what was done, who did it, any decisions or problems, and what's next.
Link to commits, PRs, meeting notes, or result files where they exist.

<!--
Entry template — copy this block to the top of the log:

## YYYY-MM-DD — Short title
**Who:** names
**Done:**
- ...
**Decisions / problems:**
- ...
**Next:**
- [ ] task (owner)
**Links:** commit / PR / meeting notes / results
-->

---

## 2026-11-15 — Seeded runner, measured pilot and repository organization
**Who:** Adithyakrishna Arunkumar / Adi (`akaAdiArun`)
**Done:**
- Built the seeded multi-process runner: independent spawned peers, fixed writers, regular update schedule, TCP ring synchronization, equal workload/settling/idle windows, cleanup and explicit timeout/error results.
- Added per-send event logs, raw workload/update/acceptance/traffic CSVs, JSON metadata, content fingerprints and final-record checks. Implemented propagation median/p95, final convergence, bytes/messages and idle rates.
- Added reanalysis that recomputes metrics from raw logs and rejects incomplete or mismatched comparisons. Paired workloads are identical across modes/delays for each seed; summary quantiles are means of per-run quantiles, with sample standard deviation across seeds.
- Extended coverage to **54 tests**, retaining the original four store tests. Verified `python -m pytest` (**54 passed**, 18.12 s) and `PYTHONASYNCIODEBUG=1 python -W error -m pytest` (**54 passed**, 19.26 s), using the workspace virtual environment and Python 3.12.14. `git diff --check` passed.
- Fixed an intermittent Python 3.12 pending-accept shutdown race exposed by the debug checks. Peers now own and join their socket accept loop; regression coverage stops peers while TCP connections are arriving.
- Ran **20 real eight-process pilot experiments**: modes push/pull × delays 0/100 ms × seeds 1–5. Each used rate 1/s, pull interval 0.5 s, 8 s workload + 2 s settling + 2 s idle. **20/20 converged**, all final records matched, 1,280 propagation samples, zero missing samples or recorded worker errors.
- Observed 128 push messages/run and 768 pull messages/run; idle rates were 0 and 64 messages/s respectively. These are pilot observations for this configuration, not full-study conclusions. Latency values and variation are in the results index and raw summaries.
- Reorganized the README around setup, implementation, experiments, evidence and team contributions; added the experiment guide and results index. Preserved Rahil's original store and historical updates. After completing code and the pilot, prepared project update 3 as Markdown and a three-page PDF at Adi's request, with test evidence, measured results and download links. The final report and course posting remain pending.

**Decisions / problems:**
- Publication was initially blocked by GitHub integration permissions. Rahil enabled access; the two implementation commits were pushed to `main` and GitHub confirmed author/committer `akaAdiArun`. Source for the pilot is `4484d97`; metadata also records a content fingerprint independent of author metadata.
- The earlier 25-test milestone passed its initial checks, but expanded debug verification exposed another intermittent shutdown issue; the 54-test suite verifies the final implementation including that fix.
- Single-host loopback timings, short windows and regular update/poll phases limit interpretation. In particular, the 0 ms pull median varies across seeds. Controller traffic is excluded; application framing is included.

**Next:**
- [ ] Longer runs across both rates and all pull intervals, then 4/16-peer scaling checks
- [ ] Investigate timing variability and repeat on a controlled host
- [x] Prepare project update 3 draft/PDF after the implementation and pilot
- [ ] Prepare the final report and presentations separately

**Links:** [experiment guide](experiments/README.md) · [findings and raw data](results/README.md) · [source commit](https://github.com/Rahilyw/csc466-push-vs-pull/commit/4484d975d41f721f8f2538412cdf3741312b8ad5)

---

## 2026-11-15 — TCP push/pull milestone verified locally
**Who:** Adi (`akaAdiArun`)
**Done:**
- Started local branch `adi/tcp-push-pull` from main `1324c57`. Verified the existing four store tests before implementation; networking and synchronization were still stubs.
- Implemented four-byte length-prefixed UTF-8 JSON over TCP, configurable one-way delay per frame, and sender message/byte counts by type. Bytes include application framing, excluding TCP/IP headers.
- Implemented push forwarding only for accepted newer versions, periodic pull with one summary request and one newer-records reply per neighbour, and in-memory monotonic acceptance events for later metric computation.
- Added real-loopback four-peer tests for final records in push and pull at both 0 ms and 100 ms added delay, bounded push forwarding under duplicate/stale injections, and exact pull request/reply counts and bytes (including empty replies).
- Added transport framing, malformed-frame, delay, timeout and peer-shutdown checks. A pending-frame shutdown test exposed a wait ordering issue on Python 3.12; handlers now close before waiting for the server to finish closing. The asyncio debug check also caught sockets left open when a handler was cancelled before its first step; a completion callback now closes them in that case.
- Verification on Python 3.12.14: `python -m pytest` — **25 passed**. Also verified with `PYTHONASYNCIODEBUG=1 python -W error -m pytest` — **25 passed**. Used a workspace virtual environment with pytest installed.
- Added README test commands and API/counter notes. Changes are local for review; no push, merge, PR, report, PDF or course post was made.

**Decisions / problems:**
- Followed the midterm's one-round-trip pull design. The four peers share an event loop in these tests but exchange synchronization traffic over real TCP sockets. This is correctness evidence, not a multi-process performance experiment.
- Acceptance events and counters are in memory; durable export and aggregate metrics remain runner work. Exchanges time out without automatic retries; background errors are retained on each peer.

**Next:**
- [ ] Build the seeded multi-process runner, durable logs and metric aggregation
- [ ] Run the planned repeated eight-peer experiments and idle windows; record actual results

**Links:** [peer](src/pushpull/peer.py) · [transport](src/pushpull/transport.py) · [peer tests](tests/test_peers.py) · [transport tests](tests/test_transport.py)

---

## 2026-11-10 — Bi-weekly updates written
**Who:** Rahil
**Done:**
- Wrote bi-weekly update 1 (October 10–24) and the midterm update (October 25–November 10).
- Exported both to PDF. Re-ran `python -m pytest`: 4 passed.
- Recorded the pull change: one round trip, using `version_vector` and `newer_than`. Pull itself is not implemented.

**Decisions / problems:**
- Both updates are late. They describe only work that is in the log or the repository. Teammates still need to add anything that was not logged.
- The PDFs are not on the course thread yet.

**Next:**
- [ ] Post both PDFs on the October 10 course thread, with the website link
- [ ] Teammates add any missing work to section 6 of each update before that post
- [ ] Length-prefixed TCP, delay, and byte counts (team, 2026-11-17)
- [ ] Push, then pull (team, 2026-11-19)
- [ ] Four peers, both modes, same final versions (team, 2026-11-21)

**Links:** [update 1 PDF](docs/updates/update-01.pdf) · [midterm PDF](docs/updates/update-02-midterm.pdf) · [website](https://rahilyw.github.io/csc466-push-vs-pull/)

---

## 2026-11-10: Project repository and website set up
**Who:** Rahil
**Done:**
- Created this GitHub repository to serve as the project website and logbook.
- Added the submitted proposal ([PDF](docs/proposal/CSC466_Push_vs_Pull_Project_Proposal.pdf)).
- Added templates for bi-weekly updates and meeting notes, and a Python package skeleton for the testbed.

**Next:**
- [ ] Add every teammate as a collaborator on the repo
- [ ] Back-fill logbook entries for work done since the proposal (Weeks 1–4)
- [x] Write bi-weekly update 1 and update 2 (see the later entry on this date)
- [ ] Post both PDFs on the course thread

---

## 2026-10-10: Project proposal submitted
**Who:** Rahil, Hamzah, Prabhnoor, Adithyakrishna
**Done:**
- Submitted the project proposal: push vs pull synchronization in a P2P ring of Python peers, with versioned keys and one writer per key.
- Experiment plan: update rate (1/5 s vs 1/s), pull interval (0.5, 2, 5 s), added delay (0 vs 100 ms), 8 peers (plus 4 and 16), at least 5 seeds per configuration.
- Metrics: propagation delay (median, p95), bytes and messages, final convergence time, idle traffic.

**Links:** [Proposal PDF](docs/proposal/CSC466_Push_vs_Pull_Project_Proposal.pdf)
