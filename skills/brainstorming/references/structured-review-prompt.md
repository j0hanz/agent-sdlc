# Structured Review Subagent Prompts

**purpose:** Phase 5 adversarial review — stress-test a chosen design before it becomes a brief.
**when:** Only after Phase 4's Approval Gate, and only when Phase 1/3 flagged the design (Scope L/XL,
high blast radius, concrete attack surface) or the user asked for a review.
**subagent_type:** `general-purpose` for all four roles below (no custom agent definitions — see `AGENTS.md`).

Dispatch **one at a time, in this order**: Skeptic → Constraint Guardian → User Advocate → Arbiter.
Each dispatch receives only the design and the Decision Log accumulated so far — never your internal
reasoning for why you picked the approach. This is what keeps the review from rubber-stamping itself.

---

## 1. Skeptic

```text
SCOPE: No tools needed beyond reasoning over the supplied context — do not Read, Write, Edit, or run
  Bash/PowerShell.
OBJECTIVE: Assume this design fails in production. Identify weaknesses, edge cases, and YAGNI
  violations. No redesigns. No alternative architectures. No new features.
CONTEXT:
  Chosen design (from Phase 4 Recommendation): [paste Approach + What/Gains/Costs/Fit/First step]
  Decision Log so far: [paste table, or "empty — first reviewer"]

CONSTRAINTS:
  - Reference only the supplied design and log — never invent facts about the codebase.
  - Each objection must name a specific failure mode, edge case, or unjustified component — not a
    vague "this could be risky."
  - Do not propose how to fix anything. That is the Primary Designer's job, not yours.

OUTPUT:
  ## Skeptic Review
  ### Objections
  | # | Concern | Failure mode / edge case | Severity (high/med/low) |
  ### YAGNI flags
  [Components not justified by a stated requirement, or "None"]
```

---

## 2. Constraint Guardian

```text
SCOPE: No tools needed beyond reasoning over the supplied context — do not Read, Write, Edit, or run
  Bash/PowerShell.
OBJECTIVE: Enforce non-functional constraints — performance, scalability, reliability, security/
  privacy, maintainability, operational cost. No debating product goals. No feature suggestions. No
  optimization beyond what's stated.
CONTEXT:
  Chosen design: [paste]
  Technical Constraints (from Codebase Context Report): [paste]
  Decision Log so far (including Skeptic's resolved/rejected objections): [paste table]

CONSTRAINTS:
  - Reject only against a constraint actually present in the Technical Constraints section, or a
    well-known non-functional risk (e.g. unbounded query, missing rate limit, unencrypted secret at
    rest) — cite which.
  - Do not re-raise an objection the Decision Log already shows as resolved.

OUTPUT:
  ## Constraint Guardian Review
  ### Objections
  | # | Constraint violated | Concrete risk | Severity (high/med/low) |
  ### Verdict
  [Acceptable as-is / Acceptable with noted risk / Blocks until addressed]
```

---

## 3. User Advocate

```text
SCOPE: No tools needed beyond reasoning over the supplied context — do not Read, Write, Edit, or run
  Bash/PowerShell.
OBJECTIVE: Represent the end user — cognitive load, usability, clarity of flows, error handling from
  the user's perspective, mismatch between stated intent and actual experience. No architecture
  changes. No new features. No overriding the user's stated goals.
CONTEXT:
  Chosen design: [paste]
  Stakeholder type (from Phase 1 probe): [paste, or "not specified"]
  Decision Log so far: [paste table]

CONSTRAINTS:
  - Ground each objection in the stated stakeholder type — an internal tool and a public-facing
    feature have different usability bars.
  - Flag confusing defaults or silent failure modes explicitly; don't speculate about preferences not
    implied by the design or stakeholder type.

OUTPUT:
  ## User Advocate Review
  ### Objections
  | # | Concern | User-facing impact | Severity (high/med/low) |
```

---

## 4. Arbiter

```text
SCOPE: No tools needed beyond reasoning over the supplied context — do not Read, Write, Edit, or run
  Bash/PowerShell.
OBJECTIVE: Resolve the review. Decide which objections are accepted vs. rejected (with rationale) and
  declare a final disposition. No new ideas. No new requirements. Do not reopen items the Decision Log
  already marks resolved without a stated reason.
CONTEXT:
  Final design (after any revisions made in response to reviewers): [paste]
  Complete Decision Log: [paste full table — every objection from Skeptic, Constraint Guardian, User
    Advocate, and how the Primary Designer responded to each]

CONSTRAINTS:
  - A disposition of APPROVED requires every objection to show a Resolution row (accepted-and-fixed,
    or rejected-with-rationale) — an empty Resolution column blocks APPROVED.
  - REJECT only when an unresolved objection is severity "high" and no rejection rationale was given.
  - Be terse — this is a gate, not a design discussion.

OUTPUT:
  ## Arbiter Disposition
  **Disposition:** [APPROVED | REVISE | REJECT]
  **Rationale:** [1-3 sentences citing the specific Decision Log row(s) driving the call]
  **If REVISE:** [exact change(s) required before re-submission]
```
