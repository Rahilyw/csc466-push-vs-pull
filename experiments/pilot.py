"""Run a paired eight-peer pilot at both delays; deliberately not the full matrix."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pushpull.experiment import Config, run_experiment
from summarize import write_summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    parser.add_argument("--duration", type=float, default=8)
    parser.add_argument("--settle", type=float, default=2)
    parser.add_argument("--idle", type=float, default=2)
    args = parser.parse_args()
    if len(set(args.seeds)) != len(args.seeds):
        parser.error("seeds must be unique")
    args.output.mkdir(parents=True, exist_ok=False)
    for seed in args.seeds:
        # Alternate mode order by seed; the paired workload is identical.
        modes = ("push", "pull") if seed % 2 == 0 else ("pull", "push")
        for delay in (0, 100):
            for mode in modes:
                name = f"{mode}-delay{delay}-seed{seed}"
                config = Config(mode=mode, seed=seed, delay_ms=delay,
                                duration=args.duration, settle=args.settle, idle=args.idle)
                result = run_experiment(config, args.output / name)
                print(f"{name}: {result['status']}, {result['metrics']['messages']} messages", flush=True)
                if result["status"] != "converged":
                    raise RuntimeError(f"pilot failed: inspect {args.output / name}")
    write_summary(args.output)
    print(f"Saved raw logs and matched-seed summaries to {args.output}")


if __name__ == "__main__":
    main()
