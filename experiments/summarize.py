"""Recompute and compare complete runs from a pilot result directory."""

import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pushpull.metrics import aggregate_results, summarize


def write_summary(root: Path):
    results = []
    paths = sorted(root.glob("*/result.json"))
    for path in paths:
        result = json.loads(path.read_text())

        def read(name, numeric):
            with (path.parent / name).open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            for row in rows:
                for key, kind in numeric.items():
                    row[key] = kind(row[key])
            return rows

        recomputed = summarize(
            read("updates.csv", {"version": int, "timestamp": float}),
            read("acceptances.csv", {"peer_id": int, "version": int, "timestamp": float}),
            read("traffic.csv", {"bytes": int, "timestamp": float}),
            peers=result["config"]["peers"],
            **{k: result["windows"][k] for k in ("start", "convergence_deadline", "idle_start", "end")},
        )
        if recomputed != result["metrics"]:
            raise ValueError(f"raw logs do not match metrics: {path}")
        results.append(result)
    rows = aggregate_results(results)
    with (root / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (root / "summary.json").write_text(json.dumps({
        "runs": [str(p.relative_to(root)) for p in paths],
        "source_sha256": results[0]["source_sha256"],
        "latency_summary": "mean and sample standard deviation of per-run quantiles; not pooled quantiles",
        "rows": rows,
    }, indent=2) + "\n", encoding="utf-8")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    rows = write_summary(args.directory)
    print(f"Recomputed {len(rows)} configuration summaries from raw CSV logs.")
