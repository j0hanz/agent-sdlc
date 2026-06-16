# Code Quality Reviewer Prompt Template

Use this template when dispatching the `detective` subagent in Phase 3.
Only run Phase 3 after SPEC_PASS from Phase 2.

---

## Dispatch Template

```
SCOPE:
  Files changed: [list from implementer's FILES_CHANGED]
  Baseline commit: [git hash from BEFORE implementer ran]
  Implementation commit: [implementer's COMMIT hash]

OBJECTIVE:
  Assess whether the implementation is clean, testable, and maintainable.
  This is NOT a spec check — assume spec compliance is already verified.

CONTEXT:
  Task summary (what was built):
  [Paste implementer's SUMMARY verbatim]

  Project conventions:
  [Paste relevant conventions from AGENTS.md — naming, error handling, test patterns]

CONSTRAINTS:
  - Evaluate ONLY the code introduced by this task (delta from baseline to implementation commit).
  - DO NOT re-check spec compliance — that was Phase 2's job.
  - DO NOT suggest features or scope expansions.
  - Flag files whose size grew by more than 150 lines due to this task alone.

CHECKS:
  1. Responsibility: Does each file/class/function have one clear job?
  2. Testability: Are new units decomposed so they can be understood and tested independently?
  3. Test coverage: Do tests exercise the implementation beyond the happy path?
  4. Error handling: Are all error paths handled, propagated, or explicitly documented as out-of-scope?
  5. File growth: Did any file grow excessively? (Flag if >150 lines added to a single file)
  6. Interface clarity: Are public APIs clearly named and typed?

OUTPUT:
  Return a single final message with this exact structure:

  VERDICT: [QUALITY_PASS | CRITICAL | IMPORTANT | MINOR]

  STRENGTHS:
  [bullet list of what is well-implemented — be specific with file:line references]

  CRITICAL_ISSUES:
  [file:line — description of the issue and why it blocks]
  [or: none]

  IMPORTANT_ISSUES:
  [file:line — description and recommended fix]
  [or: none]

  MINOR_ISSUES:
  [file:line — advisory note; fix in a later refactor pass]
  [or: none]

  SUMMARY:
  [2-3 sentences: overall quality verdict with specific evidence]
```

---

## Verdict Severity Rules

| Verdict        | Definition                                                                                               | Action                               |
| :------------- | :------------------------------------------------------------------------------------------------------- | :----------------------------------- |
| `QUALITY_PASS` | No CRITICAL or IMPORTANT issues                                                                          | Advance to next task                 |
| `CRITICAL`     | Silent failure, broken abstraction, untested error path that could cause data loss or incorrect behavior | Fix before advancing; re-run Phase 3 |
| `IMPORTANT`    | Responsibility violation, tight coupling, test gap that will cause pain soon                             | Fix before advancing                 |
| `MINOR`        | Style inconsistency, minor naming issue, advisory improvement                                            | Log; fix later                       |

## Guidance for the Dispatcher

- **Supply project conventions** from AGENTS.md — the reviewer cannot infer them from code alone.
- **CRITICAL/IMPORTANT triggers a fix loop:** Dispatch a new coder subagent with the issues listed verbatim. Then re-run Phase 3.
- **MINOR issues do NOT block** — log them and proceed to the next task.
- **Max 2 quality-fix iterations** before surfacing to the user.
- **After QUALITY_PASS:** Mark the task complete in your tracking list, then move to the next task.
