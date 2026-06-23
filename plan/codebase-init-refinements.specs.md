# codebase-init-refinements

## 1. Goal

- One sentence: Add a CI/CD Automation survey question and configuration parameter, and dynamically generate language-specific Key Conventions to eliminate placeholder TODOs during codebase initialization.
- Completion signal: The Python unit test suite passes and a scaffolded `AGENTS.md` containing the `ci` parameter passes verification.

## 2. Requirements

- `REQ-001`: The Phase 0 Policy Survey MUST prompt the user for **CI/CD Automation** (`github-actions` / `gitlab-ci` / `local-only`) via a single consolidated `AskUserQuestion` call alongside the other three policy questions.
- `REQ-002`: The generated `AGENTS.md` file MUST contain a `codebase-init:hard-rules` marker comment on version `v1` which includes the new `ci` attribute (e.g. `<!-- codebase-init:hard-rules v1 commit=strict maturity=production testing=always ci=github-actions -->`).
- `REQ-003`: The `scaffold-agents-md` command MUST dynamically generate 3-7 language-appropriate `## Key Conventions` based on the detected project environment instead of a static generic TODO checklist.
- `REQ-004`: The `validate_agents_md_file` function in `scripts/run.py` MUST validate that the marker comment includes the `ci` parameter.
- `REQ-005`: The `validate_agents_md_file` function in `scripts/run.py` MUST verify that the file contains no unresolved TODO comments (including those inside HTML comments).
- `REQ-006`: The Phase 1 Environment Discovery MUST detect the CI/CD provider configuration (`github-actions` if `.github/` folder contains workflows, `gitlab-ci` if `.gitlab-ci.yml` exists, otherwise `local-only`).
- `REQ-007`: The `analyze-env` command MUST display the detected CI/CD provider in the output.
- `REQ-008`: The `analyze-all` command MUST display the detected CI/CD provider in the output.

## 3. Constraints

- `CON-001`: The Policy Survey MUST NOT include any questions related to Code Style or Linter Preference.
- `CON-002`: The generated `AGENTS.md` file MUST NOT exceed 100 lines.

## 4. Interfaces

The system exposes the following interfaces:

### Scaffolding CLI Option

**Input:**
- `--ci` (type: string, optional): One of `github-actions`, `gitlab-ci`, `local-only`.

**Output:**
- Generated `AGENTS.md` file containing the `ci` marker parameter and language-appropriate key conventions.

**Errors:**
- Unrecognized or malformed values for the `--ci` option.

### Policy Survey Prompt

**Input:**
- Consolidation of 4 questions (Commit policy, Project maturity, Testing rigor, CI/CD automation) using `AskUserQuestion`.

**Output:**
- User selections passed to scaffold generator script.

## 5. Context

- Files: [skills/codebase-init/SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md), [skills/codebase-init/references/hard-rules.md](file:///C:/agent-dev/skills/codebase-init/references/hard-rules.md), [skills/codebase-init/scripts/run.py](file:///C:/agent-dev/skills/codebase-init/scripts/run.py), [skills/codebase-init/tests/test_run.py](file:///C:/agent-dev/skills/codebase-init/tests/test_run.py), [skills/codebase-init/evals/evals.json](file:///C:/agent-dev/skills/codebase-init/evals/evals.json)
- Current behavior: Scaffolding asks 3 questions and outputs a generic conventions TODO checklist. Validation looks for `codebase-init:hard-rules v1` containing only `commit`, `maturity`, and `testing`.
- Conventions: `scripts/run.py` contains linter and rendering utility functions written in standard Python.
- CI/CD Recommendation Heuristics:
  - Recommend `github-actions` if `.github/workflows/` directory contains files;
  - Recommend `gitlab-ci` if `.gitlab-ci.yml` file exists;
  - Otherwise recommend `local-only`.

## 6. Acceptance Criteria & Validation

- `AC-001`: Scaffolding a Node.js repository creates an `AGENTS.md` containing dynamic Node-specific conventions and a `ci` marker parameter.
- `VAL-001`: `python -m pytest skills/codebase-init/tests/test_run.py` runs and all tests pass.
- `AC-002`: The lint-agents-md command warns if a file has missing/malformed `ci` markers or unresolved TODO placeholders.
- `VAL-002`: Running `python skills/codebase-init/scripts/run.py lint-agents-md C:\agent-dev\plan\codebase-init-refinements.specs.md` fails if there are unresolved TODOs.
- `AC-003`: Interactive Phase 0 policy survey asks for CI/CD automation preference in the AskUserQuestion payload.
- `VAL-003`: Verify that the Phase 0 survey prompt triggers 4 questions in order.
- `AC-004`: When scaffolding a project without `--ci`, it automatically detects the CI provider (e.g. `github-actions` if `.github/` folder exists) and generates the correct marker.
- `VAL-004`: Run scaffold command without `--ci` and check that the marker matches the local CI setup.
- `AC-005`: The linter flags lowercase or uppercase `TODO` comments even when wrapped in HTML comments (`<!-- TODO: ... -->`).
- `VAL-005`: Validate a test file containing `<!-- TODO: placeholder -->` and check that it reports a lint issue.

## 7. Examples & Edge Cases

**Positive example:**
```markdown
# Agent Instructions

purpose: Web API
commit: relaxed
maturity: development
testing: touched-files
ci: github-actions

<!-- codebase-init:hard-rules v1 commit=relaxed maturity=development testing=touched-files ci=github-actions -->
```

**Edge cases:**
- `--ci` omitted: Defaults to the CI/CD detected during Environment Discovery (`github-actions` if `.github/` exists, `gitlab-ci` if `.gitlab-ci.yml` exists, otherwise `local-only`).

