"""Compute experiment metrics from run logs.

TODO:
- Propagation delay: for each (key, version), the time from its creation until
  each peer holds that version or newer. Report the median and p95.
- Communication overhead: total bytes and messages over equal-length runs.
- Final convergence time: from the last update until every peer holds the final
  version of every key. Record a timeout if this never happens.
- Idle traffic: bytes/s and messages/s during the idle window.
"""
