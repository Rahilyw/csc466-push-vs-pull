"""Experiment runner.

Starts N peer processes in a ring, replays a seeded update sequence, waits for
the idle window, then collects the logs into results/raw/*.csv.
The runner never relays sync traffic between peers.

TODO: implement. Planned interface:
    python experiments/run.py --mode push|pull --peers 8 --rate 1.0 \
        --pull-interval 2.0 --delay-ms 0 --seed 1 --duration 60 --idle 20
"""

if __name__ == "__main__":
    raise SystemExit("experiments/run.py is not implemented yet. See the TODO in this file.")
