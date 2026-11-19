"""Run matched-seed push/pull comparisons for a configurable experiment setup."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pushpull.experiment import Config, run_experiment, source_fingerprint
from summarize import write_summary


def build_manifest(configurations):
    """Record every expected run, including ones that have not started yet."""
    runs = []
    for config in configurations:
        delay = float(config.delay_ms)
        label = str(int(delay)) if delay.is_integer() else repr(delay)
        runs.append({
            "directory": f"{config.mode}-delay{label}-seed{config.seed}",
            "config": asdict(config),
        })
    return {
        "schema_version": 1,
        "provenance": "before_run",
        "source_sha256": source_fingerprint(),
        "runs": runs,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    parser.add_argument("--peers", type=int, default=8)
    parser.add_argument("--rate", type=float, default=1.0)
    parser.add_argument("--pull-interval", type=float, default=0.5)
    parser.add_argument("--keys", type=int, default=16)
    parser.add_argument("--delay-ms", type=float, nargs="+", default=[0, 100])
    parser.add_argument("--duration", type=float, default=8)
    parser.add_argument("--settle", type=float, default=2)
    parser.add_argument("--idle", type=float, default=2)
    args = parser.parse_args(argv)
    if len(set(args.seeds)) != len(args.seeds):
        parser.error("seeds must be unique")
    if len(set(args.delay_ms)) != len(args.delay_ms):
        parser.error("delays must be unique")
    # Validate every setting before creating directories or starting workers.
    # One run keeps fixed parameters so summary comparisons remain matched.
    configurations = []
    try:
        for seed in args.seeds:
            modes = ("push", "pull") if seed % 2 == 0 else ("pull", "push")
            for delay in args.delay_ms:
                for mode in modes:
                    configurations.append(Config(
                        mode=mode, seed=seed, delay_ms=delay,
                        peers=args.peers, rate=args.rate,
                        pull_interval=args.pull_interval, keys=args.keys,
                        duration=args.duration, settle=args.settle, idle=args.idle,
                    ))
    except ValueError as exc:
        parser.error(str(exc))
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = build_manifest(configurations)
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    for config, planned in zip(configurations, manifest["runs"]):
        name = planned["directory"]
        result = run_experiment(config, args.output / name)
        print(f"{name}: {result['status']}, {result['metrics']['messages']} messages", flush=True)
        if result["status"] != "converged":
            raise RuntimeError(f"pilot failed: inspect {args.output / name}")
    write_summary(args.output)
    print(f"Saved raw logs and matched-seed summaries to {args.output}")


if __name__ == "__main__":
    main()
