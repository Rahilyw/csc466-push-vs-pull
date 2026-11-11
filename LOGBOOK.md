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

## 2026-11-10: Project repository and website set up
**Who:** Rahil
**Done:**
- Created this GitHub repository to serve as the project website and logbook.
- Added the submitted proposal ([PDF](docs/proposal/CSC466_Push_vs_Pull_Project_Proposal.pdf)).
- Added templates for bi-weekly updates and meeting notes, and a Python package skeleton for the testbed.

**Next:**
- [ ] Add every teammate as a collaborator on the repo
- [ ] Back-fill logbook entries for work done since the proposal (Weeks 1–4)
- [ ] Write and submit bi-weekly update 1 and update 2 (midterm)

---

## 2026-10-10: Project proposal submitted
**Who:** Rahil, Hamzah, Prabhnoor, Adithyakrishna
**Done:**
- Submitted the project proposal: push vs pull synchronization in a P2P ring of Python peers, with versioned keys and one writer per key.
- Experiment plan: update rate (1/5 s vs 1/s), pull interval (0.5, 2, 5 s), added delay (0 vs 100 ms), 8 peers (plus 4 and 16), at least 5 seeds per configuration.
- Metrics: propagation delay (median, p95), bytes and messages, final convergence time, idle traffic.

**Links:** [Proposal PDF](docs/proposal/CSC466_Push_vs_Pull_Project_Proposal.pdf)
