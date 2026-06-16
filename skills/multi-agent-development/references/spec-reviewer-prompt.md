# Spec Compliance Reviewer Prompt Template

Use this template when dispatching the `detective` subagent in Phase 2.
Fill in every `[FIELD]` before dispatching. The reviewer reads actual code — not the implementer's report.

---

## Dispatch Template

```
SCOPE:
  Files changed: [list from implementer's FILES_CHANGED]
  Baseline commit: [git hash from BEFORE implementer ran]
  Implementation commit: [implementer's COMMIT hash]

OBJECTIVE:
  Verify the implementation matches the task specification — nothing more, nothing less.

CONTEXT:
  Task spec (verbatim):
  [Paste the full original task spec here]

  What the implementer claims they built:
  [Paste the implementer's SUMMARY verbatim]

CONSTRAINTS:
  - DO NOT trust the implementer's summary. Verify by reading the actual code.
  - Read every file listed in FILES_CHANGED.
  - Compare the actual implementation to the spec line by line.
  - DO NOT evaluate code quality, style, or test coverage — that is Phase 3's job.
  - Focus only on: did they build what was asked?

OUTPUT:
  Return a single final message with this exact structure:

  VERDICT: [SPEC_PASS | SPEC_FAIL]

  MISSING_REQUIREMENTS:
  [list anything the spec required that was NOT implemented — with file:line references]
  [or: none]

  EXTRA_WORK:
  [list anything implemented that was NOT in the spec — with file:line references]
  [or: none]

  MISINTERPRETATIONS:
  [list cases where the implementation solves a different problem than specified]
  [or: none]

  SUMMARY:
  [2-3 sentences: overall compliance verdict with evidence from code, not from report]
```

---

## Guidance for the Dispatcher

- **Run this immediately** after a `DONE` or `DONE_WITH_CONCERNS` from the implementer.
- **Provide the spec verbatim** — do not paraphrase or summarize. The reviewer compares code to exact requirements.
- **Supply both commit hashes** so the reviewer can diff and see only what changed.
- **SPEC_FAIL triggers a fix loop:** Dispatch a new coder subagent with the MISSING_REQUIREMENTS and EXTRA_WORK listed verbatim. Then re-run Phase 2.
- **Max 2 fix iterations** before surfacing to the user — persistent spec failure signals an ambiguous or conflicting spec.
