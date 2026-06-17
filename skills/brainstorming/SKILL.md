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
   - **Integration**: Upon subagent completion, extract the "Interface Shapes," "Technical Constraints," "Analogous Features," and "Key Unknowns" sections. These MUST be used to ground the Understanding Statement.
   - **Zero-Code Exit**: If the scanner finds an existing feature or configuration that satisfies the request, present it immediately and offer to exit.
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
- **Proactive Filter**: If a zero-code or analogous solution is found, it MUST be presented as "Approach A" in Phase 4.

## Phase 4: Design Proposal

1. **Dispatch:** Spawn `general-purpose` agent (`references/design-proposer-prompt.md`) with compressed scan report and discovery findings.
2. **Present:** Offer 2-3 competing approaches with grounded tradeoffs.
3. **Approval Gate:** Wait for explicit commitment to one approach. Do not guess.
4. **Review Check:** If Phase 1 or Phase 3 flagged this design (Scope L/XL, high blast radius, or concrete attack surface), proceed to Phase 5 before the brief. Otherwise skip to Phase 6.

## Phase 5: Structured Review (Conditional)

Only runs when flagged in Phase 1 or Phase 3, or when the user explicitly asks to "stress test" or "review" the design.

**Parallel Adversarial Loop**: To ensure objectivity and reduce latency, reviewers run concurrently.

1. **Dispatch Parallel Stress-Test:** Using `multi-agent-dispatch`, spawn three independent reviewers who only see the design and context packet — they do NOT see each other's objections or your internal reasoning.
   - **Skeptic** (`general-purpose`) — assumes the design fails in production; surfaces weaknesses, edge cases, YAGNI violations.
   - **Constraint Guardian** (`general-purpose`) — checks performance, scalability, security/privacy against the Codebase Context Report.
   - **User Advocate** (`general-purpose`) — checks usability, cognitive load, error handling from the end user's view.
2. **Consolidate & Respond**:
   - Collect all objections into a **Response Log** (Objection | Source | Severity | Designer Response | Resolution).
   - You MUST address every objection: either **Accept & Revise** (updating the design) or **Reject** with a technical rationale.
3. **Arbiter Gate**:
   - Dispatch the **Arbiter** (`general-purpose`) with the original design, the revised design, and the full Response Log.
   - The Arbiter evaluates if your rejections are valid and if your revisions actually mitigate the concerns.
   - It returns `APPROVED`, `REVISE` (back to step 2), or `REJECT` (back to Phase 4).
4. **Exit gate**: all reviewers invoked; Response Log is complete; Arbiter disposition is `APPROVED`.

## Phase 6: Transition (Design Brief)

Produce mandatory `markdown-kv` brief:

- **Chosen Approach:** [Name + Letter]
- **Why:** [Key Tradeoff]
- **Scope:** [In-scope vs. Out-of-scope]
- **Constraints:** [Stack, Timeline, Compliance]
- **Interface:** [Input/Output surface]
- **Architecture:** [Components + Responsibilities]
- **Risk Register:** [Risk/Likelihood/Mitigation table — pull rows from the Response Log if Phase 5 ran]
- **Review Disposition:** [Arbiter's APPROVED + date, or "Phase 5 not triggered"]
- **First Step:** [Single concrete action]

## Red Flags

- Skipping brainstorming because "it's obvious".
- Assumed terminology (e.g., Account vs. Customer).
- Capturing "HOW" (code) before "WHAT" (domain).
- **Self-Approval**: Approving a flagged design without the Arbiter.
- **Arbiter Rubber-stamping**: Arbiter approving with unresolved High-severity objections or rejections without rationale.
- **Context Drift**: Design ignores architectural constraints found in Phase 1.
- **Subagent Role Bleed**: Reviewers proposing redesigns instead of identifying flaws.
- **NEVER** proceed without an explicit Approval Gate.
