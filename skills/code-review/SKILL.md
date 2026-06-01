---
name: code-review
description: "Code quality review for correctness bugs, security issues, and reuse opportunities. Trigger on 'code review', 'review this', 'any issues with', 'check for bugs', 'quality review'. Mandatory gate between verification and delivery."
disable-model-invocation: false
---

# Code Review

A code review is distinct from verification (does it work?) and architecture (is it well-designed?). Reviews hunt for correctness bugs, security risks, and missed reuse opportunities that slipped past testing.

---

## Scope: What This Skill Covers

Code review is narrowly focused on finding **discoverable issues in the diff**:

- **Correctness bugs** — off-by-one errors, type mismatches, unhandled edge cases, logic inversions
- **Security issues** — command injection, XSS, SQL injection, hardcoded secrets, unsafe deserialization
- **Performance regressions** — N+1 queries, unbounded loops, unnecessary copies
- **Missed reuse** — patterns already in the codebase; duplication; reinventing utilities
- **API hygiene** — breaking changes, undocumented parameters, confusing names

---

## Scope: What This Skill Does NOT Cover

Don't use this skill for:

- **Architecture design** — use `architecture` skill for structural problems
- **Testing adequacy** — that's covered by `verification-before-completion`
- **Performance optimization** — only flag regressions, not "could be faster"
- **Style/naming nitpicks** — unless they block understanding
- **Refactoring** — use `refactor` skill when code is "hard to read" (diff is not in scope for that skill yet)

---

## Workflow

### Step 1: Get the Diff

The review target is always a **git diff**. Don't review code in isolation; review changes.

```bash
git diff origin/main..HEAD            # typical: compare to main
git diff <commit>                     # or: compare to a specific commit
git show <commit>                     # or: single commit
```

If git history is unavailable, ask the user to explain what changed, but know you're at a disadvantage — without the before/after picture, you cannot spot regressions.

### Step 2: Skim for Red Flags

Scan the diff in order of risk:

1. **External-facing changes** — APIs, CLI arguments, config file formats
2. **Security-sensitive** — auth, crypto, secrets, SQL, shell escaping, deserialization
3. **Cross-module changes** — changes that touch multiple files or public interfaces
4. **Dense logic** — tight loops, deeply nested conditions, complex state machines
5. **Error handling** — try-catch blocks, error returns, validation

For each red flag, ask:

- Is this safe? (security, invariants, contracts)
- Is this correct? (edge cases, off-by-one, null checks)
- Is this already done better elsewhere? (missed reuse)

### Step 3: Report Findings

Categorize findings as **blocking** (must fix before shipping) or **advisory** (nice-to-have, doesn't block):

#### Blocking Issues (Stop Shipping)

- Security vulnerabilities
- Correctness bugs (crashes, data loss, wrong output)
- Breaking API changes without migration
- Unhandled exceptions in hot paths

#### Advisory Issues (Can Ship, Fix Later)

- Missed reuse (similar code elsewhere)
- Suboptimal performance (not a regression)
- Confusing names
- Missing edge-case tests (if tests exist at all)

### Step 4: Communicate Results

State findings clearly:

```
## Code Review Result

Status: PASS ✓  (or: FAIL — [N] blocking issues)

Blocking issues:
- [Issue 1]
- [Issue 2]

Advisory issues:
- [Advisory 1]
```

If PASS with zero findings, say so explicitly. Empty reviews are valid.

---

## Common Patterns to Spot

| Pattern                    | Red Flag                | Check                                                   |
| -------------------------- | ----------------------- | ------------------------------------------------------- |
| `try { ... } catch(e) { }` | Silent failure          | Is the catch block doing anything? Is this intentional? |
| New SQL query              | SQL injection           | Are values bound (parameterized)?                       |
| Shell/exec call            | Command injection       | Are arguments escaped? Is shell syntax needed?          |
| Loop over collection       | N+1 query / performance | Is there a database call inside? Can it be batched?     |
| Error handling             | Lost context            | Is the error message descriptive enough to debug?       |
| New public function        | Breaking change         | Was this private before? Is there a migration?          |
| Copied code                | Missed reuse            | Does this utility exist elsewhere in the codebase?      |

---

## What NOT to Say

❌ "This looks correct" — Show the check you ran, not confidence.
❌ "I don't see any issues" — Either you didn't look or everything is fine; say which.
❌ "Consider adding tests" — Testing is verification's job.
❌ "This could be faster" — Only flag if it's a regression or obviously pathological.

✅ "All values are parameterized; no injection risk found."
✅ "File created, no prior version; breaking change risk: low."
✅ "Pattern `selectAll()` → map() exists in 3 places; no duplication here."

---

## Pre-Delivery Gate

This skill is typically invoked between `verification-before-completion` and `delivery-manager`:

1. **Verification** — Does it work? (tests pass, manual testing done)
2. **Code Review** — Is it safe and well-integrated? ← **You are here**
3. **Delivery** — Commit, PR, changelog (only if review passes)

If review fails with blocking issues, stop and route back to implementation.
