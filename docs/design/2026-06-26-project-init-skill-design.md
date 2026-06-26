# project-init — Design Brief

approach: Replace `codebase-init` with a new skill `project-init` at `skills/project-init/` (delete the old dir). Same goal — a lean `<100`-line markdown-kv `AGENTS.md` + one-line `CLAUDE.md`/`GEMINI.md` redirect stubs — but discovery is a blind parallel Researcher fan-out (Approach B, "Facet fan-out") converging into a single deterministic serial generator. Full engine rewrite carrying old hardening forward.

why: The old skill is strictly sequential and script-bound; the only genuinely independent work is repo discovery. Fanning it out across facet specialists matches the house `multi-agent-dispatch` / `parallel-brainstorming` patterns and is the most literal reading of "fully parallel optimized." Every finding is an evidence-cited claim so the deterministic merge is contradiction-free, hallucination-filtered, and budget-bounded by construction — solving the hardest constraint (merging N cold-start reports into one lean file) structurally rather than by prompting.

scope: L. In: new SKILL.md, single `scripts/init.py` (prescan/merge/scaffold/wire/lint subcommands), `references/`, `tests/`, delete `skills/codebase-init/`, update plugin registration + slash-command name. Out (excluded from lanes A/C): policy inference from git history, the self-verifying fresh-agent command-runner loop, an agent-based AGENTS.md auditor (deterministic lint replaces it).

## Constraints (hard — carried from old skill + Phase 5)

format: AGENTS.md is markdown-kv (`key: value`), never prose; `<100` lines; stubs are one-line redirects that never duplicate content.
no-exec: discovered build/test commands are transcribed as text, NEVER executed. Researchers limited to Read/Grep/Glob — no Bash.
containment: `realpath`-resolve then repo-root containment check on every READ (claim evidence path) and WRITE (AGENTS.md + stub targets) path; OS-correct comparison for Windows.
write-safety: UTF-8 no BOM, `\n` newlines, atomic temp-file + rename; normalize BOM/CRLF on input reads.
consent: present generated AGENTS.md for approval before writing to disk; back up + require explicit consent before replacing any non-stub existing AGENTS.md / CLAUDE.md / GEMINI.md.
trust: never trust an agent self-report; deterministic lint is the gate.

## Interface

invocation: user-invocable slash skill (`disable-model-invocation: true`, `user-invocable: true`), trigger phrases: init project, onboard repo, project-init, setup agent instructions, initialize project memory.
survey: one `AskUserQuestion` (commit policy / maturity / testing rigor), 3 options each with a plain-language effect line. Skipped only when an existing AGENTS.md carries a valid hard-rules marker; the marker ENCODES the answers (`commit= maturity= testing= ci=`) so re-runs reuse them. `--force` re-surveys.
claim-schema: `{ key, value, evidence: { path, match }, confidence }`. `key` from a CLOSED canonical vocabulary; out-of-vocab keys dropped + logged. `match` REQUIRED for command/version keys.
outputs: AGENTS.md + wired stubs + a closing receipt (files written, line count) + a side "dropped/unverified" report (outside AGENTS.md) listing discarded claims and why.

## Architecture (flow)

```
Phase 0  PRESCAN + SURVEY (serial)
  prescan: bounded depth<=2 walk (skip vendor/node_modules/.git) -> {packages[], file_count}
  survey:  AskUserQuestion unless valid marker -> answers
  no recognizable manifest -> collapse to ONE serial discovery lane (tiny-repo fast-path)

Phase 1  DISCOVERY (parallel, blind, read-only) -- five-field contract, answers ride in CONTEXT
  L1 build+PM     | L2 stack+layout (may invoke architecting) | L3 conventions+CI+docs
  3 lanes = foreground cap. Monorepo (3+ pkgs): per-package lanes batch <=3 background,
  confirm above N. Each lane gets the prescan file manifest + targeted-Read (no full dumps).
  Output: evidence-cited markdown-kv claims only.

Phase 2  MERGE (serial, deterministic init.py = SOLE writer)
  verify(claim): path resolves in repo AND text-file < size-cap contains match -> else discard
  arbitrate: tier from cited-path pattern (lockfile/config > script > prose > inference), then confidence
  one winner / canonical key; sanitize values (strip newlines, single line)
  emit by fixed priority (build/test/PM top); HARD-STOP <100L; required keys overflow -> lint FAIL surfaced
  monorepo: per-package detail -> package-level AGENTS.md; root stays summary

Phase 3  GENERATE (serial) -> show for approval -> scaffold AGENTS.md -> wire 1-line stubs -> lint
  lint: kv-only (+ whitelisted ## Commit Attribution section), <100L, no TODO/filler/hallucinated-command

Failure: any script failure -> diagnose skill. Finish -> verification-before-completion.
```

## Risks (residual, post-critique)

prescan-miscount: vendored/nested manifests inflate package count -> needless fan-out. Mitigation: depth<=2, exclude vendor dirs; orchestrator may override.
canonical-vocab-tuning: too narrow drops real signal, too broad reverts the noise/budget problem. The one piece needing human judgment; iterate against real repos in tests.
lane-overlap: L1/L3 may surface the same key with differing confidence; arbitration (tier-then-confidence) resolves, but redundant reads cost tokens — share the prescan manifest.

## First step

build: `scripts/init.py` skeleton with the closed canonical-key list, claim JSON schema, the path-containment + required-match verification gate, priority-ranked arbitration, value sanitization, and `lint()` assertions — plus `tests/` covering: conflicting pnpm-vs-npm claims resolve to the lockfile winner, a no-match command claim is demoted, an out-of-repo/symlink evidence path is rejected, and byte-level `\n`-newline output. Then SKILL.md frontmatter + Process-Flow cloned from the multi-agent-dispatch shape.
