"""Pilot CLI checks: matched configurations and a real spawned-process smoke run."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from pushpull.experiment import make_workload


SCRIPT = Path(__file__).resolve().parents[1] / "experiments/pilot.py"


@pytest.fixture
def pilot(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPT.parent))
    spec = importlib.util.spec_from_file_location("pilot_cli", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_defaults_keep_twenty_matched_runs(pilot, tmp_path, monkeypatch):
    seen = []
    summaries = []

    def record(config, output):
        # The complete plan must exist before even the first worker is launched.
        manifest = json.loads((output.parent / "manifest.json").read_text())
        assert len(manifest["runs"]) == 20
        assert manifest["provenance"] == "before_run"
        seen.append((config, output))
        return {"status": "converged", "metrics": {"messages": 0}}

    monkeypatch.setattr(pilot, "run_experiment", record)
    monkeypatch.setattr(pilot, "write_summary", summaries.append)
    output = tmp_path / "default"
    pilot.main(["--output", str(output)])
    assert len(seen) == 20
    assert summaries == [output]
    assert {config.peers for config, _ in seen} == {8}
    assert {config.rate for config, _ in seen} == {1}
    assert {config.pull_interval for config, _ in seen} == {0.5}
    assert {config.keys for config, _ in seen} == {16}
    for seed in range(1, 6):
        group = [(config, path) for config, path in seen if config.seed == seed]
        assert {(c.mode, c.delay_ms) for c, _ in group} == {
            ("push", 0), ("pull", 0), ("push", 100), ("pull", 100)
        }
        assert all(make_workload(c) == make_workload(group[0][0]) for c, _ in group)
        assert group[0][0].mode == ("push" if seed % 2 == 0 else "pull")
        assert all(".0-" not in path.name for _, path in group)


@pytest.mark.parametrize("options", [
    ["--seeds", "1", "1"],
    ["--delay-ms", "0", "0.0"],
    ["--delay-ms", "0", "-1"],
    ["--delay-ms", "nan"],
    ["--peers", "2"],
    ["--rate", "-0.2"],
    ["--pull-interval", "0"],
    ["--keys", "0"],
    ["--duration", "0"],
])
def test_invalid_settings_have_no_output_or_workers(pilot, tmp_path, monkeypatch, options):
    def unexpected(*args):
        pytest.fail("invalid CLI settings must not launch experiments")

    monkeypatch.setattr(pilot, "run_experiment", unexpected)
    output = tmp_path / "invalid"
    with pytest.raises(SystemExit) as error:
        pilot.main(["--output", str(output), *options])
    assert error.value.code == 2
    assert not output.exists()


def test_custom_pilot_cli_runs_real_paired_processes(tmp_path):
    output = tmp_path / "custom"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(output), "--seeds", "4",
         "--peers", "3", "--rate", "0", "--pull-interval", "2", "--keys", "7",
         "--delay-ms", "0", "--duration", "0.05", "--settle", "0", "--idle", "0.1"],
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    paths = sorted(output.glob("*/result.json"))
    assert len(paths) == 2
    runs = [json.loads(path.read_text()) for path in paths]
    assert {r["config"]["mode"] for r in runs} == {"push", "pull"}
    assert len({r["workload_sha256"] for r in runs}) == 1
    for run in runs:
        assert run["status"] == "converged"
        assert len(set(run["process_ids"])) == 3
        assert {key: run["config"][key] for key in ("peers", "rate", "pull_interval", "keys")} == {
            "peers": 3, "rate": 0, "pull_interval": 2, "keys": 7,
        }
    summary = json.loads((output / "summary.json").read_text())
    assert len(summary["rows"]) == 2
    assert summary["completeness"] == {
        "status": "complete", "expected_runs": 2, "observed_runs": 2,
        "manifest_provenance": "before_run",
    }


def test_worker_failure_preserves_full_plan(pilot, tmp_path, monkeypatch):
    def fail(*args):
        raise RuntimeError("injected experiment failure")

    monkeypatch.setattr(pilot, "run_experiment", fail)
    output = tmp_path / "interrupted"
    with pytest.raises(RuntimeError, match="injected experiment failure"):
        pilot.main(["--output", str(output)])
    assert len(json.loads((output / "manifest.json").read_text())["runs"]) == 20
    assert not (output / "summary.json").exists()
