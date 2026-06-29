# Design Brief: `project-audit`

Status: DRAFT v2 — produced via `parallel-brainstorming`, redone after v1 was rejected as derivative. 5 ideators → synthesis → 3 blind critics → arbiter, twice. Not yet implemented.

## Approach

Replace the `architecting` skill entirely with a new skill, `skills/project-audit/`, scoped to read-only structural/architecture auditing. Core mechanism ("Ask, don't compute"): **no detection scripts as the primary mechanism.** Parallel `researcher` agents reason directly over source, one per directory-lane, answering five fixed questions; a small deterministic helper only handles the one sub-problem judgment is bad at (joining free-text import claims into a cycle graph).

1. **GROUP:** a cheap depth-1 directory listing (no file content read) bands top-level directories into ≤8 lanes by file count — merge tiny ones, split oversized ones, drop non-code dirs (docs/, .github/, lockfile-only) before any dispatch.
2. **LAUNCH:** one `researcher` agent per lane, in parallel, in one message. Each reads only its own lane and answers: stated purpose (or admits none), literal imports out, infra-bleed smell (file+pattern), size/cohesion outliers (file), hidden non-import coupling (file).
3. **AGGREGATE:** a small new script joins the literal import answers into a graph (lane-resolved, not raw strings) and runs cycle detection. A synthesis prompt does the rest: ranks findings by how many independent lanes corroborate them, adjudicates intent-mismatch contradictions by evidence strength rather than just reporting disagreement, merges repeated finding-shapes into one pattern, and flags lanes that claim overlapping responsibility.
4. **OUTPUT:** one flat report, corroborated findings first, tagged by kind — no borrowed severity vocabulary, no ADR, no scaffold.

## Why

v1 of this brief kept `architecting`'s four detection scripts (with two bug fixes) and its dispatch-by-file-shard mechanics — the user rejected it as "just copied from the old skill." Root cause (see memory: feedback on fresh-build-vs-inspiration): the v1 brainstorm's shared ideation context pre-labeled those scripts "confirmed safe to reuse," which anchored every lens toward porting old mechanism forward instead of inventing fresh.

This redo removed that anchor and re-ran ideation neutrally. Three of five lenses independently converged on dropping static-analysis scripts entirely in favor of agents reasoning directly about code — for three different reasons (cost-bounding, intent-detection, peer-review structure), which is a real signal, not framing bias. The user picked "Ask, don't compute" specifically because it shares zero mechanism with `architecting`.

Critique then found 22 flaws, the most serious being a scale problem: unbounded fan-out (one agent per top-level directory, no cap) is arguably _worse_ than `architecting`'s scale problem, since every lane reads full directory content rather than a bounded hotspot list. The fix borrows lane-banding from a sibling, also-fresh, **not-selected** brainstorm approach from this same round ("bounded lanes") — not from `architecting`, which had no such mechanism. The arbiter explicitly checked for, and found none of, the original failure mode: no resolution reintroduces `architecting`'s scripts-as-primary-mechanism, its HIGH/MEDIUM/LOW vocabulary, or ADRs.

## Scope

- **In:** circular dependencies (best-effort, via free-text import corroboration, not guaranteed-complete), infra-bleed into domain code, hotspot/God-file/cohesion outliers, hidden coupling, responsibility overlap between modules, intent-mismatch (stated purpose vs. actual coupling — a finding type `architecting` could never produce). Read-only.
- **Out:** new-module design mode, ADRs, scaffolding, structured handoff artifacts, anything overlapping `find-bugs`/`security-review`/`ponytail-audit`.
- **Size:** L — new skill (SKILL.md + one small script + its test) plus edits to 5 cross-reference files.

## Constraints

- Must pass `tests/validate-plugin.test.mjs` (frontmatter validity, no dangling cross-skill references).
- `AGENTS.md`: clean rewrites are this repo's convention — no compat shim for `architecting`.
- `researcher` subagent (`agents/researcher.md`) is fixed: Haiku model, default schema is flexible enough to repurpose. **Lane dispatches grant Read/Grep/Glob/Bash only — WebFetch is explicitly NOT granted** (no question in the lane protocol needs external URLs; granting it only widens prompt-injection blast radius from adversarial repo content).
- Pytest auto-discovers `skills/**/scripts/tests/` via `testpaths = ["skills"]` in `pyproject.toml` — no extra config for the new script's test.

## Interface

- **Frontmatter:** `name: project-audit`, `allowed-tools: Bash(python *), Bash(python3 *), Agent(researcher)`.
- **Lane prompt (fixed, 5 questions, asked of every non-filtered lane):**
  1. Purpose: one sentence, or explicit "no coherent purpose" (itself a finding).
  2. Imports out: literal import lines, copied character-for-character, with source file — not paraphrased (this exact instruction exists because free-text drift broke the cycle-detection join in critique).
  3. Bleed smell: infra-in-domain mixing, must name the file+pattern.
  4. Size/cohesion outliers: must name the file.
  5. Hidden coupling: non-import coupling elsewhere in the repo, must name the file.
- **New script:** `skills/project-audit/scripts/check_cycles.py` (new, ~60 lines, stdlib only — not a port of `architecting`'s `utils/graph.py`). Input: all lanes' Q2 answers + lane membership. Behavior: normalizes superficial formatting (quotes, semicolons, leading `./`), resolves each import target to its owning lane by directory-prefix match (drops intra-lane edges), builds an inter-lane adjacency list, runs cycle detection. Explicitly does NOT attempt full alias/re-export resolution — out of scope, documented limitation. Own `test_check_cycles.py`.
- **Final report row:** `{finding, kind (cycle/bleed/cohesion/coupling/intent-mismatch/overlap), corroboration (N lanes, or "single-lane"), evidence}`. No numeric score, no HIGH/MEDIUM/LOW tier.

## Architecture

```text
┏━ GROUP (cheap, no content read) ━━━━━━━━━━┓
┃ depth-1 listing → drop non-code dirs →     ┃
┃ band into ≤8 lanes (merge tiny, split      ┃
┃ oversized; flat repo → chunk by extension, ┃
┃ NOT alphabetical — and flag low-confidence)┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
              ↓
┏━ LAUNCH (parallel, one message, ≤8) ━━━━━━┓
┃ researcher(lane 1) | ... | researcher(lane K) ┃
┃ Read/Grep/Glob/Bash only. 5 fixed questions.  ┃
┃ Lane with nothing flagged → one-line summary. ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
              ↓
┏━ AGGREGATE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ check_cycles.py: joins Q2 answers,         ┃
┃   lane-resolved, best-effort (not complete)┃
┃ Synthesis prompt:                          ┃
┃   - corroboration ranking (2+ lanes agree  ┃
┃     → surfaced first, labeled "N lanes")   ┃
┃   - adjudicates intent-mismatch by evidence┃
┃     strength, not just "these disagree"    ┃
┃   - merges repeated finding-shapes (3+     ┃
┃     lanes, same pattern) into one entry    ┃
┃   - flags Q1-vs-Q1 responsibility overlap  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
              ↓
   Flat report, corroborated-first, kind-tagged,
   no severity vocabulary. Closing line points to
   `request-plan` for acting on any single finding.
```

## Risks

- **Lane-size/latency variance is mitigated, not solved.** Banding bounds lane _count_ and average size, but wall-clock is still bounded by whatever lane lands largest within its band. No further fix attempted — a full fix would require either a much tighter band (more lanes, more dispatch overhead) or abandoning per-directory granularity, neither clearly better.
- **Import-list completeness is unfixable by construction.** A lane agent that misses an import produces a false negative indistinguishable from "no such import" — judgment-based detection cannot self-verify omission the way a parser would. Accepted, not solved; `check_cycles.py` is explicitly a best-effort secondary signal, never advertised as complete.
- **Secret redaction is a heuristic, not a guarantee** (keyword/AWS-key-shape/entropy matching at the two text-emission points: lane answers, report assembly) — will have false negatives. State this plainly in the skill's output, same as any heuristic redaction.
- **Flat-repo chunking fallback has no real semantic meaning even after mitigation.** Extension-based chunking is marginally better than alphabetical but still isn't a real module boundary. The report MUST carry the mandatory disclosure line when this fallback fires ("findings below use arbitrary chunks, not real module boundaries — reduced confidence") — this is a structural limitation of avoiding parser-based detection, not a bug to chase further; doing so would mean reintroducing the static-analysis mechanism this design specifically avoids.
- **Synthesis is pairwise-framed** — a genuine 3-way contradiction (three lanes, tangled claims) may be partially missed. Documented, not solved; narrow trigger.

## First Step

1. Write the 5-question lane prompt template and the GROUP banding/filtering logic into `skills/project-audit/SKILL.md`.
2. Write `scripts/check_cycles.py` + `scripts/tests/test_check_cycles.py` (new, stdlib-only).
3. Dry-run by hand against this repo's own `skills/` tree (as 3 of 5 ideators independently suggested as their own first step) before writing the synthesis-prompt's corroboration/adjudication logic in full.
4. Delete `skills/architecting/` entirely.
5. Update the 5 cross-references from Phase 1: `using-agent-sdlc-skills/SKILL.md` (Gate 2 routing), `diagnose/SKILL.md` + `diagnose/references/phases.md` (delegation target), `README.md` (skill catalog row), `parallel-brainstorming/SKILL.md` (description's passing mention) — all `architecting` → `project-audit`.
6. Run `npm test` (covers `tests/validate-plugin.test.mjs`) before handoff.
