# Push vs Pull: Bi-weekly Update 1

**CSC 466 · University of Victoria**
Rahil Wijeyesekera · Hamzah Banday · Prabhnoor Singh · Adithyakrishna Arunkumar
**Period covered:** 2026-10-10 to 2026-10-24 · **Written:** 2026-11-10
**Project site:** https://rahilyw.github.io/csc466-push-vs-pull/

This update is late. It was written on November 10, with the midterm update, and still has to be posted on the course thread.

## 1. Summary

The proposal was submitted on October 10. During this period the experiment was fixed: a ring of Python peers, one writer per key, increasing version numbers, and the same update sequence for push and pull. No testbed code was written before October 24.

## 2. Progress since last update

| Task | Owner | Status | Evidence |
|------|-------|--------|----------|
| Write the project proposal and post it on the course thread | Whole team | Done | Thread post on October 10. PDF: `docs/proposal/CSC466_Push_vs_Pull_Project_Proposal.pdf` |
| Fix the topology, the workload, and the metrics | Whole team | Done | Proposal sections 3 and 4 |

## 3. Results so far

There are no measurements. The repository did not exist yet, so there is no configuration or seed to report.

## 4. Problems and changes to the plan

The proposal put peer connections in week 1 and push and pull in week 2. Neither had started by October 24. The question, the ring, the workload, and the metrics are unchanged.

## 5. Plan for the next two weeks

This is the plan as it stood on October 24. The midterm update says what happened instead.

| Task | Owner | Target date |
|------|-------|-------------|
| Versioned store and connections between neighbours | Team | 2026-10-31 |
| Push and pull on a ring of 4 peers | Team | 2026-11-07 |
| Check that both modes reach the same final versions | Team | 2026-11-07 |

## 6. Contributions

| Member | Work this period |
|--------|------------------|
| Rahil Wijeyesekera | Proposal, with the rest of the team. No separate implementation was logged. |
| Hamzah Banday | Proposal, with the rest of the team. No separate work was logged for this period. |
| Prabhnoor Singh | Proposal, with the rest of the team. No separate work was logged for this period. |
| Adithyakrishna Arunkumar | Posted the proposal on the course thread on October 10. Proposal, with the rest of the team. |

Anyone whose work from these two weeks is missing should add it before the PDF is posted.
