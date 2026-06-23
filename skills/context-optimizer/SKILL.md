---
name: context-optimizer
description: "Optimizes, compresses, and prunes active conversation context and memory logs to avoid token limits and context drift. Use this skill when managing long development sessions, handling large file modifications, or resolving memory drift in nested subagent workflows. Prefer manual session resetting (running /clear directly) if no critical task progress state needs to be preserved via a rolling summary. Trigger on: 'optimize context', 'compress context', 'prune memory', 'reduce tokens', 'context size too large', 'out of tokens', 'compact context', 'clear history', 'cleanup context'."
disable-model-invocation: false
---

# context-optimizer

Optimize and prune active conversation context to prevent token limits and context drift. This skill provides systematic diagnostics to sniff context bloat (unignored directories, lockfiles, large source files) and pruning strategies (JSON compaction, traceback log filtering, and rolling summaries) to preserve agent reasoning efficiency in long developer sessions.

## Process Flow

```
Phase 1: Diagnose (Run scripts/diagnose_context_bloat.py and /context)
  -> Phase 2: Select Strategy (Choose KV compaction, log filtering, or rolling summary)
  -> Phase 3: Action (Run scripts/prune_context.py or specify StartLine/EndLine slices)
  -> Phase 4: Reset & Reload (Save summary, run /clear, reload summary)
```

## Step 1: Diagnose Context Bloat

1. Run the workspace sniffer to check for large files, lockfiles, and git workspace dirtiness:
   ```bash
   python "$CLAUDE_PLUGIN_ROOT/skills/context-optimizer/scripts/diagnose_context_bloat.py"
   ```
2. Run the Claude Code command `/context` to inspect current token consumption and identify if the history, tool outputs, or system prompt is bloating.
3. Check if instruction stubs (`CLAUDE.md` and `GEMINI.md`) are properly configured to link to `AGENTS.md` instead of copying the full rules text.

## Step 2: Select and Apply Strategy

Choose and execute one of these optimization strategies based on the diagnostic results:

- **Strategy A: KV Compaction**:
  For structured data lists (configs, metadata, JSON files), pipe the JSON data through the pruning utility to convert it into a flat Key-Value format. See [references/context-pruning-guidelines.md](references/context-pruning-guidelines.md) for Markdown-KV formatting syntax.
  ```bash
  python "$CLAUDE_PLUGIN_ROOT/skills/context-optimizer/scripts/prune_context.py" --to-kv < data.json
  ```
- **Strategy B: Log & Exception Truncation**:
  For long test failures, command stdout, or compiler stack traces, pipe them through the log filter to retain only failure headers and relevant exception frames. See [references/context-pruning-guidelines.md](references/context-pruning-guidelines.md) for log truncation details.
  ```bash
  python "$CLAUDE_PLUGIN_ROOT/skills/context-optimizer/scripts/prune_context.py" --logs < test_output.log
  ```
- **Strategy C: Line Slicing**:
  Avoid reading large files in full. Run `grep_search` to find line numbers, then load only the required lines using the `StartLine` and `EndLine` parameters of `view_file`.
- **Strategy D: Subagent Isolation**:
  Delegate complex exploratory tasks or code reviews to a separate subagent so its execution history does not bloat the main conversation context.

## Step 3: Clear and Resume

For long sessions where conversation history is bloated:

1. Write a flat Key-Value status of the current task using the summary flag. Details on formatting are located in [references/context-pruning-guidelines.md](references/context-pruning-guidelines.md).
   ```bash
   python "$CLAUDE_PLUGIN_ROOT/skills/context-optimizer/scripts/prune_context.py" --summary --timestamp "$(date -Iseconds)" --done "completed items" --blocking "blockers" --next-step "next actions" --decisions "key decisions"
   ```
2. Inform the user you are clearing history and need them to type 'resume'.
3. Run the Claude Code `/clear` command to reset the context window.
4. Reload the rolling summary file (`.claude/rolling_summary.md`) to continue the task with a pruned context.

## NEVER

- **NEVER** view files larger than 300 lines without specifying `StartLine` and `EndLine`. **WHY:** Loading complete large files floods the conversation context with unnecessary code. **FIX:** Run `grep_search` first, then use `StartLine` and `EndLine` to load a small slice.
- **NEVER** run `/clear` in the Claude Code CLI without writing a rolling summary first. **WHY:** Clearing the chat history deletes the agent's progress memory and requirements state. **FIX:** Run `scripts/prune_context.py --summary` to write current progress to `.claude/rolling_summary.md` first.
- **NEVER** paste verbose test/build stdout or JSON data structures. **WHY:** Floods context with passing reports and syntax characters (brackets, quotes). **FIX:** Run `scripts/prune_context.py --logs` or `--to-kv` to compact the data.

**next skills:**

- `planning`: Trigger if the pruned context reveals major specification gaps that need re-planning.
- `using-agent-dev-skills`: Return to the main router once context is optimized.
