# dedupe-subagent-contract

Spec: [dedupe-subagent-contract.specs.md](dedupe-subagent-contract.specs.md)

## Goal

Eliminate the byte-identical duplicate of `subagent-contract.md` so there is exactly one copy to maintain.

## PHASE-001: Implementation

### TASK-001: Delete the duplicate copy

Depends on: none
Files: [multi-agent-dispatch/references/subagent-contract.md](../../multi-agent-dispatch/references/subagent-contract.md)
Symbols: none
Satisfies: REQ-001
Action: Delete `multi-agent-dispatch/references/subagent-contract.md`, keeping `multi-agent-development/references/subagent-contract.md` as the sole copy.
Validate: `git -C C:/agent-dev status --porcelain skills/multi-agent-dispatch/references/subagent-contract.md`
Expected result: File shown as deleted (`D`); no file remains on disk at that path.

### TASK-002: Repoint multi-agent-dispatch's SKILL.md

Depends on: TASK-001
Files: [multi-agent-dispatch/SKILL.md](../../multi-agent-dispatch/SKILL.md)
Symbols: none
Satisfies: REQ-002
Action: Update the link/path in `multi-agent-dispatch/SKILL.md` that previously pointed at its own `references/subagent-contract.md` to instead point at `../multi-agent-development/references/subagent-contract.md`.
Validate: `grep -n "subagent-contract.md" C:/agent-dev/skills/multi-agent-dispatch/SKILL.md`
Expected result: The matched line resolves to `../multi-agent-development/references/subagent-contract.md`, and that file exists.

### TASK-003: Verify no other references broke

Depends on: TASK-002
Files: [brainstorming/SKILL.md](../../brainstorming/SKILL.md), [brainstorming/references/structured-review-prompt.md](../../brainstorming/references/structured-review-prompt.md), [multi-agent-development/SKILL.md](../../multi-agent-development/SKILL.md), [planning/SKILL.md](../SKILL.md)
Symbols: none
Satisfies: REQ-003
Action: Grep all referencing files for `subagent-contract.md` and confirm each resolved relative path points at an existing file (the single surviving copy under `multi-agent-development/references/`).
Validate: `grep -rn "subagent-contract.md" C:/agent-dev/skills --include=*.md`
Expected result: Every match's relative path, when resolved from its containing file, points to `multi-agent-development/references/subagent-contract.md`, and that file exists; zero matches point at a now-deleted path.

## PHASE-END: Acceptance

### TASK-END: Confirm dedup complete

Depends on: TASK-003
Files: none
Symbols: none
Satisfies: REQ-001, REQ-002, REQ-003
Action: Run final verification that exactly one `subagent-contract.md` exists repo-wide and content is unchanged from the original.
Validate: `find /c/agent-dev/skills -name subagent-contract.md`
Expected result: Exactly one path printed: `multi-agent-development/references/subagent-contract.md`.
