# The Craft of Agent System Prompts

System prompts MUST be written in strict `markdown-kv` format. This structure minimizes conversational noise, token waste, and enforces tight behavioral boundaries, especially critical in multi-agent and TDD orchestrations.

## The `markdown-kv` Skeleton

```markdown
Role: <One-sentence job description>
Objective: <Core goal>
Procedure:

- Step 1: <Imperative action>
- Step 2: <Imperative action>
- Fallback: <Action on timeout/failure>
  Boundaries:
- Limit 1: <Strict "Do not..." constraint>
- Limit 2: <Strict "Do not..." constraint>
  Output:
- Format: <e.g., Markdown List, JSON schema>
- Requirements: <What must be returned>
```

## The Handoff Contract

The parent agent or thread only ever sees the agent's **final message**. Intermediate tool calls and reasoning are discarded.

- **Design Output Explicitly:** The final message must contain all required context (file paths, line numbers, exact findings). Vague output destroys delegation value.
- **Self-Containment:** Subagents receive NO parent context. The invocation prompt and system prompt must provide all needed state.

## Boundaries and Fences

- **Prompt Fences:** Use strict rules (e.g., `Limit: Do not modify files. Do not commit.`).
- **Config Fences:** Strip capabilities. A reviewer with no `Edit`/`Write` tools mathematically cannot rewrite code.

## Multi-Agent Orchestration & Workflows

When designing subagents that operate within a larger workflow (e.g., test-driven governance, scatter-gather coordination):

- **State Passing:** Define exactly how outputs from Agent A feed into Agent B.
- **Scatter-Gather:** Define timeout handling and partial result collection. Ensure agents fail gracefully.
- **Saga/Compensation:** If a downstream task fails, define rollback instructions for previous steps.
- **Checkpoints:** Establish validation gates before moving states.

## Anti-Patterns

- **Aspirational Language:** "You should try to..." -> Use "Procedure: - Step 1: Do X."
- **Conversational Filler:** "You are a helpful assistant..." -> Use "Role: Security Reviewer."
- **No Output Contract:** Assuming the agent will "summarize".
- **Kitchen Sink:** Combining three unrelated jobs into one agent.
