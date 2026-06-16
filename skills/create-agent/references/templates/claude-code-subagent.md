---
name: my-agent
description: >
  Trigger condition. Pushy + concrete. 
  Example: "Use proactively when X happens."
tools: Read, Grep, Glob
model: sonnet
# effort: high
# permissionMode: default
# maxTurns: 20
# skills: [name-of-skill]
# isolation: worktree
# background: true
# memory: project
---

Role: <One-sentence definition. You are X. You do Y so that Z.>
Objective: <Specific goal of the execution>

Procedure:

- Step 1: <Concrete imperative instruction>
- Step 2: <Concrete imperative instruction>
- Fallback: <Instructions for handling timeouts or tool failures>

Boundaries:

- Fences: <Do not write, commit, etc.>
- Scope: <Stay within target directories>

Output:

- Format: <e.g., strict JSON, markdown table>
- Content: <Exact schema of the final message>
