---
name: agents-maintainer
description: "Create, audit, refactor, or trim AGENTS.md, CLAUDE.md, GEMINI.md, and onboarding guides. Trigger on 'agent docs', 'instructions', 'onboard me', 'understand this repo', 'setup AGENTS.md', 'this file is too long', 'trim CLAUDE.md', 'improve agent instructions', 'add conventions', 'update instructions file', or when the user shares an existing AGENTS.md/CLAUDE.md and asks to improve, review, or clean it up."
disable-model-invocation: true
user-invocable: true
allowed-tools: Bash(python *) Bash(python3 *)
---

# agents-maintainer

Maintain lean, high-signal `AGENTS.md` (symlinked to `CLAUDE.md`/`GEMINI.md`). Optimized for agent context injection, not human reading. Target: < 100 lines.

## Phase 1: Environment Discovery

Run all analysis subcommands to ground instructions in project reality:

```bash
python <skill-dir>/scripts/run.py analyze-all . --max-depth 2
```

**Manual Fallback:** Inspect `package.json`, `tsconfig.json`, `pytest.ini`, `.github/workflows/`, and root structure. Never hallucinate tools.

## Phase 1.5: Architecture Mapping

**Required:** Read `references/phase-1.5-architecture.md` to select the project-specific template and detect tech stack patterns.

## Phase 2: High-Density Drafting

Compose `AGENTS.md` using these strict constraints:

- **Format:** Headers, bullets, tables, code blocks only. Zero prose paragraphs.
- **Reference, Don't Embed:** Point to `CONTRIBUTING.md` or `docs/` for deep detail.
- **File-Scoped Commands:** Always provide `tsc --noEmit src/file.ts` over full builds.
- **Dependency Locations:** Explicitly state where `.venv` or `node_modules` live.
- **Instruction Budget:** Focus on the top 150-200 instructions. Link the rest.

## Phase 3: Validate & Wire

1. **Lint:** `python <skill-dir>/scripts/run.py lint-agents-md AGENTS.md`
2. **Semantic Review:** Dispatch `general-purpose` agent to check Signal Density, Convention Specificity, and Command Completeness.
3. **Manual Check:** Verify every command works and links exist.
4. **Wire:** `python <skill-dir>/scripts/run.py wire-agents AGENTS.md CLAUDE.md GEMINI.md`

## Required Sections

| Section           | Requirement                                                               |
| :---------------- | :------------------------------------------------------------------------ |
| **H1 Header**     | `# Agent Instructions` or `# <Project> Agent Instructions`                |
| **Description**   | Single sentence immediately following H1.                                 |
| **Toolchain**     | Package manager and critical environment commands.                        |
| **File Commands** | Table of file-targeted typecheck/lint/test commands.                      |
| **Conventions**   | 3-7 specific, actionable bullets (e.g., "Use AppError for all rethrows"). |
| **Attribution**   | `Co-Authored-By: <Model Name>` at end of file.                            |

## Writing Conventions (Actionable vs. Vague)

- ❌ "Use descriptive names" / "Follow best practices"
- ✅ "API handlers end in `.handler.ts`" / "Constructor injection only; no field injection"
- **Structure:** [What: Pattern] [Where: Context] [Why: Reason]

## Anti-Patterns (NEVER)

- No "Welcome to..." intros.
- No restating linter rules (e.g., "Use 2 spaces").
- No listing skill/plugin names the agent auto-discovers.
- No generic advice ("test thoroughly").
