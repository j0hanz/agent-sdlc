# Traceability Spine

The `Satisfies:` field is the link between spec requirements and plan tasks.

## How it works

Every plan task has a `Satisfies:` field listing one or more spec IDs:

```markdown
### TASK-003: Implement token signing

Depends on: TASK-002
Files: [src/auth/jwt.ts](src/auth/jwt.ts)
Symbols: [signToken](src/auth/jwt.ts#L24)
Satisfies: REQ-001, SEC-001
Action: Implement JWT signing using the configured secret and RS256 algorithm.
Validate: `npm test -- auth/jwt.test.ts`
Expected result: All 6 tests pass, 0 skipped.
```

`cli.py sync` sets `Satisfies:` automatically when generating stubs — never type it by hand.

## The coverage matrix (`cli.py validate --cross`)

`cli.py validate --cross` loads both paired files and checks four things: the three below, plus a warning-only scan for backtick-quoted skill names that don't exist under `skills/` (catches hallucinated handoff/skill references).

| Check                         | Rule                                                                                             | Error type                                                               |
| ----------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| **No uncovered requirements** | Every `REQ/SEC/PERF/COMP` ID from the spec must appear in at least one task's `Satisfies:` field | `[CROSS] Uncovered requirement: REQ-002`                                 |
| **No orphan tasks**           | Every ID in a `Satisfies:` field must exist in the spec                                          | `[CROSS] Orphan task: TASK-007 satisfies 'REQ-999' which is not in spec` |
| **AC coverage**               | Every `AC-###` from the spec should map to at least one task                                     | Warning: `[CROSS] AC-003 has no corresponding task`                      |

## Running the coverage check

```bash
python <skill-dir>/scripts/cli.py validate <name> --cross
```

Output includes a summary table:

```python
Coverage matrix:
  Requirements covered : 5/5
  ACs covered          : 3/3
  Orphan Satisfies IDs : 0
```

## What counts as "covered"

A requirement is covered if any task in the plan has that ID in its `Satisfies:` field. One task can satisfy multiple IDs; one ID can be satisfied by multiple tasks.

`CON-###` (constraints) and `VAL-###` (validation commands) are not checked for coverage — they are spec-internal.

## When spec changes after sync

If requirements are added or renamed after running `cli.py sync`:

1. Edit the spec.
2. Re-run `python cli.py sync <name>.specs.md` — it will add stubs for new IDs only; existing tasks are untouched.
3. Re-run `cli.py validate --cross` to confirm coverage is clean.

Never manually edit the `Satisfies:` field of an existing task. Always let `cli.py sync` manage it.

## Why this matters

The spine turns "the plan should implement the requirements" from prose advice into a machine-checkable contract. A plan that passes `--cross` with zero errors provably covers every stated requirement.
