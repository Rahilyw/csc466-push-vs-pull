"""Result-set completeness checks using copies of the committed real pilot logs."""

import csv
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from pushpull.experiment import Config


EXPERIMENTS = Path(__file__).resolve().parents[1] / "experiments"
ARCHIVE = EXPERIMENTS.parent / "results/raw/pilot-2026-11-15"


@pytest.fixture
def sample(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(EXPERIMENTS))
    summary = importlib.import_module("summarize")
    pilot = importlib.import_module("pilot")
    root = tmp_path / "sample"
    root.mkdir()
    configs = []
    for directory in sorted(ARCHIVE.glob("*-seed1")):
        shutil.copytree(directory, root / directory.name)
        result = json.loads((directory / "result.json").read_text())
        configs.append(Config(**result["config"]))
    manifest = pilot.build_manifest(configs)
    (root / "manifest.json").write_text(json.dumps(manifest))
    return root, summary, manifest


def preserve_existing_summary(root):
    for name in ("summary.csv", "summary.json"):
        (root / name).write_text("previous summary")


def assert_summary_unchanged(root):
    for name in ("summary.csv", "summary.json"):
        assert (root / name).read_text() == "previous summary"


def test_complete_plan_recomputes_real_logs(sample):
    root, summary, _ = sample
    rows = summary.write_summary(root)
    assert len(rows) == 4
    for row in rows:
        assert row["runs"] == 1
        assert row["mean_messages"] == (128 if row["mode"] == "push" else 768)
    saved = json.loads((root / "summary.json").read_text())
    assert saved["completeness"] == {
        "status": "complete", "expected_runs": 4, "observed_runs": 4,
        "manifest_provenance": "before_run",
    }


@pytest.mark.parametrize("removed", [
    ["push-delay0-seed1"],
    ["push-delay0-seed1", "push-delay100-seed1"],
    ["push-delay100-seed1", "pull-delay100-seed1"],
])
def test_missing_run_or_entire_mode_or_delay_is_rejected(sample, removed):
    root, summary, _ = sample
    for directory in removed:
        shutil.rmtree(root / directory)
    preserve_existing_summary(root)
    with pytest.raises(ValueError, match="missing="):
        summary.write_summary(root)
    assert_summary_unchanged(root)


def test_missing_result_json_is_not_treated_as_completed(sample):
    root, summary, _ = sample
    (root / "push-delay0-seed1/result.json").unlink()
    with pytest.raises(ValueError, match="push-delay0-seed1"):
        summary.write_summary(root)


def test_unplanned_result_directory_is_rejected(sample):
    root, summary, _ = sample
    shutil.copytree(root / "push-delay0-seed1", root / "extra-run")
    with pytest.raises(ValueError, match="unexpected=.*extra-run"):
        summary.write_summary(root)


@pytest.mark.parametrize("changed", ["config", "source_sha256"])
def test_result_metadata_must_match_previously_recorded_plan(sample, changed):
    root, summary, _ = sample
    path = root / "push-delay0-seed1/result.json"
    result = json.loads(path.read_text())
    if changed == "config":
        result["config"]["rate"] = 0.2
    else:
        result[changed] = "different-source"
    path.write_text(json.dumps(result))
    preserve_existing_summary(root)
    with pytest.raises(ValueError, match="differs from plan"):
        summary.write_summary(root)
    assert_summary_unchanged(root)


def test_raw_byte_count_corruption_still_fails_recomputation(sample):
    root, summary, _ = sample
    path = root / "push-delay0-seed1/traffic.csv"
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    rows[0]["bytes"] = int(rows[0]["bytes"]) + 1
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="raw logs do not match"):
        summary.write_summary(root)


@pytest.mark.parametrize("problem", ["json", "schema", "empty", "duplicate", "entry", "source"])
def test_invalid_manifest_is_rejected(sample, problem):
    root, summary, manifest = sample
    if problem == "schema":
        manifest["schema_version"] = 99
    elif problem == "empty":
        manifest["runs"] = []
    elif problem == "duplicate":
        manifest["runs"].append(manifest["runs"][0])
    elif problem == "entry":
        manifest["runs"][0] = {"directory": "bad"}
    elif problem == "source":
        del manifest["source_sha256"]
    (root / "manifest.json").write_text("{" if problem == "json" else json.dumps(manifest))
    with pytest.raises(ValueError):
        summary.write_summary(root)


def test_legacy_requires_explicit_override_and_marks_completeness_unverified(sample):
    root, summary, _ = sample
    (root / "manifest.json").unlink()
    with pytest.raises(ValueError, match="missing manifest.json"):
        summary.write_summary(root)
    with pytest.warns(UserWarning, match="completeness cannot be verified"):
        summary.write_summary(root, allow_legacy=True)
    assert json.loads((root / "summary.json").read_text())["completeness"] == {
        "status": "legacy_unverified", "expected_runs": None, "observed_runs": 4,
    }


def test_cli_missing_manifest_reports_actionable_error_without_traceback(sample):
    root, _, _ = sample
    (root / "manifest.json").unlink()
    result = subprocess.run(
        [sys.executable, str(EXPERIMENTS / "summarize.py"), str(root)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 2
    assert "missing manifest.json" in result.stderr
    assert "--allow-legacy" in result.stderr
    assert "Traceback" not in result.stderr


def test_audit_separates_timeout_crash_and_unfinished_runs(sample):
    root, summary, _ = sample
    path = root / "pull-delay0-seed1/result.json"
    result = json.loads(path.read_text())
    # A deliberately earlier deadline leaves the final writes outside it.
    result["windows"]["convergence_deadline"] = result["windows"]["start"]

    def read(name, **types):
        with (path.parent / name).open(newline="", encoding="utf-8") as stream:
            return [{k: types.get(k, str)(v) for k, v in row.items()}
                    for row in csv.DictReader(stream)]

    result["metrics"] = summary.summarize(
        read("updates.csv", timestamp=float, version=int),
        read("acceptances.csv", timestamp=float, peer_id=int, version=int),
        read("traffic.csv", timestamp=float, bytes=int),
        peers=result["config"]["peers"],
        **{k: result["windows"][k] for k in ("start", "convergence_deadline", "idle_start", "end")},
    )
    result["status"] = "timeout"
    path.write_text(json.dumps(result))
    crashed = root / "push-delay0-seed1"
    (crashed / "result.json").unlink()
    (crashed / "failure.txt").write_text("RuntimeError: worker exited\n")
    interrupted = root / "pull-delay100-seed1"
    (interrupted / "result.json").unlink()
    (interrupted / "failure.txt").write_text("KeyboardInterrupt\n")

    audit = summary.write_audit(root)
    assert audit["counts"] == {"converged": 1, "timeout": 1, "error": 0, "crash": 1, "unfinished": 1}
    outcomes = {run["directory"]: run for run in audit["runs"]}
    assert outcomes["pull-delay0-seed1"]["metrics"]["final_convergence_seconds"] is None
    assert outcomes["pull-delay0-seed1"]["metrics"]["missing_propagation_samples"] > 0
    assert outcomes["push-delay0-seed1"]["diagnostic"] == "push-delay0-seed1/failure.txt"
    assert not (root / "summary.json").exists()
