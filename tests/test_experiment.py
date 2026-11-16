import csv
from dataclasses import replace
import json
import multiprocessing as mp
from pathlib import Path
import subprocess
import sys

import pytest

from pushpull.experiment import Config, make_workload, run_experiment
from pushpull.metrics import summarize


def test_workload_is_replayable_and_assigns_a_single_writer():
    config = Config(mode="push", duration=10, rate=5, seed=17)
    workload = make_workload(config)
    assert workload == make_workload(replace(config, mode="pull", delay_ms=100, pull_interval=2))
    assert workload != make_workload(replace(config, seed=18))
    assert len(workload) == 50
    assert all(u["writer"] == int(u["key"].split("-")[1]) % config.peers for u in workload)
    assert all(u["scheduled_offset"] < config.duration for u in workload)
    assert make_workload(replace(config, rate=0)) == []


@pytest.mark.parametrize("settings", [
    {"mode": "other"}, {"peers": 2}, {"rate": -1}, {"delay_ms": float("nan")},
    {"duration": 0}, {"idle": 0}, {"pull_interval": 0}, {"keys": 0},
])
def test_rejects_invalid_configuration(settings):
    with pytest.raises(ValueError):
        Config(**{"mode": "push", **settings})


@pytest.mark.parametrize("mode", ["push", "pull"])
@pytest.mark.parametrize("delay_ms", [0, 100])
def test_spawned_ring_persists_recomputable_results(tmp_path, mode, delay_ms):
    config = Config(mode=mode, peers=4, rate=5, duration=0.4, settle=1.2,
                    idle=0.25, pull_interval=0.05, delay_ms=delay_ms, seed=11)
    output = tmp_path / "run"
    before = {p.pid for p in mp.active_children()}
    result = run_experiment(config, output)
    assert result["status"] == "converged", result["errors"]
    assert result["final_state_matches"]
    assert result["metrics"]["missing_propagation_samples"] == 0
    assert result["metrics"]["expected_propagation_samples"] == 8
    assert len(set(result["process_ids"])) == 4
    assert all(pid != mp.current_process().pid for pid in result["process_ids"])
    assert {p.pid for p in mp.active_children()} == before
    assert json.loads((output / "result.json").read_text()) == result

    def read(name):
        with (output / name).open(newline="") as stream:
            return list(csv.DictReader(stream))

    updates, acceptances, traffic = read("updates.csv"), read("acceptances.csv"), read("traffic.csv")
    for row in updates:
        row["version"] = int(row["version"])
        row["timestamp"] = float(row["timestamp"])
    for row in acceptances:
        for key in ("peer_id", "version"):
            row[key] = int(row[key])
        row["timestamp"] = float(row["timestamp"])
    for row in traffic:
        row["bytes"] = int(row["bytes"])
        row["timestamp"] = float(row["timestamp"])
    windows = result["windows"]
    recomputed = summarize(updates, acceptances, traffic, peers=config.peers,
                           **{k: windows[k] for k in ("start", "convergence_deadline", "idle_start", "end")})
    assert recomputed == result["metrics"]
    assert result["metrics"]["idle_messages"] == 0 if mode == "push" else result["metrics"]["idle_messages"] > 0
    with pytest.raises(FileExistsError):
        run_experiment(config, output)


def test_convergence_deadline_is_reported_as_timeout(tmp_path):
    result = run_experiment(
        Config(mode="pull", peers=4, duration=0.1, settle=0, idle=0.1, delay_ms=100),
        tmp_path / "timeout",
    )
    assert result["status"] == "timeout"
    assert not result["metrics"]["converged"]
    assert result["metrics"]["final_convergence_seconds"] is None
    assert result["metrics"]["missing_propagation_samples"] > 0


def test_controller_failure_joins_all_workers(tmp_path, monkeypatch):
    import pushpull.experiment as experiment
    before = {p.pid for p in mp.active_children()}

    def fail(*args, **kwargs):
        raise RuntimeError("injected controller failure")

    monkeypatch.setattr(experiment, "_collect", fail)
    with pytest.raises(RuntimeError, match="injected controller failure"):
        run_experiment(Config(mode="push", peers=3), tmp_path / "failure")
    assert {p.pid for p in mp.active_children()} == before
    assert "injected controller failure" in (tmp_path / "failure/failure.txt").read_text()


def test_documented_cli_runs_from_a_fresh_checkout(tmp_path):
    script = Path(__file__).resolve().parents[1] / "experiments/run.py"
    result = subprocess.run(
        [sys.executable, str(script), "--mode", "push", "--peers", "3", "--rate", "0",
         "--duration", "0.1", "--settle", "0", "--idle", "0.1", "--output", str(tmp_path / "cli")],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert "converged:" in result.stdout
