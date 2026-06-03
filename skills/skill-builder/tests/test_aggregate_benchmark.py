import json

import pytest
from scripts.aggregate_benchmark import (
    calculate_stats,
    aggregate_results,
    generate_markdown,
    load_run_results,
    select_primary_baseline,
    welch_ci,
)


def test_calculate_stats_empty():
    result = calculate_stats([])
    assert result == {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}


def test_calculate_stats_single():
    result = calculate_stats([0.8])
    assert result["mean"] == pytest.approx(0.8)
    assert result["stddev"] == 0.0
    assert result["min"] == pytest.approx(0.8)
    assert result["max"] == pytest.approx(0.8)


def test_calculate_stats_multiple():
    result = calculate_stats([0.5, 0.75, 1.0])
    assert result["mean"] == pytest.approx(0.75)
    assert result["min"] == pytest.approx(0.5)
    assert result["max"] == pytest.approx(1.0)
    assert result["stddev"] > 0


def test_aggregate_results_empty():
    result = aggregate_results({})
    assert "delta" in result
    delta = result["delta"]
    assert delta["pass_rate"] == "+0.00"
    assert delta["time_seconds"] == "+0.0"
    assert delta["tokens"] == "+0"


def test_aggregate_results_single_config():
    runs = [
        {"pass_rate": 1.0, "time_seconds": 5.0, "tokens": 100},
        {"pass_rate": 0.5, "time_seconds": 3.0, "tokens": 80},
    ]
    result = aggregate_results({"with_skill": runs})
    assert "with_skill" in result
    assert result["with_skill"]["pass_rate"]["mean"] == pytest.approx(0.75)
    assert "delta" in result


def test_aggregate_results_two_configs():
    with_runs = [{"pass_rate": 0.9, "time_seconds": 4.0, "tokens": 90}]
    without_runs = [{"pass_rate": 0.6, "time_seconds": 5.0, "tokens": 100}]
    result = aggregate_results({"with_skill": with_runs, "without_skill": without_runs})
    delta = result["delta"]
    assert delta["pass_rate"] == "+0.30"


# --- select_primary_baseline -------------------------------------------------


def test_select_primary_baseline_new_skill_mode():
    assert select_primary_baseline(["with_skill", "without_skill"]) == (
        "with_skill",
        "without_skill",
    )


def test_select_primary_baseline_improve_mode():
    # old_skill sorts before with_skill; role-based selection must still pick
    # with_skill as primary so the delta is new - old, not old - new.
    assert select_primary_baseline(["old_skill", "with_skill"]) == (
        "with_skill",
        "old_skill",
    )


def test_select_primary_baseline_order_independent():
    assert select_primary_baseline(["without_skill", "with_skill"]) == (
        "with_skill",
        "without_skill",
    )


def test_select_primary_baseline_single():
    assert select_primary_baseline(["with_skill"]) == ("with_skill", None)


def test_select_primary_baseline_empty():
    assert select_primary_baseline([]) == (None, None)


def test_delta_sign_positive_in_improve_mode():
    # New skill (with_skill) clearly beats the old snapshot.
    with_runs = [{"pass_rate": 0.9, "time_seconds": 4.0, "tokens": 90}]
    old_runs = [{"pass_rate": 0.5, "time_seconds": 4.0, "tokens": 90}]
    result = aggregate_results({"old_skill": old_runs, "with_skill": with_runs})
    assert result["delta"]["pass_rate"] == "+0.40"
    assert result["delta"]["primary"] == "with_skill"
    assert result["delta"]["baseline"] == "old_skill"


# --- welch_ci ----------------------------------------------------------------


def test_welch_ci_insufficient_samples():
    assert welch_ci([1.0], [0.0]) is None
    assert welch_ci([1.0, 1.0], [0.0]) is None


def test_welch_ci_separated_is_significant():
    sig = welch_ci([0.9, 0.95, 1.0], [0.5, 0.55, 0.6])
    assert sig is not None
    assert sig["significant"] is True
    assert sig["ci_low"] > 0


def test_welch_ci_overlapping_not_significant():
    sig = welch_ci([0.4, 0.6, 0.8], [0.3, 0.5, 0.7])
    assert sig is not None
    assert sig["significant"] is False
    assert sig["ci_low"] < 0 < sig["ci_high"]


def test_welch_ci_zero_variance_differing_means():
    sig = welch_ci([1.0, 1.0, 1.0], [0.0, 0.0, 0.0])
    assert sig["significant"] is True


def test_aggregate_results_includes_significance():
    with_runs = [
        {"pass_rate": p, "time_seconds": 4.0, "tokens": 90} for p in (0.9, 0.95, 1.0)
    ]
    without_runs = [
        {"pass_rate": p, "time_seconds": 5.0, "tokens": 100} for p in (0.5, 0.55, 0.6)
    ]
    result = aggregate_results({"with_skill": with_runs, "without_skill": without_runs})
    delta = result["delta"]
    assert delta["pass_rate_significant"] is True
    assert delta["pass_rate_ci"] is not None
    assert delta["n_primary"] == 3 and delta["n_baseline"] == 3


# --- token metric ------------------------------------------------------------


def test_output_chars_not_coerced_into_tokens(tmp_path):
    run_dir = tmp_path / "eval-1" / "with_skill" / "run-1"
    run_dir.mkdir(parents=True)
    grading = {
        "summary": {"pass_rate": 1.0, "passed": 1, "failed": 0, "total": 1},
        "timing": {"total_duration_seconds": 2.5},  # no total_tokens anywhere
        "execution_metrics": {"output_chars": 500},
    }
    (run_dir / "grading.json").write_text(json.dumps(grading))

    results = load_run_results(tmp_path)
    # tokens must be None (unknown) — never the 500 char count.
    assert results["with_skill"][0]["tokens"] is None


def test_tokens_read_from_timing_json_with_nonzero_grading_time(tmp_path):
    run_dir = tmp_path / "eval-1" / "with_skill" / "run-1"
    run_dir.mkdir(parents=True)
    grading = {
        "summary": {"pass_rate": 1.0, "passed": 1, "failed": 0, "total": 1},
        "timing": {"total_duration_seconds": 2.5},
        "execution_metrics": {},
    }
    (run_dir / "grading.json").write_text(json.dumps(grading))
    (run_dir / "timing.json").write_text(
        json.dumps({"total_tokens": 1234, "total_duration_seconds": 2.5})
    )

    results = load_run_results(tmp_path)
    assert results["with_skill"][0]["tokens"] == 1234


def test_aggregate_excludes_none_tokens():
    runs = [
        {"pass_rate": 1.0, "time_seconds": 1.0, "tokens": None},
        {"pass_rate": 1.0, "time_seconds": 1.0, "tokens": 100},
    ]
    result = aggregate_results({"with_skill": runs})
    # Only the one real value contributes; None is excluded, not counted as 0.
    assert result["with_skill"]["tokens"]["mean"] == pytest.approx(100)


def _make_grading(pass_rate: float, passed: int, failed: int, total: int) -> dict:
    return {
        "summary": {
            "pass_rate": pass_rate,
            "passed": passed,
            "failed": failed,
            "total": total,
        },
        "timing": {"total_duration_seconds": 2.5},
        "execution_metrics": {
            "total_tool_calls": 4,
            "output_chars": 200,
            "errors_encountered": 0,
        },
        "expectations": [],
        "user_notes_summary": {},
    }


def test_load_run_results_workspace_layout(tmp_path):
    eval_dir = tmp_path / "eval-1"
    for config in ("with_skill", "without_skill"):
        run_dir = eval_dir / config / "run-1"
        run_dir.mkdir(parents=True)
        grading = _make_grading(1.0 if config == "with_skill" else 0.5, 4, 0, 4)
        (run_dir / "grading.json").write_text(json.dumps(grading))

    results = load_run_results(tmp_path)
    assert set(results.keys()) == {"with_skill", "without_skill"}
    assert results["with_skill"][0]["pass_rate"] == 1.0
    assert results["without_skill"][0]["pass_rate"] == 0.5


def test_load_run_results_missing_grading_warns(tmp_path, capsys):
    run_dir = tmp_path / "eval-1" / "with_skill" / "run-1"
    run_dir.mkdir(parents=True)
    # No grading.json written

    load_run_results(tmp_path)
    captured = capsys.readouterr()
    assert "grading.json not found" in captured.out


def test_generate_markdown_has_summary():
    benchmark = {
        "metadata": {
            "skill_name": "test-skill",
            "executor_model": "claude-sonnet-4-6",
            "timestamp": "2026-01-01T00:00:00Z",
            "evals_run": [1, 2],
            "runs_per_configuration": 3,
        },
        "run_summary": {
            "with_skill": {
                "pass_rate": {"mean": 0.9, "stddev": 0.05, "min": 0.8, "max": 1.0},
                "time_seconds": {"mean": 4.0, "stddev": 0.5, "min": 3.0, "max": 5.0},
                "tokens": {"mean": 100, "stddev": 10, "min": 80, "max": 120},
            },
            "without_skill": {
                "pass_rate": {"mean": 0.6, "stddev": 0.1, "min": 0.5, "max": 0.7},
                "time_seconds": {"mean": 5.0, "stddev": 0.5, "min": 4.5, "max": 5.5},
                "tokens": {"mean": 110, "stddev": 10, "min": 100, "max": 120},
            },
            "delta": {"pass_rate": "+0.30", "time_seconds": "-1.0", "tokens": "-10"},
        },
        "notes": [],
    }
    md = generate_markdown(benchmark)
    assert "# Skill Benchmark: test-skill" in md
    assert "## Summary" in md
    assert "Pass Rate" in md


def test_generate_markdown_shows_significance():
    benchmark = {
        "metadata": {
            "skill_name": "test-skill",
            "executor_model": "claude-sonnet-4-6",
            "timestamp": "2026-01-01T00:00:00Z",
            "evals_run": [1],
            "runs_per_configuration": 3,
        },
        "run_summary": {
            "with_skill": {
                "pass_rate": {"mean": 0.95, "stddev": 0.05, "min": 0.9, "max": 1.0},
                "time_seconds": {"mean": 4.0, "stddev": 0.5, "min": 3.0, "max": 5.0},
                "tokens": {"mean": 100, "stddev": 10, "min": 80, "max": 120},
            },
            "without_skill": {
                "pass_rate": {"mean": 0.55, "stddev": 0.05, "min": 0.5, "max": 0.6},
                "time_seconds": {"mean": 5.0, "stddev": 0.5, "min": 4.5, "max": 5.5},
                "tokens": {"mean": 110, "stddev": 10, "min": 100, "max": 120},
            },
            "delta": {
                "pass_rate": "+0.40",
                "time_seconds": "-1.0",
                "tokens": "-10",
                "pass_rate_ci": [0.29, 0.51],
                "pass_rate_significant": True,
                "n_primary": 3,
                "n_baseline": 3,
            },
        },
        "notes": [],
    }
    md = generate_markdown(benchmark)
    assert "significant" in md
    assert "95% CI" in md
