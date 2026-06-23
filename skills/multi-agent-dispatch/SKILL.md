---
name: multi-agent-dispatch
description: "Parallel execution for independent tasks. Fans out to isolated subagents for efficiency. Not for tasks with shared mutable state or dependencies — those need strict ordering (see multi-agent-development). Trigger on: 'in parallel', 'dispatch agents', 'fan out', 'multi-agent-dispatch', 'independent tasks', 'concurrent execution'."
disable-model-invocation: false
argument-hint: '[the independent tasks to parallelize]'
---

# multi-agent-dispatch

Maximize efficiency through parallel execution across isolated problem domains. Independent domains (no shared state) → this skill. Shared mutable state or dependencies → `multi-agent-development` instead; see Dispatch Gate below for the exact test.

```
GROUP -> SELECT -> LAUNCH -> INTEGRATE
                      ^         |
                      └─ retry ─┘ (partial failure)
```

## Strict Rules

- **NO Overlapping Writes:** Never launch parallel agents editing the same files. Use sequential execution instead.
- **NO Assumed Context:** Subagents start blank. Put every needed fact directly into the prompt.
- **MAX 3 Agents:** Launch a maximum of 3 agents per batch. Combine their work before starting more.
- **NO Blind Trust:** Agents make mistakes. You MUST run the test suite to prove their work is correct.

## Dispatch Gate

Run parallel agents ONLY if BOTH are true:

1. **Authorized:** The user or the active step explicitly asked for parallel work.
2. **Independent:** Tasks are 100% separate.

- No shared files to edit.
- No task depends on another task finishing first.
- No shared limits (like databases or API limits).

_If false or unsure, do not run in parallel. Use sequential `multi-agent-development`._

## Four-Step Loop

**MANDATORY:** Read `../multi-agent-development/references/subagent-contract.md` before starting.

1. **GROUP:** Confirm the task groups with the user using `AskUserQuestion`.
2. **SELECT:** Assign roles (Investigator, Writer, Researcher).

- Writers MUST use `isolation: worktree` to prevent overlapping edits.

3. **LAUNCH:**

- Verify no files overlap between agents.
- Limit to 3 agents per batch.
- Launch all agents in ONE single message.

4. **INTEGRATE:** Combine the work and run the tests.

### Partial Failures (During Integration)

- Keep and save the successful, tested work.
- Re-run only the failed tasks with fresh agents.
- If a task failed because it secretly needed another task to finish first, stop parallel work. Switch to sequential work.
- Always report blocked or failed tasks to the user.

## Integration Rules

- **Read:** Agents can read the same files.
- **Write:** Agents CANNOT edit the same files.
- **Validate:** Run tests on all agent work. Never just trust the report.

## Success Criteria

All results are combined, tests are GREEN, and tasks are passed to `verification-before-completion`.

## Next Skills

- `verification-before-completion`: Run this to check final work.
- `multi-agent-development`: Run this if tasks depend on each other (sequential).
- `diagnose`: Run this if combining the code causes errors.
