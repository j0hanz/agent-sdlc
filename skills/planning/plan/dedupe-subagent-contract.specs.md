# dedupe-subagent-contract

## 1. Goal

- Eliminate the byte-identical duplicate of `subagent-contract.md` so there is exactly one copy to maintain.
- Completion signal: `diff` shows no second copy exists; both skills' SKILL.md still resolve to a valid contract file; `git grep` confirms all 5 referencing SKILL.md files point at the surviving copy.

## 2. Requirements

- `REQ-001`: Exactly one `subagent-contract.md` file MUST remain on disk, at `multi-agent-development/references/subagent-contract.md` (kept because it's the more "primary" of the two skills per SKILL.md cross-references).
- `REQ-002`: `multi-agent-dispatch/SKILL.md` MUST reference the surviving file via relative path (`../multi-agent-development/references/subagent-contract.md`) instead of its own deleted local copy.
- `REQ-003`: All other referencing files (`brainstorming/references/structured-review-prompt.md`, `brainstorming/SKILL.md`, `multi-agent-development/SKILL.md`, `planning/SKILL.md`) MUST continue to resolve correctly — verify no link breaks.

## 3. Constraints

- `CON-001`: MUST NOT change the contract's content (SCOPE/OBJECTIVE/CONTEXT/CONSTRAINTS/OUTPUT SCHEMA structure) — this is a dedup, not a rewrite.

## 4. Interfaces

- Input: two identical markdown files.
- Output: one markdown file + updated relative links in `multi-agent-dispatch/SKILL.md`.
