# project-init Monorepo Directory-Scoped Merges Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable the `project-init` skill to generate lightweight, directory-scoped `AGENTS.md` files for monorepo packages that inherit the root's Hard Rules and pass custom lint checks.

**Architecture:** Add a `--package <rel_path>` command-line option to `init.py generate` that filters claims by evidence path. Render-level switches omit Hard Rules/Attribution sections and write a `project-init:package-scoped` marker instead. Linter logic is updated to bypass Hard Rules and Commit Attribution checks for files carrying this marker.

**Tech Stack:** Python 3 (standard library only)

## Global Constraints

- Follow ESM conventions in JS and absolute/relative containment in python commands.
- Run tests on the touched files only (using pytest).
- No new external python libraries — rely entirely on stdlib.
- Commits must use the attribution trailer: `Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>`

---

### Task 1: Package Claim Filtering and CLI Option

**Files:**
- Modify: `skills/project-init/scripts/init.py`
- Modify: `skills/project-init/tests/test_init.py`

**Interfaces:**
- Consumes: `claims.json` format containing `evidence.path` for each claim.
- Produces: Command-line option `--package` that limits `winners` to a specified directory prefix.

- [ ] **Step 1: Write the failing test**

Add this test to `skills/project-init/tests/test_init.py`:
```python
def test_claims_filtering_by_package_prefix(tmp_path: Path):
    """Claims are filtered to only keep those matching the specified package prefix."""
    (tmp_path / "packages").mkdir()
    (tmp_path / "packages" / "api").mkdir()
    (tmp_path / "packages" / "frontend").mkdir()
    (tmp_path / "packages" / "api" / "package.json").write_text('{"name": "api"}\n')
    (tmp_path / "packages" / "frontend" / "package.json").write_text('{"name": "frontend"}\n')
    (tmp_path / "README.md").write_text("root readme\n")

    claims = [
        _claim("pm", "pnpm", "packages/api/package.json", match="api", confidence=0.9),
        _claim("cmd.build", "pnpm build", "packages/api/package.json", match="api", confidence=0.9),
        _claim("cmd.test", "vitest", "packages/frontend/package.json", match="frontend", confidence=0.8),
        _claim("conv.git", "ESM only", "README.md", confidence=0.5),
    ]

    # Run merge_claims as normal
    winners, _ = init.merge_claims(claims, tmp_path)
    
    # Simulate filtering logic
    package_path = "packages/api"
    prefix = package_path.strip().replace("\\", "/").rstrip("/") + "/"
    filtered = {
        k: v for k, v in winners.items()
        if v.evidence.path.replace("\\", "/").startswith(prefix)
    }

    assert "pm" in filtered
    assert "cmd.build" in filtered
    assert "cmd.test" not in filtered
    assert "conv.git" not in filtered
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest skills/project-init/tests/test_init.py::test_claims_filtering_by_package_prefix -v`
Expected: FAIL (or missing because the parser/CLI validation doesn't support package filter flag yet).

- [ ] **Step 3: Write minimal implementation**

Modify `skills/project-init/scripts/init.py:628-644` in the `_build_parser` function:
```python
    gen.add_argument("--claims", type=Path, required=True, help="JSON array of claims.")
    gen.add_argument(
        "--commit", required=True, choices=sorted(HARD_RULES_TEXT["commit"])
    )
    gen.add_argument(
        "--maturity", required=True, choices=sorted(HARD_RULES_TEXT["maturity"])
    )
    gen.add_argument(
        "--testing", required=True, choices=sorted(HARD_RULES_TEXT["testing"])
    )
    gen.add_argument("--ci", required=True, choices=sorted(HARD_RULES_TEXT["ci"]))
    gen.add_argument("--purpose", default=None)
    gen.add_argument(
        "--model", default=None, help="Active model name for the attribution trailer."
    )
    gen.add_argument(
        "--package", default=None, help="Relative path to package directory (e.g. 'packages/api')."
    )
    gen.add_argument("--out", type=Path, default=None)
```

And update `_cmd_generate` in `skills/project-init/scripts/init.py:548-597`:
```python
    winners, dropped = merge_claims(raws, root)
    if args.purpose:
        winners["purpose"] = Claim("purpose", _sanitize_value(args.purpose), 4, 1.0)

    if args.package:
        pkg_prefix = args.package.strip().replace("\\", "/").rstrip("/") + "/"
        winners = {
            k: v for k, v in winners.items()
            if v.evidence.path.replace("\\", "/").startswith(pkg_prefix)
        }

    winners, trimmed = _trim_to_budget(winners)
    dropped += trimmed
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest skills/project-init/tests/test_init.py::test_claims_filtering_by_package_prefix -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skills/project-init/scripts/init.py skills/project-init/tests/test_init.py
git commit -m "feat: add CLI --package option and claims filtering by path prefix" -m "Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 2: Package-scoped Header and Rule Omission in Render

**Files:**
- Modify: `skills/project-init/scripts/init.py`
- Modify: `skills/project-init/tests/test_init.py`

- [ ] **Step 1: Write the failing test**

Add this test to `skills/project-init/tests/test_init.py`:
```python
def test_render_package_scoped_agents_md(tmp_path: Path):
    """Rendering with package parameter excludes hard rules/attribution and adds package-scoped header."""
    winners = {
        "purpose": init.Claim("purpose", "test pkg purpose", 4, 1.0),
        "stack": init.Claim("stack", "Go 1.22", 4, 1.0),
    }
    out = init.render_agents_md(
        winners, "minimal", "development", "always", "local-only", package="packages/api"
    )
    
    assert "# Agent Instructions: packages/api" in out
    assert "purpose: test pkg purpose" in out
    assert "stack: Go 1.22" in out
    assert "## Hard Rules" not in out
    assert "## Commit Attribution" not in out
    assert "project-init:hard-rules" not in out
    assert "project-init:package-scoped packages/api" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest skills/project-init/tests/test_init.py::test_render_package_scoped_agents_md -v`
Expected: FAIL (signature error or missing package-scoped elements)

- [ ] **Step 3: Write minimal implementation**

Modify `render_agents_md` signature and body in `skills/project-init/scripts/init.py:338-390`:
```python
def render_agents_md(
    winners: dict[str, Claim],
    commit: str,
    maturity: str,
    testing: str,
    ci: str,
    model: str = "<Model Name>",
    package: str | None = None,
) -> str:
    """Assemble the markdown-kv AGENTS.md from verified winners + survey answers."""
    purpose = (
        winners["purpose"].value
        if "purpose" in winners
        else "<one sentence — what this repo does>"
    )
    
    if package:
        pkg_normalized = package.strip().replace("\\", "/").rstrip("/")
        lines = [
            f"# Agent Instructions: {pkg_normalized}",
            "",
            f"purpose: {purpose}"
        ]
    else:
        lines = ["# Agent Instructions", "", f"purpose: {purpose}"]

    if "stack" in winners:
        lines.append(f"stack: {winners['stack'].value}")
    
    if package:
        pkg_normalized = package.strip().replace("\\", "/").rstrip("/")
        lines += [
            "",
            f"<!-- project-init:package-scoped {pkg_normalized} -->",
        ]
    else:
        lines += [
            "",
            "## Hard Rules",
            "",
            f"commit: {HARD_RULES_TEXT['commit'][commit]}",
            f"maturity: {HARD_RULES_TEXT['maturity'][maturity]}",
            f"testing: {HARD_RULES_TEXT['testing'][testing]}",
            f"ci: {HARD_RULES_TEXT['ci'][ci]}",
            "",
            f"<!-- project-init:hard-rules {MARKER_VERSION} commit={commit} maturity={maturity} testing={testing} ci={ci} -->",
        ]

    def section(title: str, keys: list[str]) -> None:
        rows = [(k, winners[k].value) for k in keys if k in winners]
        if not rows:
            return
        lines.extend(["", f"## {title}", ""])
        for k, v in rows:
            label = k.split(".", 1)[1] if "." in k else k
            lines.append(f"{label}: {v}")

    cmd_keys = ["pm"] + sorted(k for k in winners if k.startswith("cmd."))
    section("Package Manager", cmd_keys)
    section("Dependency Locations", sorted(k for k in winners if k.startswith("dep.")))
    section("Key Conventions", sorted(k for k in winners if k.startswith("conv.")))

    file_keys = sorted(k for k in winners if k.startswith("file."))
    if file_keys:
        lines.extend(
            ["", "## File-Scoped Commands", "", "| Task | Command |", "| --- | --- |"]
        )
        for k in file_keys:
            lines.append(f"| {k.split('.', 1)[1]} | `{winners[k].value}` |")

    if not package:
        lines.extend(["", "## Commit Attribution", "", f"Co-Authored-By: {model}", ""])
    return "\n".join(lines)
```

Also, update `_cmd_generate` to pass `package=args.package` to `render_agents_md`:
```python
    content = render_agents_md(
        winners,
        args.commit,
        args.maturity,
        args.testing,
        args.ci,
        model=args.model or "<Model Name>",
        package=args.package,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest skills/project-init/tests/test_init.py::test_render_package_scoped_agents_md -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skills/project-init/scripts/init.py skills/project-init/tests/test_init.py
git commit -m "feat: render package-scoped header and exclude hard rules/attribution" -m "Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 3: Linter Updates for Package-scoped AGENTS.md

**Files:**
- Modify: `skills/project-init/scripts/init.py`
- Modify: `skills/project-init/tests/test_init.py`

- [ ] **Step 1: Write the failing test**

Add this test to `skills/project-init/tests/test_init.py`:
```python
def test_linter_passes_package_scoped_agents_md():
    """Linter passes a valid package-scoped AGENTS.md and fails if the marker is missing."""
    valid_pkg = "# Agent Instructions: packages/api\n\npurpose: api subproject\n\n<!-- project-init:package-scoped packages/api -->\n"
    fails = init.lint_agents_md(valid_pkg)
    assert not fails

    missing_marker = "# Agent Instructions: packages/api\n\npurpose: api subproject\n"
    fails = init.lint_agents_md(missing_marker)
    assert any("marker" in f for f in fails)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest skills/project-init/tests/test_init.py::test_linter_passes_package_scoped_agents_md -v`
Expected: FAIL (missing hard rules or missing commit attribution errors)

- [ ] **Step 3: Write minimal implementation**

Modify `lint_agents_md` in `skills/project-init/scripts/init.py:427-459`:
```python
_PKG_MARKER_RE = re.compile(
    r"<!--\s*project-init:package-scoped\s+(\S+)\s*-->"
)

def lint_agents_md(content: str) -> list[str]:
    """Return a list of FAIL messages; empty list == valid."""
    fails: list[str] = []
    lines = content.lstrip("\ufeff").splitlines()
    if len(lines) > MAX_LINES:
        fails.append(f"{len(lines)} lines exceeds the {MAX_LINES}-line budget")
    if not lines or not lines[0].startswith("# "):
        fails.append("must start with an H1 header")

    is_package_scoped = bool(_PKG_MARKER_RE.search(content))

    if is_package_scoped:
        if not _PKG_MARKER_RE.search(content):
            fails.append("missing/malformed project-init:package-scoped marker")
    else:
        if "## Hard Rules" not in content:
            fails.append('missing "## Hard Rules" section')
        if not _MARKER_RE.search(content):
            fails.append("missing/malformed project-init:hard-rules v1 marker")
        if "Co-Authored-By:" not in content:
            fails.append('missing "Co-Authored-By:" attribution')
        if "## Commit Attribution" not in content:
            fails.append('missing "## Commit Attribution" section')

    if "<Model Name>" in content:
        fails.append('unresolved "<Model Name>" placeholder')

    in_code = False
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code or s.startswith("<!--"):
            continue
        if _TODO_RE.search(line):
            fails.append(f'unresolved TODO (line {i}): "{s}"')
        if _FILLER_RE.search(line):
            fails.append(f'filler text (line {i}): "{s}"')
    return fails
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest skills/project-init/tests/test_init.py::test_linter_passes_package_scoped_agents_md -v`
Expected: PASS

Also run the full test suite to check for regressions:
Run: `python -m pytest skills/project-init/tests`
Expected: PASS all tests.

- [ ] **Step 5: Commit**

```bash
git add skills/project-init/scripts/init.py skills/project-init/tests/test_init.py
git commit -m "feat: bypass hard rules and attribution linting for package-scoped AGENTS.md" -m "Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 4: SKILL.md Orchestration Documentation Updates

**Files:**
- Modify: `skills/project-init/SKILL.md`

- [ ] **Step 1: Write updates to SKILL.md**

Update the Phase 2 and Phase 3 descriptions in `skills/project-init/SKILL.md`.

In Phase 2:
```markdown
## Phase 2: Check and Preview

1. **Combine:** Put all facts from Phase 1 into one file called `claims.json`.
2. **Test Root:** Run `init.py generate --claims claims.json --commit <c> --maturity <m> --testing <t> --ci <ci>` (Do not use `--out`. Just print it to the screen).
3. **Test Packages (Monorepos):** If the prescan results show `is_monorepo == true`, run the generate preview for each package folder `<pkg>` in `packages`:
   `init.py generate --claims claims.json --package <pkg> --commit <c> --maturity <m> --testing <t> --ci <ci>`
4. **Filter:** The script will keep only proven facts and drop bad ones.
5. **Show the User:** Show the user the draft of `AGENTS.md` (root and packages) and the list of dropped facts. If there is an error, fix the inputs or rerun the bad agent. Do not save yet.
```

In Phase 3:
```markdown
## Phase 3: Ask and Save

1. **Protect Old Files:** If root `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md` already exist, or if any package-level `<pkg>/AGENTS.md` exists, show them to the user, make a backup (`.bak`), and **ask for explicit permission** before replacing them.
2. **Save Root:** Run `init.py generate --claims claims.json ... --model "<active model name>" --out AGENTS.md`.
3. **Save Packages (Monorepos):** For each package folder `<pkg>`, run:
   `init.py generate --claims claims.json --package <pkg> --model "<active model name>" --out <pkg>/AGENTS.md`.
4. **Link Files:** Run `init.py wire AGENTS.md CLAUDE.md GEMINI.md` (root level redirect stubs only).
5. **Test Root File:** Run `init.py lint AGENTS.md`. It must pass.
6. **Test Package Files (Monorepos):** For each package folder `<pkg>`, run `init.py lint <pkg>/AGENTS.md`. They must pass.
7. **Report to User:** Tell the user what files were saved, how many lines they have, and remind them of the facts that were dropped.
```

- [ ] **Step 2: Commit**

```bash
git add skills/project-init/SKILL.md
git commit -m "docs: document monorepo package generate and lint steps in SKILL.md" -m "Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```
