"""A single peer process: owns a VersionedStore and runs one sync strategy.

TODO:
- Start up with a peer id, the addresses of its two ring neighbours, and a mode (push or pull).
- Push mode: when a record is first stored (local write or received), send it to
  both neighbours. Records that are not newer are dropped and not forwarded.
- Pull mode: every `pull_interval` seconds, send each neighbour our
  version_vector(), receive the newer records, and apply them.
- Log (monotonic time, peer id, key, version) each time a record is stored,
  so propagation delay and convergence can be computed afterwards.
"""
