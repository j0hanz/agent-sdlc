---
name: request-code-review
description: "Mandatory unbiased quality gate. Dispatches a fresh-context subagent to request a new review of a diff for security and correctness — use before feedback exists, not to process feedback already received (see receive-code-review). Trigger on: 'code review', 'review this diff', 'check for bugs', 'quality review', 'request-code-review', 'security audit'."
disable-model-invocation: false
argument-hint: '[target: branch, commit, file, or "current diff"]'
allowed-tools: Bash(git *), Agent
disallowed-tools: Write, Edit
---

# request-code-review

Get an unbiased review by dispatching a fresh-context subagent. Never review your own work in the same thread that wrote it — you already rationalized every decision once; a subagent with no memory of the implementation reads the diff cold, the way a human reviewer would.

## Process Flow

```
Start: Review Request -> 0. Confirm with user -> Pre-Review Checkpoint (tests, context, diffable)
  -> 1. Stat Check (git diff --stat) -> 2. Dispatch Agent (general-purpose) -> 3. Check Result Shape
       -- malformed -------> Retry Dispatch (once) -> back to 3. Check Result Shape
       -- failed twice ----> Escalate to user
       -- well-formed -----> 4. Hand Off Result
                                -- PASS -------------> github-automation (handoff)
                                -- FAIL (blocking) ---> receive-code-review (handoff)
```

## Step 0: Confirm

Action: AskUserQuestion (no manual "Other" option)
Option 1 (Recommended): Dispatch fresh-context review
Option 2 (Alternative): Inline review for small/uncommitted diffs

## Pre-Review Checkpoint

Verification: Confirm unit tests passed
Context: Get commit range (`git log --oneline -10`) and 1-paragraph summary
Diff Check: If no commits, skip dispatch and request Before/After blocks for inline review

## Phase 1: Dispatch

Stat Check: Run `git diff --stat {{base}}..{{head}}`
Prompt: Fill `references/reviewer-dispatch-prompt.md`
Dispatch: Run read-only `Agent` (strictly exclude Write/Edit tools)
Safety Check: Run `git status --porcelain` (if modified: discard, restore, re-dispatch)
Output Validation: Require `## Code Review Result` block (retry once if missing, then fail)

## Phase 2: Hand Off

Action: Keep subagent output verbatim (do not edit)
On PASS: Prompt user "Run `/github-automation`"
On FAIL: Invoke `receive-code-review` (do not fix directly)

## Strict Rules (NEVER)

Self-Review: Forbidden in the same thread
Subagent Writes: Forbidden (enforce tool limits)
Invalid Output: Forbidden (never accept without `## Code Review Result` block)
Isolated Review: Forbidden (diff or before/after blocks required)
