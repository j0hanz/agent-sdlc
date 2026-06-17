---
name: brainstorming
description: "Structured requirements discovery before implementation. Trigger on 'let's build', 'new feature', 'we need a new', 'I want to implement', 'add X to', 'create a Y', ambiguous design, or unclear terminology — even when the user says 'just build it'. Proactively offer before any implementation begins. Prevents rework by catching problems early."
---

# brainstorming

Structured discovery to prevent rework. Always run for new features or ambiguous requirements.

## Phase 1: Discovery

1. **Stakeholder Probe:** Ask who uses the feature (end users, internal, systems?).
2. **Codebase Scan:**
   - Read `references/codebase-scanner-prompt.md` before dispatching.
   - Dispatch `general-purpose` subagent with the prompt.
   - **Integration**: Upon subagent completion, extract the "Contextual Findings," "Potential Blockers," and "Architectural Fit" sections. These MUST be used to ground the Understanding Statement.
3. **Understanding Statement:** Summarize what was found, constraints, and Key Unknowns. Ask for confirmation.
4. **Adaptive Routing:**
   - **Scope S + No Unknowns:** Jump to Phase 4 (Design).
   - **Scope XL:** Offer to split into sub-features.
   - **Ambiguous Terms:** Run Phase 2 (Clarity).
   - **Scope L/XL or High Blast Radius** (auth, payments, data deletion, external-facing API): Flag now for Phase 5 (Structured Review) — confirm the flag before Phase 4 so the user isn't surprised by the extra step later.

## Phase 2: Domain Clarity (Term Definition)

- **Constraint:** One term at a time. Ask for definition, context, and usage.
- **Goal:** Resolve conflicts between code, docs, and team language.
- **Exit:** Document in `glossary.md` or `CONTEXT.md`.

## Phase 3: Expert Clarification (Techniques)

Select 1-2 techniques (max 4 questions total):

- **Why:** 5-Whys to find hidden motivation.
- **Premortem:** Imagine failure — what went wrong?
- **Success Logic:** Define success behavior without using "functional".
- **Anti-Scope:** Explicitly what we are NOT building.
- **Trust Breach:** How would an attacker abuse this? If this surfaces a concrete attack surface or sensitive data flow, flag for Phase 5 (Structured Review).

## Creative Checkpoint (Before Design)

- Is there a zero-code solution (config, existing extension)?
- Did an analogous feature already solve this?
- What is the 10x simpler version?

## Phase 4: Design Proposal

1. **Dispatch:** Spawn `design-proposer` agent (`references/design-proposer-prompt.md`) with compressed scan report and discovery findings.
2. **Present:** Offer competing approaches with grounded tradeoffs.
3. **Approval Gate:** Wait for explicit commitment to one approach. Do not guess.
4. **Review Check:** If Phase 1 or Phase 3 flagged this design (Scope L/XL, high blast radius, or concrete attack surface), proceed to Phase 5 before the brief. Otherwise skip to Phase 6.

## Phase 5: Structured Review (Conditional)

Only runs when flagged in Phase 1 or Phase 3, or when the user explicitly asks to "stress test" or "review" the design. Skip straight to Phase 6 otherwise — most S/M features don't need this.

**Why a separate phase, not more questions to the user:** the chosen design needs an adversarial check that isn't biased toward the approach you just picked. A single agent reviewing its own work tends to rubber-stamp it, so each role below is a fresh `general-purpose` dispatch that only sees the design and the Decision Log — never the reasoning that produced the design — and **must** be invoked even if you're confident the design is sound. No custom agent definitions are used (per `AGENTS.md`); every dispatch is `general-purpose` configured by the prompt in `references/structured-review-prompt.md`.

1. **Initialize the Decision Log** with the chosen approach as the first row (Decision / Alternatives / Objections / Resolution).
2. **Dispatch in fixed order**, one at a time, each reading the current design + Decision Log so far:
   - **Skeptic** — assumes the design fails in production; surfaces weaknesses, edge cases, YAGNI violations. May not propose redesigns.
   - **Constraint Guardian** — checks performance, scalability, security/privacy, operational cost against the Codebase Context Report's Technical Constraints. May not debate product goals.
   - **User Advocate** — checks usability, cognitive load, error handling from the end user's view. May not add features.
3. **After each reviewer:** explicitly accept and revise, or reject with stated rationale. Append the outcome to the Decision Log before dispatching the next reviewer.
4. **Dispatch the Arbiter** with the final design and the complete Decision Log. It returns one of `APPROVED` / `REVISE` / `REJECT` with rationale — this is the unbiased check that you, having designed the thing, should not perform on yourself.
   - `REVISE`: apply the required changes, log them, re-dispatch the Arbiter only (not the full reviewer loop) to confirm.
   - `REJECT`: return to Phase 4 with the Arbiter's rationale. Do not proceed to Phase 6.
5. **Exit gate (all must hold before Phase 6):** all three reviewers were invoked; every objection is resolved or explicitly rejected with rationale; the Decision Log is complete; the Arbiter's disposition is `APPROVED`.

## Phase 6: Transition (Design Brief)

Produce mandatory `markdown-kv` brief:

- **Chosen Approach:** [Name + Letter]
- **Why:** [Key Tradeoff]
- **Scope:** [In-scope vs. Out-of-scope]
- **Constraints:** [Stack, Timeline, Compliance]
- **Interface:** [Input/Output surface]
- **Architecture:** [Components + Responsibilities]
- **Risk Register:** [Risk/Likelihood/Mitigation table — pull rows from the Decision Log if Phase 5 ran]
- **Review Disposition:** [Arbiter's APPROVED + date, or "Phase 5 not triggered"]
- **First Step:** [Single concrete action]

## Red Flags

- Skipping brainstorming because "it's obvious".
- Assumed terminology (e.g., Account vs. Customer).
- Capturing "HOW" (code) before "WHAT" (domain).
- Skipping Phase 5 for a flagged design because you're confident it's correct — confidence is exactly what the Arbiter exists to check.
- Letting the Primary Designer (you) self-approve a flagged design instead of dispatching the Arbiter.
- **NEVER** proceed without an explicit Approval Gate: Proceeding on assumptions guarantees misalignment with user intent.
