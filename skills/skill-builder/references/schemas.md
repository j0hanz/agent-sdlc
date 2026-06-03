# JSON Schemas

Canonical JSON formats for skill-builder.

---

## evals.json

`evals/evals.json`. Defines skill test cases.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "Task",
      "expected_output": "Success criteria",
      "files": ["evals/files/sample.pdf"],
      "expectations": ["Assertion A", "Assertion B"]
    }
  ]
}
```

| Field                  | Notes                     |
| :--------------------- | :------------------------ |
| `skill_name`           | Matches skill frontmatter |
| `evals[].id`           | Unique identifier         |
| `evals[].prompt`       | Execution task            |
| `evals[].expectations` | Verifiable statements     |

---

## grading.json

`<run-dir>/grading.json`. Grader output.

```json
{
  "expectations": [
    {
      "text": "Statement",
      "passed": true,
      "evidence": "Observed in transcript Step X"
    }
  ],
  "summary": { "passed": 1, "failed": 0, "total": 1, "pass_rate": 1.0 },
  "execution_metrics": { "total_tool_calls": 5, "total_steps": 2 },
  "timing": { "total_duration_seconds": 12.5 }
}
```

---

## timing.json

`<run-dir>/timing.json`. Wall clock metrics.
**Note:** Capture `total_tokens` and `duration_ms` immediately on task completion.

```json
{
  "total_tokens": 1000,
  "duration_ms": 5000,
  "total_duration_seconds": 5.0
}
```

---

## benchmark.json

`benchmarks/<timestamp>/benchmark.json`. Aggregated results.

```json
{
  "metadata": { "skill_name": "pdf", "timestamp": "...", "runs_per_configuration": 1 },
  "runs": [
    {
      "eval_id": 1,
      "eval_name": "Test",
      "configuration": "with_skill",
      "run_number": 1,
      "result": { "pass_rate": 1.0, "time_seconds": 5.0, "tokens": 1000 }
    }
  ],
  "run_summary": {
    "with_skill": { "pass_rate": { "mean": 1.0 } },
    "without_skill": { "pass_rate": { "mean": 0.0 } },
    "delta": {
      "primary": "with_skill",
      "baseline": "without_skill",
      "pass_rate": "+1.0",
      "pass_rate_ci": [0.6, 1.0],
      "pass_rate_significant": true,
      "n_primary": 3,
      "n_baseline": 3
    }
  }
}
```

**Mandatory Fields:** `configuration` ("with_skill"|"without_skill"|"old_skill") and `result` structure are required for viewer parsing.

**Delta semantics:** `delta` is always `primary − baseline`, keyed by role (`primary`=version under test, `baseline`=comparison), NOT by directory sort order. `pass_rate_significant` is true only when the Welch 95% CI excludes 0. A non-significant delta — even a large one — is noise at the current run count; raise `--runs-per-query` / runs-per-config before trusting it.
