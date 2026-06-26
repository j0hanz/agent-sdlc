---
name: project-init
description: "Bootstrap a repo's agent instructions via a blind parallel discovery fan-out converging into a deterministic generator. Produces a lean (<100-line) markdown-kv AGENTS.md plus one-line CLAUDE.md/GEMINI.md redirect stubs. Discovery agents are read-only and emit evidence-cited claims; a single script is the sole writer and never executes a discovered command. Trigger on: 'init project', 'project-init', 'onboard repo', 'generate AGENTS.md', 'setup agent instructions', 'initialize project memory', 'audit AGENTS.md'."
disable-model-invocation: true
user-invocable: true
allowed-tools: Bash(python *) Bash(python3 *) AskUserQuestion Skill Read Grep Glob Agent
---

# project-init

**goal:** A lean, high-signal `AGENTS.md` (`<100` lines, markdown-kv `key: value`, never prose) + one-line stub `CLAUDE.md`/`GEMINI.md` that redirect to it.
**method:** Blind parallel discovery (read-only Researcher fan-out, evidence-cited claims) → ONE deterministic generator (`scripts/init.py`) that verifies, merges, and writes.
**invariant:** Discovered commands are transcribed as TEXT, never executed. `init.py` is the SOLE writer.

```
Phase 0  PRESCAN + SURVEY
  -- valid project-init marker found --> reuse encoded answers (offer --force re-survey) --> Phase 1
  -- no marker -----------------------> AskUserQuestion (3 Qs) ------------------------------> Phase 1
  -- no manifest (trivial repo) ------> single serial discovery lane (skip fan-out) ---------> Phase 2

Phase 1  DISCOVERY FAN-OUT  (blind, read-only, claims as JSON)
  L1 build+PM | L2 stack+layout | L3 conventions+CI+docs    (monorepo: + per-package lanes, batch <=3)
  ------------------------------------------------------------------------------------> Phase 2

Phase 2  MERGE (preview)   init.py generate --claims claims.json (no --out)
  -- lint FAIL -------> fix inputs / re-dispatch the failing lane
  -- preview OK ------> show AGENTS.md + dropped report to user --------------------------> Phase 3

Phase 3  CONSENT + WRITE
  -- existing authored file --> back up + explicit overwrite consent
  -- approved ---------------> generate --out --model | wire stubs | lint | receipt --> DONE
```

---

## Phase 0: Prescan & Survey

- **Prescan:** `python "$CLAUDE_PLUGIN_ROOT/skills/project-init/scripts/init.py" prescan .` → JSON `{packages, package_count, file_count, is_monorepo, has_manifest}`. This drives routing; it is cheap (bounded depth-2 walk, skips vendor/`node_modules`).
- **Marker check:** If an `AGENTS.md` exists, scan for `<!-- project-init:hard-rules v1 commit=… maturity=… testing=… ci=… -->`. If present and valid, **reuse those answers** — do not re-survey. Tell the user it was found and offer to re-survey (treat any "reconfigure / my conventions changed" as the `--force` path).
- **Survey (only when no valid marker):** Call `AskUserQuestion` **once** with the 3 questions in `references/hard-rules.md` — commit policy, project maturity, testing rigor. Use the option wording verbatim (each option states its effect in plain language). Never add an "Other" option. Halt with no files written if dismissed.
- **CI is never surveyed** — detect it: `.github/workflows/` → `github-actions`, `.gitlab-ci.yml` → `gitlab-ci`, else `local-only`.
- **Routing:** `has_manifest == false` → trivial repo: do ONE serial discovery pass yourself (Read the few files), skip the fan-out, go to Phase 2. Otherwise → Phase 1.

---

## Phase 1: Discovery Fan-Out

Dispatch blind, **read-only** Researcher agents via `multi-agent-dispatch` (write the MATRIX first). Each starts cold — put every fact in the prompt. Exactly 3 facet lanes (= foreground cap):

| Lane | Facet                   | Scope                                                                                             |
| :--- | :---------------------- | :------------------------------------------------------------------------------------------------ |
| L1   | build + PM              | package manager, install/build/dev/test/lint/typecheck commands, lockfiles, entrypoints           |
| L2   | stack + layout          | languages, frameworks, directory topology, module boundaries (may invoke `architecting`)          |
| L3   | conventions + CI + docs | lint/format config, CI workflows, commit/branch norms, existing AGENTS/CLAUDE/GEMINI/.cursorrules |

**Monorepo** (`is_monorepo`): add one lane per package dir, run in background batches of ≤3; per-package detail becomes a **package-level `AGENTS.md`** (root stays a summary). Confirm with the user before fanning out above ~6 packages.

Every lane's dispatch prompt carries the five fields (SCOPE / OBJECTIVE / CONTEXT / CONSTRAINTS / OUTPUT-SCHEMA) and:

- **CONSTRAINTS:** read-only (Read/Grep/Glob, **no Bash, never run a command**); cite evidence for every claim; a command/version claim MUST quote a literal `match` string from the cited file.
- **CONTEXT:** the survey answers + the prescan file manifest. Instruct targeted reads of named files, not full-tree dumps.
- **OUTPUT-SCHEMA:** a JSON array of claims per `references/canonical-keys.md` — `{key, value, evidence:{path, match}, confidence}`. No prose.

Collect each lane's JSON. **Never trust a self-reported verdict** — the deterministic merge is the gate.

---

## Phase 2: Merge (preview)

- Concatenate all lanes' claim arrays into one `claims.json` (scratchpad).
- `python … init.py generate --claims claims.json --commit <c> --maturity <m> --testing <t> --ci <ci> [--purpose "<one sentence>"]` (no `--out` → preview to stdout; the attribution placeholder is expected here).
- The engine verifies each claim (path resolves inside repo + required `match` present + canonical key), keeps one winner per key by evidence tier then confidence, sanitizes values, and trims to the `<100`-line budget. Dropped/unverified claims print to stderr.
- **Show the user** the previewed `AGENTS.md` AND the dropped-claims report. If `generate` exits non-zero (lint FAIL — e.g. required keys overflow the budget), fix the inputs or re-dispatch the offending lane; do not write.

---

## Phase 3: Consent & Write

- **Overwrite guard:** For any of `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` that already exists and is NOT already a one-line stub, show its content, back it up (`*.bak`), and get **explicit consent** before replacing. A real hand-written `CLAUDE.md` must never be silently reduced to a stub.
- **Write:** `init.py generate --claims claims.json … --model "<active model name>" --out AGENTS.md` (atomic temp+rename, UTF-8 no BOM, `\n`).
- **Wire stubs:** `init.py wire AGENTS.md CLAUDE.md GEMINI.md`.
- **Lint:** `init.py lint AGENTS.md` — must PASS.
- **Receipt:** report files written + line count, and restate the dropped-claims summary so the user knows what was discovered-but-omitted.

---

## Failure Recovery

- Any script non-zero exit → invoke `diagnose` via `Skill` with the stderr; fix the root cause, resume the failed phase (never restart Phase 0).
- Finish by handing to `verification-before-completion`.

## Prohibitions

- **never** execute a discovered command, or give a discovery lane Bash.
- **never** hand-write or concatenate `AGENTS.md` — `init.py` is the only writer.
- **never** copy file content into a stub (one-line redirect only).
- **never** overwrite an authored `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` without backup + consent.
- **never** keep a claim whose evidence path is unresolved, outside the repo, or missing a required `match`.
