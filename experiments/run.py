"""Run a seeded experiment; see experiments/README.md for parameters and logs."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

# Support the documented command directly from a fresh checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pushpull.experiment import Config, run_experiment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("push", "pull"), required=True)
    parser.add_argument("--peers", type=int, default=8)
    parser.add_argument("--rate", type=float, default=1.0)
    parser.add_argument("--pull-interval", type=float, default=0.5)
    parser.add_argument("--delay-ms", type=float, default=0)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--duration", type=float, default=60)
    parser.add_argument("--settle", type=float, default=5)
    parser.add_argument("--idle", type=float, default=20)
    parser.add_argument("--keys", type=int, default=16)
    parser.add_argument("--output", type=Path)
    args = vars(parser.parse_args())
    output = args.pop("output")
    try:
        config = Config(**args)
        output = output or Path("results/raw") / (
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            + f"-{config.mode}-seed{config.seed}"
        )
        result = run_experiment(config, output)
    except (ValueError, FileExistsError) as exc:
        parser.error(str(exc))
    print(f"{result['status']}: {output}")
    print(f"messages={result['metrics']['messages']}, bytes={result['metrics']['bytes']}")
    return 0 if result["status"] == "converged" else 1


if __name__ == "__main__":
    raise SystemExit(main())
