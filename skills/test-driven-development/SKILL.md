---
name: test-driven-development
description: 'This skill should be used when the user asks to write tests, implement a feature using TDD, perform red-green-refactor cycles, write a unit test, cover scenarios, or do test-first development. It enforces a strict test-first workflow for new features, excluding pre-diagnosed bug fixes.'
disable-model-invocation: false
---

# test-driven-development

Autonomous TDD execution. **HARD GATE:** No implementation code WITHOUT a failing test.

## When NOT to use TDD

These are escape hatches from the HARD GATE — never self-invoke one silently. Confirm the carve-out via `AskUserQuestion` before skipping RED (the tool supplies a free-text "Other" automatically). Pick from the three categories below (see their definitions immediately following):

1. ✅ **Recommended** — Skip TDD: [the matching category from the list below] because [specific reason this case matches].
2. **Alternative** — Use full TDD anyway + the reason the carve-out doesn't actually apply.

- **Exploratory Spikes:** When the implementation path is unknown and you need to "find the shape" of the code first (throwaway code). **Mandatory:** once the shape is found, the spike code MUST be discarded (`git stash drop`/delete, not committed) and re-implemented through the normal RED-GREEN-REFACTOR loop. A spike is a sketch, never the shipped diff.
- **Trivial One-Liners:** Pure data mappings or standard boilerplate with zero logic.
- **Pure UI/CSS:** Visual styling that requires manual "eye-balling" rather than logical assertions.

## Process Flow

```
Start: TDD Request -> Carve-out applies (spike/trivial/CSS)? -- yes --> AskUserQuestion confirms skip -> exit (handle outside this skill)
                                                              -- no  --> 0. Confirm with user -> Pre-TDD: Interface (signatures, errors, examples) -> TDD Cycle:

  1. RED (write failing test + minimal stub) -> run test, confirm failure
       -- failure confirmed --> 2. GREEN (write minimal implementation) -> run test
                                   -- fail --> Stuck? (3+ attempts)
                                                  -- yes --> diagnose/planning (handoff)
                                                  -- no  --> retry GREEN
                                   -- pass --> 3. REFACTOR (surgical cleanup) -> run test, stay passing
                                                  -> All scenarios covered?
                                                       -- no  --> back to TDD Cycle
                                                       -- yes --> verification-before-completion (handoff)
```

**trigger:** TDD, write tests, implement feature, build this.
**constraint:** No implementation code WITHOUT a failing test.
**constraint:** Execute exactly ONE scenario per cycle. No horizontal slicing.
**example:** WRONG — write failing tests for `calculate_discount`, `apply_tax`, and `format_price` before implementing any of them. RIGHT — RED+GREEN+REFACTOR `calculate_discount` fully, then start the next scenario.

## Step 0: Confirm

**action: TDD Confirmation**
Confirm the start of an autonomous session via `AskUserQuestion` — the tool supplies a free-text "Other" automatically, so don't add one manually:

1. ✅ **Recommended** — Proceed with TDD for [specific function/feature].
2. **Alternative** — [Non-TDD approach, e.g. spike/throwaway exploration first] + the reason it fits this case better.

## Step 1: Pre-TDD Interface

**action: Document Interface**
Propose and confirm the public surface via `AskUserQuestion` — the tool supplies a free-text "Other" automatically, so don't add one manually:

1. ✅ **Recommended** — Signature: [name(params) -> return_type] based on [requirements/conventions].
2. **Alternative** — [Alternative Signature] + the justification for the different shape.

3. **Error Cases:** Explicit exception types.
4. **Usage:** 2-3 realistic scenarios.
5. **Target:** Identify test file path.
6. **Sanity Check:** Run the existing test suite to verify that the test runner and project configuration are active and healthy before writing the new failing test.

## Step 2: RED (Failing Test)

**MANDATORY:** For JavaScript/TypeScript projects, read [js-ts-patterns.md](references/js-ts-patterns.md) completely from start to finish. Do NOT set any range limits when reading this file. Do NOT load this file if the project is written in Python.

**action:** Write simplest test for single core behavior.
**action:** Write minimal stub to allow compilation (e.g., `pass`, `return null`).
**action:** Run test.
**gate:** Confirm failure (Assertion Fail). If pass, delete and rewrite.

### N-1 Test (False-Green Elimination)

A test that never fails proves nothing. Before trusting any GREEN result (here or in `verification-before-completion`):

1. **Revert** the implementation change (stash or comment it out) while keeping the test.
2. **Fail** — run the test, confirm it fails. If it still passes, the test is not exercising the behavior; rewrite it.
3. **Fix** — restore the implementation.
4. **Pass** — run the test again, confirm it passes.

Use this whenever a test's failure mode is non-obvious (e.g., async code, mocked boundaries, snapshot tests).

## Step 3: GREEN (Minimal Implementation)

**MANDATORY:** If the "absolute minimum" implementation is unclear for the domain (e.g., math, validation, parsing, class extraction), read [minimal-impl-examples.md](references/minimal-impl-examples.md) completely from start to finish. Do NOT set any range limits when reading this file. Skip if the minimal implementation is obvious.

**action:** Commit/stash before editing.
**action:** Write **absolute minimum** code to pass the test.
**constraint:** No speculative abstractions or "just-in-case" logic.
**escalation:** If stuck 3+ attempts, revert and write a smaller test.
**escalation:** If still stuck, invoke `diagnose` or `planning`.

## Step 4: REFACTOR (Cleanup)

**gate:** Enter ONLY when tests are GREEN.
**action:** Perform surgical improvements (Rename, Decompose, Flatten, DRY).
**constraint:** Refactor and Implementation must be separate tool calls. Run tests between them.
**example:** WRONG — spotting duplicate logic while still RED and cleaning it up alongside the fix. RIGHT — get GREEN first (duplication and all), run tests, then refactor as its own step, then run tests again.

**next skills:**

- `verification-before-completion`: Once all scenarios are covered and passing, to perform final regression sweeps and manual verification.

**transition:** Invoke `verification-before-completion` after final REFACTOR pass.

## Mandatory Rules

**constraint:** Never mock internal collaborators. Mock only at system boundaries (API, DB, I/O).
**constraint:** Never bypass public interfaces for setup.
**constraint:** Never write multiple tests before implementing the first one.
**constraint:** Never skip "Run Test" between RED and GREEN.
**constraint:** Never edit a test's assertions to force GREEN. Fix the implementation; if the test itself was wrong, revert to RED and state why before changing it.

## Transition

**next:** Invoke `verification-before-completion` after final REFACTOR pass.
