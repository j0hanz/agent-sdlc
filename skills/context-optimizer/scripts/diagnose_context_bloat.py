#!/usr/bin/env python3
"""
Workspace Context Bloat Diagnostics script.
Checks file lengths, unignored heavy directories, lockfiles, and instruction stub consistency.
"""

import os
from pathlib import Path

BLOAT_LINE_LIMIT = 500
BLOAT_SIZE_LIMIT_KB = 50
HEAVY_DIRS = {".venv", "venv", "node_modules", "dist", "build", ".next", "target"}
LOCKFILES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "poetry.lock",
    "go.sum",
}


def parse_gitignore(root: Path) -> set[str]:
    ignore_patterns = set()
    gitignore_path = root / ".gitignore"
    if gitignore_path.exists():
        for line in gitignore_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                ignore_patterns.add(line)
    return ignore_patterns


def scan_files(root: Path, ignores: set[str]):
    large_files = []
    unignored_heavy_dirs = []

    # Check for unignored heavy directories
    for d in HEAVY_DIRS:
        dir_path = root / d
        if dir_path.is_dir() and d not in ignores:
            unignored_heavy_dirs.append(d)

    # Recursive file walk with size/LOC checks
    for dirpath, dirnames, filenames in os.walk(root):
        # Exclude dot folders and heavy dirs in-place
        dirnames[:] = [
            d for d in dirnames if d not in HEAVY_DIRS and not d.startswith(".")
        ]

        for f in filenames:
            file_path = Path(dirpath) / f
            try:
                # Exclude lockfiles from LOC check, but flag them
                if f in LOCKFILES:
                    large_files.append(
                        (file_path, "Lockfile", file_path.stat().st_size)
                    )
                    continue

                size = file_path.stat().st_size
                size_kb = size / 1024

                if size_kb > BLOAT_SIZE_LIMIT_KB:
                    large_files.append((file_path, f"{size_kb:.1f} KB", size))
                    continue

                # LOC check for text files
                if file_path.suffix in {
                    ".py",
                    ".ts",
                    ".js",
                    ".tsx",
                    ".jsx",
                    ".go",
                    ".rs",
                    ".java",
                    ".cpp",
                    ".h",
                    ".cs",
                }:
                    lines = file_path.read_text(
                        encoding="utf-8", errors="ignore"
                    ).splitlines()
                    if len(lines) > BLOAT_LINE_LIMIT:
                        large_files.append((file_path, f"{len(lines)} lines", size))
            except OSError:
                continue

    return large_files, unignored_heavy_dirs


def check_instruction_stubs(root: Path) -> list[str]:
    warnings = []
    stub_files = ["CLAUDE.md", "GEMINI.md", ".cursorrules"]
    for stub in stub_files:
        path = root / stub
        if path.exists():
            content = path.read_text(encoding="utf-8").strip()
            # If the stub contains more than a redirect line, raise a warning
            if len(content.splitlines()) > 5 or "AGENTS.md" not in content:
                warnings.append(
                    f"`{stub}` does not appear to be a single-line stub referencing `AGENTS.md` (length={len(content.splitlines())} lines)."
                )
    return warnings


def main():
    root = Path(os.getcwd())
    ignores = parse_gitignore(root)
    large_files, unignored_dirs = scan_files(root, ignores)
    stub_warnings = check_instruction_stubs(root)

    print("## Workspace Context Bloat Diagnostics")
    print(f"Project Root: {root}\n")

    issues_found = False

    if unignored_dirs:
        print("### [WARNING] Unignored Heavy Directories:")
        for d in unignored_dirs:
            print(
                f"- `{d}/` exists but is not ignored in `.gitignore`. Indexing/searching may bloat context."
            )
        issues_found = True
        print()

    if large_files:
        print("### [WARNING] Bloat Candidates (Exceeding limits):")
        # Sort by size descending
        large_files.sort(key=lambda x: x[2], reverse=True)
        for path, reason, size in large_files:
            try:
                rel_path = path.relative_to(root)
            except ValueError:
                rel_path = path
            est_tokens = int(size / 3.7)
            print(
                f"- `{rel_path}` ({reason}) → Estimated: ~{est_tokens} tokens if read."
            )
        issues_found = True
        print()

    if stub_warnings:
        print("### [WARNING] Instruction Stub Warnings:")
        for warn in stub_warnings:
            print(f"- {warn}")
        issues_found = True
        print()

    if not issues_found:
        print("PASS: No bloating files or directories detected.")


if __name__ == "__main__":
    main()
