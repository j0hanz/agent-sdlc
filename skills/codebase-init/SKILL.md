---
name: codebase-init
description: "Generate, audit, or onboard a repo with a fresh AGENTS.md (wired to CLAUDE.md/GEMINI.md). Trigger on 'init agents.md', 'generate AGENTS.md', 'onboard this repo', 'setup AGENTS.md', 'this repo has no agent instructions'."
disable-model-invocation: true
user-invocable: true
allowed-tools: Bash(python *) Bash(python3 *)
---

# codebase-init

Maintain lean, high-signal `AGENTS.md` (symlinked to `CLAUDE.md`/`GEMINI.md`). Optimized for agent context injection, not human reading. Target: < 100 lines.

## Phase 1: Environment Discovery

Run all analysis subcommands to ground instructions in project reality:

```bash
python <skill-dir>/scripts/run.py analyze-all . --max-depth 2
```

This sequentially runs `analyze-env` (package manager, test runner, linter, monorepo structure), `find-dependencies` (installed dependency directories), and `scan-structure` (directory tree, respecting `.gitignore`).

**Manual Fallback:** If the script can't run, inspect `package.json`, `tsconfig.json`, `pytest.ini`, `.github/workflows/`, and root structure directly. Never hallucinate tools.

## Phase 1.5: Architecture Mapping

**Required:** Read `references/phase-1.5-architecture.md` to select the project-specific template and detect tech stack patterns.

## Required Sections

| Section            | Requirement                                                               |
| :----------------- | :------------------------------------------------------------------------ |
| **H1 Header**      | `# Agent Instructions` or `# <Project> Agent Instructions`                |
| **Description**    | Single sentence immediately following H1.                                 |
| **Toolchain**       | Package manager and critical environment commands.                        |
| **File Commands**  | Table of file-targeted typecheck/lint/test commands.                      |
| **Conventions**    | 3-7 specific, actionable bullets (e.g., "Use AppError for all rethrows"). |
| **Attribution**    | `Co-Authored-By: <Model Name>` at end of file.                            |
