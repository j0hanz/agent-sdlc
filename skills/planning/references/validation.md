# Validation Guide

Run `cli.py validate` after authoring each artifact and after every `cli.py sync` run.

```bash
python <skill-dir>/scripts/cli.py validate <name>              # all three checks
python <skill-dir>/scripts/cli.py validate <name> --spec       # spec only
python <skill-dir>/scripts/cli.py validate <name> --plan       # plan only
python <skill-dir>/scripts/cli.py validate <name> --cross      # coverage matrix only
```

`<name>` can be a bare stem (`auth-jwt`) or a full path to either artifact.

## What each mode checks

### `--spec`

- All mandatory sections present for the chosen depth (sketch/contract/blueprint)
- Requirements are atomic (no "and" joining two obligations)
- Requirements use active voice
- No vague adjectives (fast, robust, lightweight…) without numeric threshold
- REQs have corresponding ACs; ACs have corresponding VALs

### `--plan`

- Every task has all six mandatory fields: `Depends on`, `Files`, `Symbols`, `Action`, `Validate`, `Expected result`
- `Files` and `Symbols` are markdown links `[name](path#L42)`, not bare paths
- `Validate` field contains a backtick-wrapped command
- Warning when `Satisfies:` is missing (traceability spine not set)

### `--cross`

See [traceability.md](traceability.md) for full details. In brief:

- Every `REQ/SEC/PERF/COMP` ID covered by ≥1 task
- Every `Satisfies:` ID exists in the spec
- Every `AC-###` mapped to a task (warning if not)
- Every backtick-quoted skill-name-shaped token resolves to a real `skills/` directory (warning if not — catches hallucinated/cross-plugin skill references)

## Exit codes

- `0` — all selected checks pass
- `1` — at least one ERROR found (warnings do not affect exit code)

## Fixing common errors

| Error                                                  | Fix                                                                                         |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| `Missing mandatory section: Interfaces`                | Add the section; include at least one introductory sentence before sub-headings             |
| `REQ-002 missing fields: Action`                       | Fill the empty field in the task block                                                      |
| `bare path — use markdown links`                       | Replace `src/auth.ts` with `[src/auth.ts](src/auth.ts)`                                     |
| `Uncovered requirement: REQ-003`                       | Re-run `cli.py sync` to add the missing stub, then author it                                |
| `Orphan task satisfies 'REQ-999'`                      | The ID doesn't exist in the spec — fix the typo or remove the Satisfies entry               |
| `Backtick token 'xyz' looks like a skill reference...` | Verify the skill name is real (check `skills/` directory); fix typo or remove the reference |

## UNVERIFIED markers

`cli.py sync` emits `[UNVERIFIED](UNVERIFIED)` in task `Files:` fields. Before the plan is ready for execution, replace each `UNVERIFIED` with a real path from Grep/Glob output, or document why the path is not yet resolvable (e.g., "new file created by TASK-001").

## Quality gate checklist

Before marking a plan ready for execution:

- [ ] `cli.py validate --spec` — 0 errors
- [ ] `cli.py validate --plan` — 0 errors, 0 bare-path warnings
- [ ] `cli.py validate --cross` — 0 errors, coverage matrix complete
- [ ] All `UNVERIFIED` markers resolved or documented
- [ ] Reviewer agent returns `ready_for_execution: true`
