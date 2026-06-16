# Implementer Subagent Prompt Template

Use this template when dispatching the `coder` subagent in Phase 1.
Fill in every `[FIELD]` with task-specific content before dispatching.
Remove all template annotations — the subagent receives only the filled prompt.

---

## Dispatch Template

```
SCOPE:
  Files/dirs IN scope:   [list exact file paths or directories this task touches]
  Files/dirs OUT of scope: [list what must NOT be modified]

OBJECTIVE:
  [Paste the full task spec verbatim. One concrete outcome. Do not paraphrase.]

CONTEXT:
  Codebase root: [absolute path]
  Relevant existing code:
    [file:line — function signature, type definition, or pattern this task extends]
    [file:line — test file pattern to follow]
    [file:line — any interface or contract this task must satisfy]
  Last commit: [git hash] — use this as your baseline for diff and self-review.

CONSTRAINTS:
  - Implement exactly what the spec states. Nothing more, nothing less.
  - Write tests before or alongside implementation (red → green).
  - Do NOT restructure code outside this task's file scope.
  - Do NOT add "nice to have" features not in the spec.
  - Commit when complete: git commit -m "Task [N]: [task title]"
  - [Add any task-specific constraints here]

OUTPUT:
  Return a single final message with this exact structure:

  STATUS: [DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT]

  SUMMARY:
  [2-4 sentences: what was built, which functions/classes were added, how tests verify it]

  FILES_CHANGED:
  [file path] — [what changed]
  [file path] — [what changed]

  COMMIT: [git hash]

  CONCERNS: [if DONE_WITH_CONCERNS: describe the ambiguity or risk. Otherwise: none.]
  BLOCKER: [if BLOCKED: exact blocker — missing requirement, conflicting constraint, etc.]
  QUESTION: [if NEEDS_CONTEXT: one specific clarifying question.]
```

---

## Guidance for the Dispatcher

- **Read before writing:** The implementer must read all files in scope before making any edits.
- **Ask before assuming:** If the spec is ambiguous on a design decision with multiple valid approaches, the implementer returns `NEEDS_CONTEXT` rather than guessing.
- **One task per subagent:** Never bundle two tasks into one implementer call.
- **Worktree isolation:** Always dispatch with `isolation: "worktree"` when the task writes files, to prevent collisions with the parent working tree.
- **Model selection:** Use `model: "sonnet"` (default) for standard implementation. Use `model: "opus"` only for tasks involving security-sensitive logic, complex algorithmic design, or adversarial edge cases.
