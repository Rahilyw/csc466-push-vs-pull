"""Recompute and compare complete runs from a pilot result directory."""

import argparse
import csv
import json
from pathlib import Path
import sys
import warnings

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pushpull.metrics import aggregate_results, summarize


def _read_manifest(path: Path):
    manifest = json.loads(path.read_text(encoding="utf-8"))
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
    return plan, source, manifest.get("provenance", "unspecified")


def _load_plan(root: Path, paths: list[Path], *, allow_legacy: bool):
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        if not allow_legacy:
            raise ValueError("missing manifest.json; use --allow-legacy only for an unverified legacy run set")
        warnings.warn("No manifest: expected run-set completeness cannot be verified", UserWarning)
        return None, {
            "status": "legacy_unverified", "expected_runs": None, "observed_runs": len(paths),
        }
    plan, source, provenance = _read_manifest(manifest_path)
    observed = {path.parent.name for path in paths}
    missing, unexpected = set(plan) - observed, observed - set(plan)
    if missing or unexpected:
        raise ValueError(
            f"incomplete or unexpected run set: missing={sorted(missing)}, unexpected={sorted(unexpected)}"
        )
    return (plan, source), {
        "status": "complete", "expected_runs": len(plan), "observed_runs": len(paths),
        "manifest_provenance": provenance,
    }


def verify_result(path: Path, *, config=None, source=None):
    """Recompute one result from raw logs, including convergence timeouts."""
    result = json.loads(path.read_text(encoding="utf-8"))
    if config is not None and result.get("config") != config:
        raise ValueError(f"result configuration differs from plan: {path}")
    if source is not None and result.get("source_sha256") != source:
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
    expected_status = "error" if result["errors"] else (
        "converged" if recomputed["converged"] else "timeout"
    )
    if result["status"] != expected_status:
        raise ValueError(f"result status does not match the logs: {path}")
    return result


def write_summary(root: Path, *, allow_legacy: bool = False):
    results = []
    paths = sorted(root.glob("*/result.json"))
    planned, completeness = _load_plan(root, paths, allow_legacy=allow_legacy)
    for path in paths:
        plan, source = planned if planned is not None else (None, None)
        config = plan[path.parent.name] if plan is not None else None
        results.append(verify_result(path, config=config, source=source))
    rows = aggregate_results(results)
    with (root / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
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


def write_audit(root: Path):
    """Verify measured runs and record every planned outcome, even mid-batch."""
    plan, source, provenance = _read_manifest(root / "manifest.json")
    unexpected = {p.parent.name for p in root.glob("*/result.json")} - set(plan)
    if unexpected:
        raise ValueError(f"unexpected results: {sorted(unexpected)}")
    counts = dict.fromkeys(("converged", "timeout", "error", "crash", "unfinished"), 0)
    runs = []
    for name, config in plan.items():
        directory = root / name
        record = {"directory": name, "config": config}
        path = directory / "result.json"
        failure = directory / "failure.txt"
        if failure.exists():
            traceback = failure.read_text(encoding="utf-8").rstrip().splitlines()
            interrupted = bool(traceback and traceback[-1].startswith("KeyboardInterrupt"))
            status = "unfinished" if interrupted else "crash"
            record["diagnostic"] = f"{name}/failure.txt"
        elif path.exists():
            result = verify_result(path, config=config, source=source)
            status = result["status"]
            record.update(metrics=result["metrics"], errors=result["errors"],
                          workload_sha256=result["workload_sha256"])
        else:
            status = "unfinished"
        counts[status] += 1
        runs.append({**record, "status": status})
    audit = {"source_sha256": source, "manifest_provenance": provenance,
             "counts": counts, "runs": runs}
    (root / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return audit


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-legacy", action="store_true",
                        help="explicitly permit a run set without a manifest; mark completeness unverified")
    parser.add_argument("--audit", action="store_true",
                        help="verify available runs and list all outcomes, including unfinished runs")
    args = parser.parse_args(argv)
    try:
        if args.audit:
            audit = write_audit(args.directory)
            print(f"Run outcomes: {audit['counts']}")
            return
        rows = write_summary(args.directory, allow_legacy=args.allow_legacy)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"Recomputed {len(rows)} configuration summaries from raw CSV logs.")


if __name__ == "__main__":
    main()
