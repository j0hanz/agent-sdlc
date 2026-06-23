---
name: diagnose
description: "Disciplined root-cause analysis for bugs and crashes. Systematic falsification workflow to identify true causes. Not for writing tests for new feature work (see test-driven-development) or non-bug structural cleanup (see refactor). Trigger on: 'debug', 'fix crash', 'why is this failing', 'unexpected output', 'diagnose bug', 'root cause analysis', 'feedback loop', 'instrumentation'."
disable-model-invocation: false
argument-hint: '[symptom description or error trace]'
---

# diagnose

Identify true root cause through systematic falsification. **DO NOT GUESS.**

## Process Flow

```
Phase 1: Build Feedback Loop (pass/fail signal)
  -> Phase 2: Reproduce (confirm bug)
  -> Phase 3: Hypothesize & Falsify (3-5 hypotheses)
       -- falsified --> retry Phase 3 with new hypotheses
  -> Phase 4: Instrumentation (targeted probes)
  -> Phase 5: Red-Green Fix (regression test)
  -> Phase 6: Finalization (de-instrument / verify)
```

**trigger:** debug, fix crash, unexpected behavior
**constraint:** apply 1 hypothesis per run
**constraint:** modify working copy only
**constraint:** reject "works on my machine"

## Phase 1: Feedback Loop

**action:** create <2s deterministic pass/fail signal
**action:** isolate filesystem, pin seeds/time
**mandatory:** read `references/feedback-loops.md` (do NOT load `phases.md`)
**gate:** require loop or request telemetry/logs

## Phase 2: Reproduce

**action:** achieve >50% reproduction rate
**gate:** require logged repro signal before Phase 3

## Phase 3: Hypothesize & Falsify

**mandatory:** read `references/phases.md` (do NOT load `feedback-loops.md`)
**action:** propose 3-5 falsifiable hypotheses via `AskUserQuestion` (surface top 3, queue rest)
**format:** "If [X] is the cause, then [Y] will change when I do [Z]."
**dispatch:** use `multi-agent-dispatch` for independent hypotheses (require `isolation: worktree`)
**gate:** require confirmed probe result (no guessing by elimination)

## Phase 4: Instrumentation

**action:** instrument decision boundaries dynamically
**format:** prefix logs with `[DEBUG-XXXX]`
**constraint:** target logs strictly; use profilers for performance

## Phase 5: Red-Green Fix

**action:** write regression test targeting failing seam
**action:** confirm RED
**action:** apply minimal fix on working copy
**action:** confirm GREEN
**action:** execute N-1 test (revert fix -> confirm RED -> restore fix)

## Phase 6: Finalization

**action:** remove all `[DEBUG-XXXX]` tags
**action:** verify fix via Phase 1 loop
**action:** promote scripts to test suite or delete

## Next Skills

**test-driven-development:** implement new logic/tests
**refactor:** clean up 1 file/function
**architecting:** clean up multiple files/modules
**planning:** address major specification gaps

## Transitions

**verification-before-completion:** re-verify in same skill
**test-driven-development:** resume current task/phase
**multi-agent-development:** resume current task/phase
**refactor:** resume refactor cycle
**multi-agent-dispatch:** resume INTEGRATE step
**receive-code-review:** resume Step 4 Implement
**codebase-init:** resume Failure Recovery step
**github-automation:** resume failed script/PR step

## Exclusions

**test-driven-development:** use for writing new feature tests
**refactor:** use for non-bug structural issues

## References

**references/feedback-loops.md:** setup patterns by system type
**references/phases.md:** detailed phases, hypothesis prioritization, profiling

## Output Format

**symptom:** [Description]
**root_cause:** [Correct Hypothesis]
**fix:** [Changes]
**feedback_loop:** [Reproduction Script]
**prevention:** [Architecture/Test improvement]
**next_steps:** [Follow-up tasks]
