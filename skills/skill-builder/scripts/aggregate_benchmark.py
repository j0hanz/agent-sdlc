#!/usr/bin/env python3
"""
Aggregate individual run results into benchmark summary statistics.

Reads grading.json files from run directories and produces:
- run_summary with mean, stddev, min, max for each metric
- delta between with_skill and without_skill configurations
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.json_utils import load_json


def calculate_stats(values: list[float]) -> dict[str, float]:
    """Calculate mean, stddev, min, max for a list of values."""
    if not values:
        return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}

    n = len(values)
    mean = sum(values) / n

    if n > 1:
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        stddev = math.sqrt(variance)
    else:
        stddev = 0.0

    return {
        "mean": round(mean, 4),
        "stddev": round(stddev, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }


# Config names ranked by role. The "primary" is the version under test (the new
# skill); the "baseline" is whatever it is measured against. Delta is always
# primary - baseline, so a genuine improvement reads positive regardless of how
# the config directories happen to sort alphabetically.
_PRIMARY_PREF = ("with_skill",)
_BASELINE_PREF = ("without_skill", "old_skill", "baseline")

# Two-sided t critical values at 95% confidence, keyed by integer df.
_T_TABLE_95 = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    11: 2.201,
    12: 2.179,
    13: 2.160,
    14: 2.145,
    15: 2.131,
    16: 2.120,
    17: 2.110,
    18: 2.101,
    19: 2.093,
    20: 2.086,
    21: 2.080,
    22: 2.074,
    23: 2.069,
    24: 2.064,
    25: 2.060,
    26: 2.056,
    27: 2.052,
    28: 2.048,
    29: 2.045,
    30: 2.042,
}


def select_primary_baseline(
    configs: list[str],
) -> tuple[str | None, str | None]:
    """Pick the (primary, baseline) config by semantic role, not sort order.

    Without this, delta was computed as configs[0] - configs[1] in alphabetical
    order, which silently inverted the sign in improve mode (old_skill sorts
    before with_skill, so an improvement read as negative).
    """
    if not configs:
        return None, None
    primary = next((c for c in _PRIMARY_PREF if c in configs), configs[0])
    baseline = next((c for c in _BASELINE_PREF if c in configs and c != primary), None)
    if baseline is None:
        baseline = next((c for c in configs if c != primary), None)
    return primary, baseline


def _t_critical_95(df: float) -> float:
    """Two-sided 95% t critical value for df, conservative when df is unlisted."""
    di = int(math.floor(df))
    if di >= 31:
        return 1.96
    if di in _T_TABLE_95:
        return _T_TABLE_95[di]
    lower = [k for k in _T_TABLE_95 if k <= di]
    return _T_TABLE_95[max(lower)] if lower else _T_TABLE_95[1]


def welch_ci(a: list[float], b: list[float]) -> dict[str, Any] | None:
    """Welch 95% CI for mean(a) - mean(b). None when n < 2 in either group.

    Significance = the CI excludes 0. Uses Welch's unequal-variance t with a
    Satterthwaite df and stdlib only (no scipy). Designed for the small-n
    regime (3-5 runs) where a raw delta carries no information about whether it
    is real or noise.
    """
    n_a, n_b = len(a), len(b)
    if n_a < 2 or n_b < 2:
        return None

    mean_a, mean_b = sum(a) / n_a, sum(b) / n_b
    delta = mean_a - mean_b
    var_a = sum((x - mean_a) ** 2 for x in a) / (n_a - 1)
    var_b = sum((x - mean_b) ** 2 for x in b) / (n_b - 1)
    se = math.sqrt(var_a / n_a + var_b / n_b)

    if se == 0:
        return {
            "delta": delta,
            "ci_low": delta,
            "ci_high": delta,
            "significant": delta != 0,
            "n_a": n_a,
            "n_b": n_b,
        }

    df = (var_a / n_a + var_b / n_b) ** 2 / (
        (var_a / n_a) ** 2 / (n_a - 1) + (var_b / n_b) ** 2 / (n_b - 1)
    )
    margin = _t_critical_95(df) * se
    lo, hi = delta - margin, delta + margin
    return {
        "delta": delta,
        "ci_low": lo,
        "ci_high": hi,
        "significant": lo > 0 or hi < 0,
        "n_a": n_a,
        "n_b": n_b,
    }


def load_run_results(benchmark_dir: Path) -> dict[str, list[dict[str, Any]]]:
    """
    Load all run results from a benchmark directory.

    Returns dict keyed by config name (e.g. "with_skill"/"without_skill"),
    each containing a list of run results.
    """
    runs_dir = benchmark_dir / "runs"
    if runs_dir.exists():
        search_dir = runs_dir
    elif list(benchmark_dir.glob("eval-*")):
        search_dir = benchmark_dir
    else:
        print(
            f"No eval directories found in {benchmark_dir} or {benchmark_dir / 'runs'}"
        )
        return {}

    results: dict[str, list[dict[str, Any]]] = {}

    for eval_idx, eval_dir in enumerate(sorted(search_dir.glob("eval-*"))):
        metadata_path = eval_dir / "eval_metadata.json"
        eval_id: str | int
        if metadata_path.exists():
            try:
                eval_id = load_json(metadata_path).get("eval_id", eval_idx)
            except (json.JSONDecodeError, OSError):
                eval_id = eval_idx
        else:
            try:
                eval_id = int(eval_dir.name.split("-")[1])
            except (IndexError, ValueError):
                eval_id = eval_idx

        # Discover config directories dynamically
        for config_dir in sorted(eval_dir.iterdir()):
            if not config_dir.is_dir():
                continue
            if not list(config_dir.glob("run-*")):
                continue

            config = config_dir.name
            if config not in results:
                results[config] = []

            for run_dir in sorted(config_dir.glob("run-*")):
                try:
                    run_number = int(run_dir.name.split("-")[1])
                except (IndexError, ValueError):
                    run_number = 0
                grading_file = run_dir / "grading.json"

                if not grading_file.exists():
                    print(f"Warning: grading.json not found in {run_dir}")
                    continue

                try:
                    grading = load_json(grading_file)
                except Exception as e:
                    print(f"Warning: Invalid JSON in {grading_file}: {e}")
                    continue

                # Extract metrics
                result: dict[str, Any] = {
                    "eval_id": eval_id,
                    "run_number": run_number,
                    "pass_rate": grading.get("summary", {}).get("pass_rate", 0.0),
                    "passed": grading.get("summary", {}).get("passed", 0),
                    "failed": grading.get("summary", {}).get("failed", 0),
                    "total": grading.get("summary", {}).get("total", 0),
                }

                # Extract timing
                timing = grading.get("timing", {})
                result["time_seconds"] = timing.get("total_duration_seconds", 0.0)

                # Token count comes only from authoritative token sources. Never
                # coerce output_chars into tokens — they are different units, and
                # mixing them across configs produces a meaningless delta. When no
                # token data exists the value stays None and is excluded from
                # aggregate token stats rather than fabricated as 0.
                tokens = timing.get("total_tokens")

                timing_file = run_dir / "timing.json"
                if timing_file.exists():
                    try:
                        timing_data = load_json(timing_file)
                        if result["time_seconds"] == 0.0:
                            result["time_seconds"] = timing_data.get(
                                "total_duration_seconds", 0.0
                            )
                        if tokens is None:
                            tokens = timing_data.get("total_tokens")
                    except Exception:
                        pass

                result["tokens"] = tokens  # None when genuinely unknown

                # Extract metrics
                metrics = grading.get("execution_metrics", {})
                result["tool_calls"] = metrics.get("total_tool_calls", 0)
                result["output_chars"] = metrics.get("output_chars", 0)
                result["errors"] = metrics.get("errors_encountered", 0)

                # Extract expectations
                result["expectations"] = grading.get("expectations", [])

                # Extract notes
                notes_summary = grading.get("user_notes_summary", {})
                notes = []
                notes.extend(notes_summary.get("uncertainties", []))
                notes.extend(notes_summary.get("needs_review", []))
                notes.extend(notes_summary.get("workarounds", []))
                result["notes"] = notes

                results[config].append(result)

    return results


def aggregate_results(results: dict[str, list[dict[str, Any]]]) -> dict[str, dict]:
    """
    Aggregate run results into summary statistics.
    """
    run_summary: dict[str, dict] = {}
    configs = list(results.keys())

    for config in configs:
        runs = results[config]

        if not runs:
            run_summary[config] = {
                "pass_rate": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
                "time_seconds": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
                "tokens": {"mean": 0, "stddev": 0, "min": 0, "max": 0},
            }
            continue

        pass_rates = [float(r["pass_rate"]) for r in runs]
        times = [float(r["time_seconds"]) for r in runs]
        # Exclude runs with no token data instead of counting them as 0.
        tokens = [float(r["tokens"]) for r in runs if r.get("tokens") is not None]

        run_summary[config] = {
            "pass_rate": calculate_stats(pass_rates),
            "time_seconds": calculate_stats(times),
            "tokens": calculate_stats(tokens),
        }

    primary, baseline = select_primary_baseline(configs)

    if primary and baseline and primary != baseline:
        p = run_summary[primary]
        b = run_summary[baseline]
        delta_pass_rate = p["pass_rate"]["mean"] - b["pass_rate"]["mean"]
        delta_time = p["time_seconds"]["mean"] - b["time_seconds"]["mean"]
        delta_tokens = p["tokens"]["mean"] - b["tokens"]["mean"]

        sig = welch_ci(
            [float(r["pass_rate"]) for r in results[primary]],
            [float(r["pass_rate"]) for r in results[baseline]],
        )

        run_summary["delta"] = {
            "primary": primary,
            "baseline": baseline,
            "pass_rate": f"{delta_pass_rate:+.2f}",
            "time_seconds": f"{delta_time:+.1f}",
            "tokens": f"{delta_tokens:+.0f}",
            "pass_rate_ci": (
                [round(sig["ci_low"], 4), round(sig["ci_high"], 4)] if sig else None
            ),
            "pass_rate_significant": bool(sig and sig["significant"]),
            "n_primary": sig["n_a"] if sig else len(results.get(primary, [])),
            "n_baseline": sig["n_b"] if sig else len(results.get(baseline, [])),
        }
    else:
        run_summary["delta"] = {
            "pass_rate": "+0.00",
            "time_seconds": "+0.0",
            "tokens": "+0",
            "pass_rate_ci": None,
            "pass_rate_significant": False,
        }

    return run_summary


def generate_benchmark(
    benchmark_dir: Path, skill_name: str = "", skill_path: str = ""
) -> dict:
    """
    Generate complete benchmark.json from run results.
    """
    results = load_run_results(benchmark_dir)
    run_summary = aggregate_results(results)

    runs = []
    for config, config_results in results.items():
        for result in config_results:
            runs.append(
                {
                    "eval_id": result["eval_id"],
                    "configuration": config,
                    "run_number": result["run_number"],
                    "result": {
                        "pass_rate": result["pass_rate"],
                        "passed": result["passed"],
                        "failed": result["failed"],
                        "total": result["total"],
                        "time_seconds": result["time_seconds"],
                        "tokens": result.get("tokens") or 0,
                        "tool_calls": result.get("tool_calls", 0),
                        "errors": result.get("errors", 0),
                    },
                    "expectations": result["expectations"],
                    "notes": result["notes"],
                }
            )

    eval_ids = sorted(
        set(r["eval_id"] for config_runs in results.values() for r in config_runs)
    )

    return {
        "metadata": {
            "skill_name": skill_name or "<skill-name>",
            "skill_path": skill_path or "<path/to/skill>",
            "executor_model": "<model-name>",
            "analyzer_model": "<model-name>",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "evals_run": eval_ids,
            "runs_per_configuration": 3,
        },
        "runs": runs,
        "run_summary": run_summary,
        "notes": [],
    }


def generate_markdown(benchmark: dict) -> str:
    """Generate human-readable benchmark.md from benchmark data."""
    metadata = benchmark["metadata"]
    run_summary = benchmark["run_summary"]

    configs = [k for k in run_summary if k != "delta"]
    config_a = configs[0] if len(configs) >= 1 else "config_a"
    config_b = configs[1] if len(configs) >= 2 else "config_b"
    label_a = config_a.replace("_", " ").title()
    label_b = config_b.replace("_", " ").title()

    lines = [
        f"# Skill Benchmark: {metadata['skill_name']}",
        "",
        f"**Model**: {metadata['executor_model']}",
        f"**Date**: {metadata['timestamp']}",
        f"**Evals**: {', '.join(map(str, metadata['evals_run']))} ({metadata['runs_per_configuration']} runs each per configuration)",
        "",
        "## Summary",
        "",
        f"| Metric | {label_a} | {label_b} | Delta |",
        "|--------|------------|---------------|-------|",
    ]

    a_summary = run_summary.get(config_a, {})
    b_summary = run_summary.get(config_b, {})
    delta = run_summary.get("delta", {})

    a_pr = a_summary.get("pass_rate", {})
    b_pr = b_summary.get("pass_rate", {})
    lines.append(
        f"| Pass Rate | {a_pr.get('mean', 0) * 100:.0f}% ± {a_pr.get('stddev', 0) * 100:.0f}% | {b_pr.get('mean', 0) * 100:.0f}% ± {b_pr.get('stddev', 0) * 100:.0f}% | {delta.get('pass_rate', '—')} |"
    )

    a_time = a_summary.get("time_seconds", {})
    b_time = b_summary.get("time_seconds", {})
    lines.append(
        f"| Time | {a_time.get('mean', 0):.1f}s ± {a_time.get('stddev', 0):.1f}s | {b_time.get('mean', 0):.1f}s ± {b_time.get('stddev', 0):.1f}s | {delta.get('time_seconds', '—')}s |"
    )

    a_tokens = a_summary.get("tokens", {})
    b_tokens = b_summary.get("tokens", {})
    lines.append(
        f"| Tokens | {a_tokens.get('mean', 0):.0f} ± {a_tokens.get('stddev', 0):.0f} | {b_tokens.get('mean', 0):.0f} ± {b_tokens.get('stddev', 0):.0f} | {delta.get('tokens', '—')} |"
    )

    ci = delta.get("pass_rate_ci")
    if ci is not None:
        verdict = (
            "**significant** (95% CI excludes 0)"
            if delta.get("pass_rate_significant")
            else "NOT significant (95% CI includes 0)"
        )
        lines.extend(
            [
                "",
                f"**Pass-rate delta {delta.get('pass_rate', '')}** — {verdict}; "
                f"95% CI [{ci[0]:+.2f}, {ci[1]:+.2f}] over "
                f"n={delta.get('n_primary', '?')} vs {delta.get('n_baseline', '?')} runs.",
            ]
        )

    if benchmark.get("notes"):
        lines.extend(["", "## Notes", ""])
        for note in benchmark["notes"]:
            lines.append(f"- {note}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate benchmark run results into summary statistics"
    )
    parser.add_argument(
        "benchmark_dir", type=Path, help="Path to the benchmark directory"
    )
    parser.add_argument(
        "--skill-name", default="", help="Name of the skill being benchmarked"
    )
    parser.add_argument(
        "--skill-path", default="", help="Path to the skill being benchmarked"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output path for benchmark.json",
    )

    args = parser.parse_args()

    if not args.benchmark_dir.exists():
        print(f"Directory not found: {args.benchmark_dir}")
        sys.exit(1)

    benchmark = generate_benchmark(args.benchmark_dir, args.skill_name, args.skill_path)

    output_json = args.output or (args.benchmark_dir / "benchmark.json")
    output_md = output_json.with_suffix(".md")

    output_json.write_text(json.dumps(benchmark, indent=2), encoding="utf-8")
    print(f"Generated: {output_json}")

    markdown = generate_markdown(benchmark)
    output_md.write_text(markdown, encoding="utf-8")
    print(f"Generated: {output_md}")

    run_summary = benchmark["run_summary"]
    configs = [k for k in run_summary if k != "delta"]
    delta = run_summary.get("delta", {})

    print("\nSummary:")
    for config in configs:
        pr = run_summary[config]["pass_rate"]["mean"]
        label = config.replace("_", " ").title()
        print(f"  {label}: {pr * 100:.1f}% pass rate")
    print(f"  Delta:         {delta.get('pass_rate', '—')}")
    ci = delta.get("pass_rate_ci")
    if ci is not None:
        verdict = (
            "significant" if delta.get("pass_rate_significant") else "not significant"
        )
        print(f"  95% CI:        [{ci[0]:+.2f}, {ci[1]:+.2f}] ({verdict})")


if __name__ == "__main__":
    main()
