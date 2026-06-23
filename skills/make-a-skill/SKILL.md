---
name: make-a-skill
description: "Guides the creation, scaffolding, and structural auditing of Claude Code skills to ensure they follow best practices (500-line rule, progressive disclosure). Use this to generate skill skeletons or to validate that an existing skill's structure, placeholders, and references are correct. Not for qualitative content review or critique. Trigger on: 'make a skill', 'build a skill', 'create a skill', 'scaffold a skill', 'new skill', 'make-a-skill', 'validate this skill', 'lint this skill', 'validate skill structure'."
disable-model-invocation: false
---

# make-a-skill

Scaffold a new skill from a template, draft its body, then validate it before calling it done.

**Entry point:** this skill is reached directly from skill-authoring requests ("make a skill", "validate this skill"), not through `using-agent-dev-skills`'s Gate 0-4 flow — that router operates on the target repo's code, not on the plugin's own `skills/` directory. See `using-agent-dev-skills`'s NEVER list (it routes all skill authoring here).

## Process Flow

```
0. Name Collision Check
  -- exists -------> Exists-Gate (AskUserQuestion)
                       -- Continue ---> 1.5 Pattern Pick
                       -- Overwrite --> 1. Survey + Scaffold (--force)
                       -- Rename -----> back to 0
  -- no collision -> 1. Survey + Scaffold
1. Survey + Scaffold (AskUserQuestion once, then scaffold_skill.py)
  -> 1.5 Pattern Pick (AskUserQuestion)
  -> 2. Draft Body (fill placeholders, leave description)
  -> 3. Validate (validate_skill.py)
       -- errors? yes --> back to 2. Draft Body
       -- errors? no  --> 4. Write Real Description + revalidate -> Done
```

## Step 0: Check for a name collision

Before scaffolding, check whether `<name>/SKILL.md` already exists (`.claude/skills/<name>` or `skills/<name>`). If it doesn't, skip straight to Step 1. If it does, ask before touching anything:

`AskUserQuestion`: _"A skill named '<name>' already exists."_ — options: "Continue drafting it (Recommended)" / "Overwrite with fresh template" / "Pick a different name".

- **Continue** — skip Step 1's scaffold entirely; go straight to Step 1.5 using what's already on disk.
- **Overwrite** — proceed to Step 1 with `--force`.
- **Pick a different name** — ask for a new name, restart at Step 0.

## Step 1: Resource survey, then scaffold

Ask one batched question — a single `AskUserQuestion` call, never split into multiple round-trips:

- **Q1 (multiSelect):** "Which bundled resources does this skill need?" — options: `scripts/` / `references/` / `evals/` / `none`. Mark whichever the task description implies as "(Recommended)" — e.g. repeated/deterministic code → `scripts/`; large lookup tables or schemas → `references/`; explicit eval coverage requested → `evals/`.
- **Q2 (single-select, conditional):** only ask "Where should this skill live?" — ".claude/skills/ (project-level, Recommended)" / "skills/ (this plugin's own directory)" — when genuinely ambiguous (both directories exist at repo root, or neither does). If only one exists, or the request already says "plugin skill", decide silently and skip this question.

(`AskUserQuestion` always exposes an "Other" escape hatch regardless of how the question is worded — there's no way to suppress it, unlike a CLI flag set.)

```bash
python "$CLAUDE_PLUGIN_ROOT/skills/make-a-skill/scripts/scaffold_skill.py" <name> [--scripts] [--references] [--evals] [--dir skills] [--force]
```

`<name>` must be lowercase kebab-case (e.g. `make-a-skill`). Flags are the direct output of the survey answers above — never guessed. Every section, including `description`, is written as a `{{FILL: ...}}` placeholder except `name`.

## Step 1.5: Pick a pattern

Ask (single-select): "Which structural pattern fits this skill?" — options:

- **Process** (Recommended if multi-step) — phased workflow, ~200 lines, checkpoints, medium freedom.
- **Tool** — decision trees, low freedom, ~300 lines, for precise/fragile format operations.
- **Mindset** — ~50 lines, thinking patterns over technique, high freedom, for creative/taste tasks.
- **Navigation** — minimal routing to sub-files, ~30 lines, for several distinct sub-scenarios.

Mark whichever the task description most resembles as "(Recommended)". The answer shapes Step 2: a Process pick keeps a numbered Process Flow diagram; a Mindset pick means deleting that section in favor of a short, NEVER-heavy body; a Navigation pick means the body is mostly links to sub-files.

## Step 2: Draft the body

Fill in every `{{FILL: ...}}` placeholder **except** `description` — leave that one alone for now. Ground each section in a real, concrete procedure; don't write generic advice the agent already knows (see `references/checklist.md` §Calibration). If the skill doesn't need a branching Process Flow diagram, delete that section entirely rather than leaving a trivial one.

## Step 3: Validate (structural pass)

```bash
python "$CLAUDE_PLUGIN_ROOT/skills/make-a-skill/scripts/validate_skill.py" <name>
```

Fix every `[X]` ERROR before continuing — these include leftover `{{FILL` placeholders, a `name`/directory mismatch, and dangling links to `references/`/`scripts/`/`evals/` files that don't exist. Review `[!]` WARNINGs (vague adjectives, passive voice, an unreferenced sibling file, a too-long body with no `references/` split) but they don't block progress on their own — use judgment.

`<name>` resolves relative to the current working directory (it checks `.claude/skills/<name>` and `skills/<name>`), unlike the script invocations above which use the `$CLAUDE_PLUGIN_ROOT`-prefixed absolute path — run validation from the repo root the skill actually lives in.

## Step 4: Write the real description, then revalidate

Only now, with the body finished, replace the placeholder `description`. It must be third person, state what the skill is for, name the sibling skill to use instead when this one doesn't apply, and end with an explicit `Trigger on: 'phrase one', 'phrase two', ...` clause listing literal phrases a user might type (see `references/checklist.md` §Description). Writing it last, instead of up front, means it describes what the skill actually became rather than what it was guessed to be.

Re-run Step 3's command. It must report `VALID (0 error(s), ...)` before the skill is considered done. Zero errors is mandatory; outstanding warnings are a judgment call.

## NEVER

- **NEVER** write the real `description` before the body is drafted. **WHY:** the two-pass split exists so the description reflects what the skill actually does, not a guess made before any of it was written. **FIX:** leave the `{{FILL` placeholder through Step 3; only do Step 4 after Step 3 passes.
- **NEVER** skip a repo's own plugin-wide validation (e.g. this plugin's own `npm run validate`) just because `validate_skill.py` passed. **WHY:** `validate_skill.py` checks one skill in isolation; a repo-wide validator may check things this can't see (plugin manifest, cross-skill consistency). **FIX:** run both if the target repo has one.
- **NEVER** hand-write a SKILL.md skeleton instead of running `scaffold_skill.py`. **WHY:** hand-copying drifts from the placeholder-marker convention `validate_skill.py` depends on to catch unfinished sections. **FIX:** always scaffold first.
- **NEVER** pass `--scripts`/`--references`/`--evals` from agent guesswork. **WHY:** a guessed flag set stubs directories the skill won't use, or omits ones it will. **FIX:** run the Step 1 resource survey and pass exactly what the answer says.
- **NEVER** let `scaffold_skill.py`'s `FileExistsError` reach the user as a raw stack trace. **WHY:** a name collision is a normal, recoverable case, not a failure. **FIX:** run the Step 0 Exists-Gate before scaffolding.

**next skills:**

- `architecting`: If drafting the body surfaces a structural question — where shared logic should live across two skills, or a circular reference between two `references/` files. This skill is otherwise a leaf step in skill authoring; there's no required next skill on the happy path.
