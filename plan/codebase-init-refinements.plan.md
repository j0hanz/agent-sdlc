# codebase-init-refinements

Spec: [codebase-init-refinements.specs.md](file:///C:/agent-dev/plan/codebase-init-refinements.specs.md)

## Goal

Add a CI/CD Automation survey question and configuration parameter, and dynamically generate language-specific Key Conventions to eliminate placeholder TODOs during codebase initialization.

## PHASE-001: Implementation

### TASK-001: Implement REQ-001 (Survey & References Update)

Depends on: none
Files: [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md), [hard-rules.md](file:///C:/agent-dev/skills/codebase-init/references/hard-rules.md)
Symbols: none
Satisfies: REQ-001
Action: Update [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md) Phase 0 Action to prompt for a 4th question on CI/CD Automation (`github-actions` / `gitlab-ci` / `local-only`) in the single consolidated `AskUserQuestion` call. Update [hard-rules.md](file:///C:/agent-dev/skills/codebase-init/references/hard-rules.md) to document the new CI/CD question, options, marker parameters, and recommendation heuristics based on directory layout (e.g., recommend `github-actions` if `.github/workflows` exists).
Validate: Run `python skills/codebase-init/scripts/run.py validate-skills` to check skill file structure.
Expected result: The skill validation command prints PASS.

### TASK-002: Implement REQ-006 (CI/CD Environment Discovery Detection Logic)

Depends on: TASK-001
Files: [run.py](file:///C:/agent-dev/skills/codebase-init/scripts/run.py)
Symbols: [ProjectEnvironment](file:///C:/agent-dev/skills/codebase-init/scripts/run.py#L248), [analyze_project_env](file:///C:/agent-dev/skills/codebase-init/scripts/run.py#L395)
Satisfies: REQ-006
Action: Add `ci_provider: str = "Unknown"` to the [ProjectEnvironment](file:///C:/agent-dev/skills/codebase-init/scripts/run.py#L248) DTO. Update [analyze_project_env](file:///C:/agent-dev/skills/codebase-init/scripts/run.py#L395) to scan for `.github/workflows/` containing files (returning `"github-actions"`), `.gitlab-ci.yml` (returning `"gitlab-ci"`), or fallback to `"local-only"`.
Validate: Run `python skills/codebase-init/scripts/run.py analyze-env .` and verify detection does not crash.
Expected result: Environment discovery successfully returns ProjectEnvironment containing the detected CI provider.

### TASK-003: Implement REQ-007 & REQ-008 (CLI Printing of CI Provider)

Depends on: TASK-002
Files: [run.py](file:///C:/agent-dev/skills/codebase-init/scripts/run.py)
Symbols: [main](file:///C:/agent-dev/skills/codebase-init/scripts/run.py#L1147)
Satisfies: REQ-007, REQ-008
Action: Update [main](file:///C:/agent-dev/skills/codebase-init/scripts/run.py#L1147) subcommand handling for `analyze-env` and `analyze-all` to print the detected CI/CD provider (e.g. `CI/CD Automation: local-only`).
Validate: Run `python skills/codebase-init/scripts/run.py analyze-env .` and `python skills/codebase-init/scripts/run.py analyze-all .`
Expected result: Both commands output a line displaying the detected CI provider.


### TASK-004: Implement REQ-002 (CLI Scaffold with CI option/defaults)

Depends on: TASK-003
Files: [run.py](file:///C:/agent-dev/skills/codebase-init/scripts/run.py)
Symbols: [Config.HARD_RULES_TEXT](file:///C:/agent-dev/skills/codebase-init/scripts/run.py#L192), [render_hard_rules_marker](file:///C:/agent-dev/skills/codebase-init/scripts/run.py#L572), [_HARD_RULES_MARKER_RE](file:///C:/agent-dev/skills/codebase-init/scripts/run.py#L567), [_setup_parser](file:///C:/agent-dev/skills/codebase-init/scripts/run.py#L1025), [render_agents_md_skeleton](file:///C:/agent-dev/skills/codebase-init/scripts/run.py#L582)
Satisfies: REQ-002
Action: Update [run.py](file:///C:/agent-dev/skills/codebase-init/scripts/run.py):
  1. Add `ci` choices to `Config.HARD_RULES_TEXT` with user-friendly descriptions.
  2. Add `--ci` option to `scaffold-agents-md` in `_setup_parser` (optional, choices: `github-actions`, `gitlab-ci`, `local-only`).
  3. If `--ci` is omitted during execution in `main`, run `analyze_project_env` to detect it.
  4. Update `_HARD_RULES_MARKER_RE` regex pattern to support `ci=\S+`.
  5. Update `render_hard_rules_marker` to accept and render `ci` attribute.
  6. Update `render_agents_md_skeleton` to take `ci`, write it under Hard Rules, and output the updated marker.
Validate: Run `python skills/codebase-init/scripts/run.py scaffold-agents-md --language node --purpose "Test" --commit relaxed --maturity development --testing touched-files --ci github-actions`
Expected result: Output contains `ci: CI runs on GitHub Actions` and `<!-- codebase-init:hard-rules v1 commit=relaxed maturity=development testing=touched-files ci=github-actions -->`.

### TASK-005: Implement REQ-003 (Conventions scaffold for all 7 languages)

Depends on: TASK-004
Files: [run.py](file:///C:/agent-dev/skills/codebase-init/scripts/run.py), [guide.md](file:///C:/agent-dev/skills/codebase-init/references/guide.md)
Symbols: [render_agents_md_skeleton](file:///C:/agent-dev/skills/codebase-init/scripts/run.py#L582)
Satisfies: REQ-003
Action: Define dynamic, language-specific conventions in `Config.LANGUAGE_DEFAULTS` for all 7 languages (`node`, `python`, `go`, `rust`, `java`, `dotnet`, `bun`). Update `render_agents_md_skeleton` to insert these conventions under the `## Key Conventions` section, completely replacing the static `# TODO` checklist. Update [guide.md](file:///C:/agent-dev/skills/codebase-init/references/guide.md) to document this change.
Validate: `python skills/codebase-init/scripts/run.py scaffold-agents-md --language python --purpose "Acceptance"`
Expected result: Output for all 7 languages contains language-specific rules and no generic TODO checkboxes.

### TASK-006: Implement REQ-004 & REQ-005 (Linter Validation checking CI & HTML comments)

Depends on: TASK-005
Files: [run.py](file:///C:/agent-dev/skills/codebase-init/scripts/run.py)
Symbols: [validate_agents_md_file](file:///C:/agent-dev/skills/codebase-init/scripts/run.py#L667)
Satisfies: REQ-004, REQ-005
Action: Update [validate_agents_md_file](file:///C:/agent-dev/skills/codebase-init/scripts/run.py#L667):
  1. Validate that the marker contains the `ci` attribute. Warn if missing/malformed.
  2. Modify the TODO/filler checks so they inspect the entire line (including HTML comments) using a case-insensitive regex for `\bTODO\b` rather than skipping line analysis for lines starting with `<!--`.
Validate: Create a temporary markdown file with `<!-- TODO: fix -->` and run lint-agents-md on it.
Expected result: The linter flags the TODO warning/error inside the comment.

### TASK-007: Update Unit Tests and Evals

Depends on: TASK-006
Files: [test_run.py](file:///C:/agent-dev/skills/codebase-init/tests/test_run.py), [evals.json](file:///C:/agent-dev/skills/codebase-init/evals/evals.json)
Symbols: none
Satisfies: REQ-004, REQ-005
Action: Update [test_run.py](file:///C:/agent-dev/skills/codebase-init/tests/test_run.py) to provide the `ci` parameter in skeleton rendering tests and mock file checks. Add test cases for TODO detection in HTML comments, missing/malformed CI parameters in marker comments, and automated CI detection. Update [evals.json](file:///C:/agent-dev/skills/codebase-init/evals/evals.json).
Validate: Run `python -m pytest skills/codebase-init/tests/test_run.py`
Expected result: All tests pass successfully.

## PHASE-END: Acceptance

### TASK-008: Final Acceptance Verification

Depends on: TASK-007
Files: none
Symbols: none
Satisfies: AC-001, AC-002, AC-003, AC-004, AC-005
Action: Perform verification commands:
  1. Verify Phase 0 survey consolidation by testing the survey prompt setup.
  2. Scaffold a Node project instructions file to `TEST_AGENTS.md` using the updated `--ci` flag, then validate the file via `lint-agents-md`.
  3. Run scaffold command without `--ci` and check that the marker matches the local CI setup.
  4. Validate a test file containing `<!-- TODO: placeholder -->` and check that it reports a lint issue.
Validate: `python skills/codebase-init/scripts/run.py scaffold-agents-md --language node --purpose "Acceptance" --commit strict --maturity production --testing always --ci github-actions --out TEST_AGENTS.md && python skills/codebase-init/scripts/run.py lint-agents-md TEST_AGENTS.md && echo "<!-- TODO: verify this -->" >> TEST_AGENTS.md && python skills/codebase-init/scripts/run.py lint-agents-md TEST_AGENTS.md; del TEST_AGENTS.md`
Expected result: All acceptance criteria verification checks pass.

