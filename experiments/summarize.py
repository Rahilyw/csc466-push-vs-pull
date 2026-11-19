"""Recompute and compare complete runs from a pilot result directory."""

import argparse
import csv
import json
from pathlib import Path
import sys
import warnings

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pushpull.metrics import aggregate_results, summarize


def _load_plan(root: Path, paths: list[Path], *, allow_legacy: bool):
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        if not allow_legacy:
            raise ValueError("missing manifest.json; use --allow-legacy only for an unverified legacy run set")
        warnings.warn("No manifest: expected run-set completeness cannot be verified", UserWarning)
        return None, {
            "status": "legacy_unverified", "expected_runs": None, "observed_runs": len(paths),
        }
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("unsupported experiment manifest schema")
    runs = manifest.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("manifest must contain planned runs")
    plan = {}
    for run in runs:
        if not isinstance(run, dict) or not isinstance(run.get("directory"), str) or not isinstance(run.get("config"), dict):
            raise ValueError("invalid planned run in manifest")
        name = run["directory"]
        if name in plan:
            raise ValueError(f"duplicate planned run: {name}")
        plan[name] = run["config"]
    source = manifest.get("source_sha256")
    if not isinstance(source, str) or not source:
        raise ValueError("manifest must record a source fingerprint")
    observed = {path.parent.name for path in paths}
    missing, unexpected = set(plan) - observed, observed - set(plan)
    if missing or unexpected:
        raise ValueError(
            f"incomplete or unexpected run set: missing={sorted(missing)}, unexpected={sorted(unexpected)}"
        )
    return (plan, source), {
        "status": "complete", "expected_runs": len(plan), "observed_runs": len(paths),
        "manifest_provenance": manifest.get("provenance", "unspecified"),
    }


def write_summary(root: Path, *, allow_legacy: bool = False):
    results = []
    paths = sorted(root.glob("*/result.json"))
    planned, completeness = _load_plan(root, paths, allow_legacy=allow_legacy)
    for path in paths:
        result = json.loads(path.read_text())
        if planned is not None:
            plan, source = planned
            if result.get("config") != plan[path.parent.name]:
                raise ValueError(f"result configuration differs from plan: {path}")
            if result.get("source_sha256") != source:
                raise ValueError(f"result source differs from plan: {path}")

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
        "completeness": completeness,
        "latency_summary": "mean and sample standard deviation of per-run quantiles; not pooled quantiles",
        "rows": rows,
    }, indent=2) + "\n", encoding="utf-8")
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-legacy", action="store_true",
                        help="explicitly permit a run set without a manifest; mark completeness unverified")
    args = parser.parse_args(argv)
    try:
        rows = write_summary(args.directory, allow_legacy=args.allow_legacy)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"Recomputed {len(rows)} configuration summaries from raw CSV logs.")


if __name__ == "__main__":
    main()
