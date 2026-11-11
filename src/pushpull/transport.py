"""Messaging layer between peers (TCP sockets).

TODO:
- Length-prefixed JSON messages over TCP between ring neighbours.
- Optional added one-way delay per message (0 ms or 100 ms) applied here,
  so the delay experiments do not depend on OS network emulation.
- Count serialized bytes and messages sent, by message type, for the
  communication-overhead metric. TCP/IP headers are not counted.
"""
