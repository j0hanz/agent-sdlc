---
name: code-review
description: "Mandatory quality gate before delivery. Trigger on 'code review', 'review this diff', 'any issues with this', 'check for bugs', 'quality review'. ALSO trigger automatically: (1) after verification-before-completion confirms tests pass, (2) before opening a PR/shipping the change, (3) on any non-trivial change that will be committed. Do not skip — correctness bugs and security issues discovered here are cheaper to fix than after merge."
disable-model-invocation: false
argument-hint: '[target: branch, commit, file, or "current diff"]'
allowed-tools: Bash(git *)
disallowed-tools: Write, Edit
---

# Code Review

Code review is not verification (does it work?) and not architecture (is it well-designed?). It is a focused scan for **correctness bugs, security risks, missed reuse, and API hygiene** that survived testing. Catching these in the diff is 10× cheaper than after merge.

**Integration Check**: Before proceeding, verify that associated unit tests have passed. If you are unsure, ask the user to confirm that tests passed in the current session or run them using `verification-before-completion`. Do not perform a review if the code hasn't been verified.

**Context Checkpoint**: Because a code review requires deep focus, your context window should not be polluted with early discovery dialogue or debugging logs. Before you begin reviewing the diff, you MUST use the `/compact` or `/clear` command (or the equivalent CLI command in your environment) to clear the conversational history, retaining _only_ the generated artifacts (Specs, Plans) and the diff itself.

---

## Scope

**In scope — hunt for these:**

- Correctness bugs: off-by-one, type mismatches, unhandled edge cases, logic inversions, null dereferences
- Security: command injection, XSS, SQL injection, hardcoded secrets, unsafe deserialization, insecure defaults
- Performance regressions: N+1 queries, unbounded loops, unnecessary copies in hot paths
- Missed reuse: utilities that already exist in the codebase, duplication across 3+ call sites
- API hygiene: breaking changes, undocumented parameters, confusing names on public interfaces

**Out of scope — route elsewhere:**

- **Architecture problems** → `architecture` skill
- **Test adequacy** → `verification-before-completion`
- **Improving readability/structure** → `refactor` skill
- **Performance optimization** (not regression) → not a review concern

---

## NEVER

- **NEVER accept "I don't see any issues"** as a conclusion — state what you checked and why it passed
- **NEVER review code in isolation** — always get a git diff; you need the before/after to spot regressions
- **NEVER report PASS after only skimming** — work through the Phase 2 risk tiers in order
- **NEVER conflate advisory and blocking issues** — mixing them buries the things that actually stop a merge
- **NEVER review without knowing what the code is supposed to do** — read the PR description or ask before scanning

---

## Parallel Per-Module Review

For parallel per-module review, use the `multi-agent-dispatch` skill with `explorer` agents.

---

## Phase 1: Get the Diff

Get the exact diff that is being reviewed. Use the argument if provided; otherwise default to comparing against the main branch.

```bash
git diff origin/main..HEAD            # full branch diff (most common)
git diff HEAD~1                       # last commit only
git diff <commit-sha>                 # specific commit
git show <commit-sha>                 # show single commit with context
git diff --stat origin/main..HEAD     # summary of what changed (run first)
```

Run `--stat` first to understand the shape of the change before reading the full diff.

**If no git history is available:** ask the user for the diff using this format:

```markdown
File: <path/to/file>
Before:
<paste before-code block>
After:
<paste after-code block>
```

Note explicitly that you are reviewing without the before/after context and your confidence is lower.

**Plugin-specific:** For agent-dev plugin files, validate frontmatter in addition to logic — see Phase 2 section.

---

## Phase 2: Risk-Ordered Scan

Scan in this order. Higher tiers surface issues earlier. Do not skip to lower tiers until you have cleared the ones above.

### Tier 1 — Security (Stop Everything If Found)

| Pattern                       | Check                                                                    |
| ----------------------------- | ------------------------------------------------------------------------ |
| Shell / exec call             | Are arguments shell-escaped? Is shell interpolation needed at all?       |
| SQL / query construction      | Are all values parameterized — no string concatenation?                  |
| Permission check placement    | Is the check before the action, not after?                               |
| Hardcoded secret / credential | Is any token, key, or password hardcoded or logged?                      |
| Deserialization call          | Is input validated before deserializing (JSON.parse, pickle, yaml.load)? |
| File path construction        | Is user input sanitized against path traversal?                          |

Any Tier 1 finding is a **blocking issue** — stop and flag immediately.

### Tier 2 — Correctness

| Pattern                             | Check                                                                |
| ----------------------------------- | -------------------------------------------------------------------- |
| Empty catch / swallowed error       | Is the error logged or re-raised with context?                       |
| Off-by-one in loops / slices        | Check boundary conditions: `< n` vs `<= n`, `[i:]` vs `[i+1:]`       |
| Null / undefined access             | Is the value checked before use?                                     |
| State mutation in unexpected places | Does the function mutate its input? Is that documented?              |
| Async / await gaps                  | Are all async calls awaited? Is error handling on the awaited value? |
| Boolean logic                       | De Morgan's law: `!(A && B)` ≠ `!A && !B`; verify complex conditions |

### Tier 3 — Performance Regressions

Check only for **regressions** (new problems introduced by this diff), not pre-existing inefficiency.

- Database call or I/O inside a loop that wasn't there before
- Copying a large collection where a reference or generator would work
- Unbounded retry / recursion with no depth limit
- Missing index on a newly-queried column

### Tier 4 — Missed Reuse & API Hygiene

**Missed reuse:** Grep the codebase for the function's purpose before declaring it new.

```bash
# Example: looking for existing date formatting utilities
git grep -n "formatDate\|format_date\|dateToString" --
```

**API hygiene (public interface changes only):**

- Does the function name describe what it returns, not how it works?
- Are new optional parameters truly optional (backward-compatible defaults)?
- Is any previously-private function now public without documentation?

### Plugin-Aware Checks (agent-dev specific)

When the diff touches a SKILL.md, agent, or hook file, validate it against the authoring rules owned by that file type's skill — do not re-derive the rules here:

- Skills (`skills/*/SKILL.md`) → check against `skill-builder`'s reference rules
- Agents (`agents/*.md`) → check against `create-agent`'s reference rules
- Hooks (`hooks/hooks.json`) → check against `create-hook`'s reference rules
- Commands (`commands/*.md`) → check frontmatter only contains documented fields (`description`, `argument-hint`, `allowed-tools`) and has no `name:` field

---

## Phase 3: Required Output

Always conclude with this exact structure. Do not omit it even when there are no findings.

```markdown
## Code Review Result

**Status**: PASS ✓ | FAIL ✗ ([N] blocking)

### Blocking Issues

<!-- One per bullet. Empty if none. -->

- [file:line] [Issue type] — [what the problem is] → [what to fix]

### Advisory Issues

<!-- One per bullet. Empty if none. -->

- [file:line] [Issue type] — [observation] → [suggested improvement]

### What Was Checked

<!-- Provide a concise summary of checks performed per tier. -->

- Tier 1 (Security): [summary]
- Tier 2 (Correctness): [summary]
- Tier 3 (Performance): [summary]
- Tier 4 (Reuse/API): [summary]
- Plugin checks: [if applicable]
```

**Status definitions:**

- `PASS` — zero blocking issues; advisory issues may exist but do not stop delivery
- `FAIL` — one or more blocking issues; delivery must not proceed until all are resolved

---

## Blocking vs. Advisory

| Category                                | Blocking | Advisory           |
| --------------------------------------- | -------- | ------------------ |
| Security vulnerabilities                | Always   | —                  |
| Data loss / corruption bug              | Always   | —                  |
| Crash in a code path reachable by input | Always   | —                  |
| Breaking API change without migration   | Always   | —                  |
| Swallowed error hiding a real failure   | Usually  | If debug-only path |
| Missed reuse of an existing utility     | Rarely   | Normally           |
| Confusing name on internal helper       | Never    | Yes                |
| Performance concern (non-regression)    | Never    | Yes                |

When in doubt, lean advisory — the goal is to unblock delivery, not to gatekeep.

---

## Transition

After Phase 3:

- **PASS** → prompt the user to run `/github-automation` to open a pull request or merge — that skill requires user invocation and cannot be triggered automatically
- **FAIL** → route to a concrete target based on the blocking issue type, then re-run this skill **only after the developer confirms all blocking issues are resolved** — do not re-review the same unchanged code, and do not downgrade blocking findings to advisory to unblock delivery:
  - Correctness or security issues → invoke `diagnose`
  - Structural issues (coupling, God modules, poor decomposition) → invoke `refactor`
  - Otherwise → return to the originating implementation skill

Do not merge or submit the pull request until code review returns PASS with zero blocking issues.

---

## Reference Files (Conditional Loading)

Do NOT load these by default. Load only when needed:

- **Extended pattern catalog with code examples:** MANDATORY — READ ENTIRE FILE: [`references/patterns.md`](references/patterns.md) when a finding needs a precise name, canonical anti-pattern description, or example fix.
