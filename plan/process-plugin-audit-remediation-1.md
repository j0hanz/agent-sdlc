# Plugin Audit Remediation Plan

**Purpose**: process
**Component**: plugin-audit-remediation
**Version**: 1
**Created**: 2026-06-01
**Source**: Plugin-validator agent audit — 2 critical issues, 7 warnings

---

## Goal

Resolve all 9 findings from the plugin audit to bring the agent-dev plugin to a clean pass against the Claude Code plugin spec. Two critical issues break runtime behaviour (missing skill, invalid color values). Seven warnings are spec violations or stale documentation that cause confusion or silent failures. All changes are low-risk, surgical edits — no architectural changes required.

---

## Requirements & Constraints

| ID      | Statement                                                                                             |
| ------- | ----------------------------------------------------------------------------------------------------- |
| REQ-001 | All 2 critical findings must be resolved before marking plan complete                                 |
| REQ-002 | All 7 warnings must be resolved or explicitly accepted with documented reasoning                      |
| REQ-003 | No existing skill, agent, or hook behaviour may be broken by the changes                              |
| CON-001 | The `code-review` SKILL.md must match the frontmatter conventions of all other skills in the repo     |
| CON-002 | Agent color values must be from the spec-allowed set: `red blue green yellow purple orange pink cyan` |
| PAT-001 | File edits follow narrowest-change principle — remove/replace only the offending field or line        |

---

## Current Context

```
c:\agent-dev\
├── .claude-plugin\plugin.json         # manifest — contains redundant hooks/monitors keys (W5)
├── agents\
│   ├── coder.md                       # color: '#198754'  → must be green (Critical-2)
│   ├── detective.md                   # color: '#dc3545'  → must be red   (Critical-2)
│   ├── documenter.md                  # color: '#0d6efd'  → must be blue + has skill_composition (Critical-2, W2)
│   └── explorer.md                    # color: '#8B4513'  → must be orange (Critical-2)
├── commands\
│   └── detective.md                   # has undocumented name: field (W1)
├── hooks\
│   └── hooks.json                     # UserPromptSubmit + Stop missing matcher (W3)
├── monitors\
│   └── monitors.json                  # telemetry-watcher missing shell: powershell (W4)
├── output-styles\
│   └── agent-dev.md                   # unrecognised directory; unknown runtime effect (W7)
├── skills\                            # 18 skills — code-review/ is ABSENT (Critical-1)
│   └── (18 existing skill directories)
└── README.md                          # Skills: 19 (wrong), Agents: 2 (wrong), Commands: 11 (wrong) (W6)
```

Actual counts (verified by directory listing):

- Skills: **18** (not 19)
- Agents: **4** — `coder`, `detective`, `documenter`, `explorer`
- Commands: **8** — `brainstorm`, `coder`, `detective`, `diagram`, `explore`, `fix`, `hook`, `pr`

---

## Implementation Phases

### Phase 1 — Critical Fixes

#### TASK-001 — Create `skills/code-review/SKILL.md`

```
Depends on: none
Files: skills/code-review/SKILL.md (to be created)
Action: Create the file with valid frontmatter (name, description, argument-hint) and a minimal
        body describing code review responsibilities, so that the three skills that gate on it
        (delivery-manager, verification-before-completion, using-agent-dev) have a real target.
        Model the frontmatter on skills/refactor/SKILL.md for consistency.
        The skill body should: (1) state its purpose, (2) define what a passing review looks like,
        (3) list the checks it performs (correctness bugs, security, reuse/simplification).
Validate: Glob pattern skills/code-review/SKILL.md returns one result
Expected result: File exists and contains valid YAML frontmatter with name: code-review
```

#### TASK-002 — Fix agent color values (4 files)

```
Depends on: none
Files: agents/coder.md, agents/detective.md, agents/documenter.md, agents/explorer.md
Action: In each file replace the hex color value with the closest spec-allowed named color:
          agents/coder.md      color: '#198754'  →  color: green
          agents/detective.md  color: '#dc3545'  →  color: red
          agents/documenter.md color: '#0d6efd'  →  color: blue
          agents/explorer.md   color: '#8B4513'  →  color: orange
        Edit only the color: line — no other changes.
Validate: Grep pattern "color: '#" in agents/ returns zero matches
Expected result: All four agent files use named colors; no hex strings remain
```

---

### Phase 2 — Frontmatter Cleanups

#### TASK-003 — Remove undocumented `name:` from `commands/detective.md`

```
Depends on: none
Files: commands/detective.md
Action: Delete the line `name: detective` from the YAML frontmatter block (lines 1-5).
        The command name is derived from the filename; the field is silently ignored and adds noise.
        Keep description:, argument-hint:, and the body unchanged.
Validate: Grep pattern "^name:" in commands/detective.md returns zero matches
Expected result: Frontmatter contains only description and argument-hint fields
```

#### TASK-004 — Remove undocumented `skill_composition:` from `agents/documenter.md`

```
Depends on: none
Files: agents/documenter.md
Action: Delete the line `skill_composition: declined` from the frontmatter (currently line 32).
        This field is not in the documented subagent frontmatter spec; it is silently ignored.
        All other frontmatter fields and the body remain unchanged.
Validate: Grep pattern "skill_composition" in agents/documenter.md returns zero matches
Expected result: documenter.md frontmatter contains no undocumented fields
```

---

### Phase 3 — Hook & Monitor Fixes

#### TASK-005 — Document intentional matcherless hooks in `hooks/hooks.json`

```
Depends on: none
Files: hooks/hooks.json
Action: The UserPromptSubmit and Stop hook groups intentionally have no matcher (fires on every
        event). This is valid per spec but the audit flagged it as a performance concern.
        Add a JSON comment-equivalent by prepending a "_comment" sibling key to each matcherless
        group explaining the intent:
          UserPromptSubmit group: add "_comment": "Intentional: no matcher — nudge fires on all prompts; handler checks config flag internally"
          Stop group:             add "_comment": "Intentional: no matcher — debug scan runs on every stop event"
        Note: JSON does not support comments natively; use "_comment" as a convention key
        (the Claude Code runtime ignores unknown keys in hook group objects).
Validate: Grep pattern "_comment" in hooks/hooks.json returns 2 matches
Expected result: Both matcherless groups have a _comment key documenting the intent
```

#### TASK-006 — Add `shell: powershell` to `telemetry-watcher` in `monitors/monitors.json`

```
Depends on: none
Files: monitors/monitors.json
Action: In the telemetry-watcher entry (currently the first object in the array),
        add the field "shell": "powershell" immediately after the "command" field.
        This is required because the command uses Get-Content (PowerShell syntax) and
        the monitor will fail silently on non-Windows environments without this declaration.
Validate: Grep pattern '"shell"' in monitors/monitors.json returns 1 match inside telemetry-watcher
Expected result: monitors.json telemetry-watcher object contains "shell": "powershell"
```

---

### Phase 4 — Manifest Cleanup

#### TASK-007 — Evaluate and retain `hooks`/`experimental.monitors` keys in `plugin.json`

```
Depends on: none
Files: .claude-plugin/plugin.json
Action: The audit flagged "hooks" and "experimental.monitors" manifest keys as potentially
        redundant with auto-discovery. However, auto-discovery is only guaranteed in the latest
        spec version; explicit paths ensure compatibility with older Claude Code installations.
        DECISION: RETAIN both keys as-is. Add an inline _comment key documenting why:
          "_comment_hooks": "Explicit path retained for pre-auto-discovery Claude Code compatibility"
          "_comment_monitors": "experimental.monitors retained; auto-discovery not guaranteed across all versions"
        Place both comment keys at the top level alongside existing keys.
Validate: Grep pattern "_comment_hooks" in .claude-plugin/plugin.json returns 1 match
Expected result: plugin.json retains hooks/experimental.monitors and has inline documentation of intent
```

---

### Phase 5 — Documentation Fixes

#### TASK-008 — Update `README.md` Highlights table with correct counts and command names

```
Depends on: none
Files: README.md
Action: In the Highlights table (lines 20-27), update three rows:
        Skills row:   Count 19 → 18
        Agents row:   Count 2 → 4; Purpose "coder · explorer" → "coder · detective · documenter · explorer"
        Commands row: Count 11 → 8; list "/brainstorm, /coder, /detective, /diagram, /explore, /fix, /hook, /pr"
        Also update the Project Structure section line `skills/ — 19 skill definitions` → 18.
        Remove the Usage table rows for commands that don't exist:
          /plan, /new, /eval, /check, /deliver, /artifact-review, /debug, /test, /refactor, /docs, /welcome
        Replace with the 8 actual commands and their descriptions (derive from the command file bodies).
Validate: Grep pattern "19" in README.md returns zero matches in the component count context;
          Grep "Agents" row returns "4"; command list contains exactly the 8 real command names
Expected result: README accurately reflects 18 skills, 4 agents, 8 commands with correct names
```

#### TASK-009 — Audit `output-styles/agent-dev.md` and migrate to a documented location

```
Depends on: none
Files: output-styles/agent-dev.md
Action: The output-styles/ directory is not a recognised plugin component directory per the spec.
        The file has non-standard frontmatter keys (force-for-plugin, keep-coding-instructions)
        that have no documented runtime effect.
        Steps:
        1. Read output-styles/agent-dev.md to understand its full content.
        2. DECISION: Move the content into the SessionStart hook handler as injected context,
           OR retain the directory as a documented convention with a note in AGENTS.md.
        3. If retaining: add a note to AGENTS.md under a new "Output Styles" section explaining
           that output-styles/ is a plugin-local convention (not a Claude Code spec directory),
           that agent-dev.md is loaded by the SessionStart session hook as injected style context,
           and that the frontmatter keys are hints consumed by the runner, not by Claude Code itself.
        4. If migrating: move file content into hooks/handlers/session.mjs as a style-injection
           string emitted via SessionStart, and delete the output-styles/ directory.
        Recommended: Retain + document (lower risk, preserves existing hook wiring if any).
Validate: AGENTS.md contains an "Output Styles" section explaining the convention
Expected result: output-styles/ status is explicitly documented; no longer an undocumented mystery
```

---

## Testing & Validation

After all tasks complete, run the following checks in order:

```bash
# 1. Verify code-review skill exists and has valid frontmatter
node -e "const fs=require('fs'); const c=fs.readFileSync('skills/code-review/SKILL.md','utf8'); console.assert(c.includes('name: code-review'),'Missing name field'); console.log('SKILL.md OK')"

# 2. Confirm no hex colors remain in agents/
grep -r "color: '#" agents/ && echo "FAIL: hex colors remain" || echo "PASS: no hex colors"

# 3. Confirm no undocumented frontmatter in commands/detective.md
grep "^name:" commands/detective.md && echo "FAIL: name field still present" || echo "PASS"

# 4. Confirm skill_composition removed from documenter
grep "skill_composition" agents/documenter.md && echo "FAIL: field still present" || echo "PASS"

# 5. Confirm shell declaration in monitors
grep '"shell"' monitors/monitors.json && echo "PASS: shell declared" || echo "FAIL"

# 6. Confirm README counts
grep -E "^\| Skills\s+\|\s+18" README.md && echo "PASS: skills count" || echo "FAIL"
grep -E "^\| Agents\s+\|\s+4"  README.md && echo "PASS: agents count" || echo "FAIL"
grep -E "^\| Commands\s+\|\s+8" README.md && echo "PASS: commands count" || echo "FAIL"
```

---

## Acceptance Criteria

| #   | Criterion                                                                         | Verified by             |
| --- | --------------------------------------------------------------------------------- | ----------------------- |
| 1   | `skills/code-review/SKILL.md` exists with valid frontmatter                       | Glob + Grep             |
| 2   | All 4 agent files use named colors from the spec-allowed set                      | Grep (no `#` in color:) |
| 3   | `commands/detective.md` frontmatter has no `name:` field                          | Grep                    |
| 4   | `agents/documenter.md` has no `skill_composition:` field                          | Grep                    |
| 5   | Matcherless hooks in `hooks.json` have documented intent via `_comment` keys      | Grep                    |
| 6   | `monitors/monitors.json` `telemetry-watcher` has `"shell": "powershell"`          | Grep                    |
| 7   | `plugin.json` retains hooks/monitors keys with inline compatibility documentation | Grep                    |
| 8   | `README.md` shows 18 skills, 4 agents, 8 commands with correct command names      | Grep                    |
| 9   | `output-styles/` is documented in `AGENTS.md` or migrated to a spec-valid home    | Read AGENTS.md          |

---

## Effort Estimate

| Task      | Type            | Estimate    |
| --------- | --------------- | ----------- |
| TASK-001  | New file        | 20 min      |
| TASK-002  | 4 × line edit   | 5 min       |
| TASK-003  | 1 × line delete | 2 min       |
| TASK-004  | 1 × line delete | 2 min       |
| TASK-005  | 2 × key insert  | 5 min       |
| TASK-006  | 1 × key insert  | 2 min       |
| TASK-007  | 2 × key insert  | 5 min       |
| TASK-008  | Table rewrite   | 15 min      |
| TASK-009  | Read + write    | 15 min      |
| **Total** | —               | **~70 min** |

---

## Rollback Strategy

All changes are additive (new skill file) or surgical edits to markdown/JSON. Git diff is the rollback:

```bash
git diff HEAD               # review all changes
git checkout -- <file>      # revert a single file
git checkout -- .           # revert all if needed
```

No migrations, no dependency changes, no schema changes. Safe to revert any task independently.
