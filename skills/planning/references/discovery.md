# Discovery Guide

Use Claude's native **Grep** and **Glob** tools to resolve file paths and code
symbols before writing `Files:`/`Symbols:` fields in plan tasks.

## Usage

- Find files matching a pattern: Glob with pattern `src/**/*.ts` (or `src/**/*.{ts,tsx}`)
- Find a symbol by name: Grep with pattern `parseConfig`, `output_mode: "content"`, `-n: true` for line numbers
- Regex symbol search (e.g. all React hooks): Grep with pattern `^export (function|const) use[A-Z]`
- Combined search: run Glob to narrow files, then Grep within that scope

## Output (paste directly into plan tasks)

Grep/Glob return raw paths and line numbers — format them yourself as markdown
links before pasting into `Files:`/`Symbols:`:

```markdown
- [src/auth/jwt.ts](src/auth/jwt.ts)
- [signToken](src/auth/jwt.ts#L24) — `src/auth/jwt.ts:24`
- [validateToken](src/auth/jwt.ts#L41) — `src/auth/jwt.ts:41`
```

Copy the link blocks directly into `Files:` and `Symbols:` fields. Never fabricate `#L` anchors — only use line numbers Grep actually reported.

## Rules

1. Run discovery before writing task fields — never guess paths
2. Copy line anchors exactly as reported by Grep
3. For new files (not yet created): mark as `[UNVERIFIED: path/to/new-file.ts](UNVERIFIED)` and note which task creates it
4. For cross-repo paths discovery can't reach: mark as `[UNVERIFIED: path/to/file.ts](UNVERIFIED)` and document the assumption inline (which repo, why it's not discoverable here)

## When discovery returns no matches

| Situation                    | Action                                            |
| ---------------------------- | ------------------------------------------------- |
| Pattern returns 0 results    | Simplify glob; check the directory exists         |
| Symbol not found             | Try broader pattern; verify the symbol name       |
| New file created during plan | Mark UNVERIFIED; resolve after creating task runs |
| Cross-repo path needed       | Mark UNVERIFIED; document the assumption inline   |
