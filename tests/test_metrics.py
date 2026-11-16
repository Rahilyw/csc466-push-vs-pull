import pytest

from pushpull.metrics import summarize


def calculate(updates=(), acceptances=(), traffic=()):
    return summarize(list(updates), list(acceptances), list(traffic), peers=2,
                     start=0, convergence_deadline=6, idle_start=7, end=10)


def event(peer, version, timestamp, key="k"):
    return {"peer_id": peer, "key": key, "version": version, "timestamp": timestamp}


def test_newer_acceptance_satisfies_skipped_versions_and_windowed_traffic():
    updates = [{"key": "k", "version": 1, "timestamp": 1},
               {"key": "k", "version": 2, "timestamp": 2}]
    accepts = [event(0, 1, 1), event(0, 2, 2), event(1, 2, 3)]
    traffic = [{"timestamp": t, "message_type": "push", "bytes": 20}
               for t in (-1, 1, 7, 9, 10)]
    result = calculate(updates, accepts, traffic)
    assert result["converged"]
    assert result["missing_propagation_samples"] == 0
    assert result["propagation_samples"] == 4
    assert result["propagation_median_seconds"] == 0.5
    assert result["propagation_p95_seconds"] == pytest.approx(1.85)
    assert result["final_convergence_seconds"] == 1
    assert result["messages"] == 3
    assert result["bytes"] == 60
    assert result["idle_messages_per_second"] == pytest.approx(2 / 3)
    assert result["idle_bytes_per_second"] == pytest.approx(40 / 3)


def test_late_or_missing_acceptance_is_a_timeout_not_zero_delay():
    result = calculate([{"key": "k", "version": 2, "timestamp": 2}],
                       [event(0, 2, 2), event(1, 1, 3), event(1, 2, 8)])
    assert not result["converged"]
    assert result["final_convergence_seconds"] is None
    assert result["propagation_samples"] == 1
    assert result["missing_propagation_samples"] == 1


def test_versions_of_different_keys_cannot_satisfy_each_other():
    result = calculate([{"key": "k", "version": 1, "timestamp": 1}],
                       [event(0, 1, 1), event(1, 99, 2, key="other")])
    assert not result["converged"]
    assert result["missing_propagation_samples"] == 1


def test_empty_workload_has_no_propagation_samples():
    result = calculate()
    assert result["converged"]
    assert result["propagation_median_seconds"] is None
    assert result["propagation_p95_seconds"] is None
    assert result["final_convergence_seconds"] == 0
    assert result["messages"] == 0


def paired_results():
    from copy import deepcopy
    metrics = calculate([{"key": "k", "version": 1, "timestamp": 1}],
                        [event(0, 1, 1), event(1, 1, 2)])
    return [{
        "status": "converged", "source_sha256": "source", "workload_sha256": f"seed-{seed}",
        "config": {"mode": mode, "delay_ms": delay, "seed": seed, "duration": 10},
        "metrics": deepcopy(metrics),
    } for mode in ("push", "pull") for delay in (0, 100) for seed in (1, 2)]


def test_aggregation_preserves_per_run_quantile_meaning():
    from pushpull.metrics import aggregate_results
    rows = aggregate_results(paired_results())
    assert len(rows) == 4
    for row in rows:
        assert row["runs"] == 2
        assert row["mean_run_median_ms"] == 500
        assert row["std_run_median_ms"] == 0
        assert row["mean_run_p95_ms"] == 950
        assert row["mean_convergence_ms"] == 1000


@pytest.mark.parametrize("problem", ["timeout", "missing", "source", "workload", "parameters", "duplicate", "unpaired"])
def test_aggregation_refuses_invalid_comparisons(problem):
    from pushpull.metrics import aggregate_results
    results = paired_results()
    if problem == "timeout":
        results[0]["status"] = "timeout"
    elif problem == "missing":
        results[0]["metrics"]["missing_propagation_samples"] = 1
    elif problem == "source":
        results[0]["source_sha256"] = "different"
    elif problem == "workload":
        results[0]["workload_sha256"] = "different"
    elif problem == "parameters":
        results[0]["config"]["duration"] = 20
    elif problem == "duplicate":
        results.append(results[0])
    else:
        results.pop()
    with pytest.raises(ValueError):
        aggregate_results(results)
