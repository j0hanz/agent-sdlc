# Managed Agents — API-Callable Agents

A **Managed Agent** is invoked by your code through the Agent API, outside any interactive session. Used for webhooks, cron jobs, or backend endpoints.

## At a Glance

- **Invoked by:** External code (not Claude).
- **Scope:** One independent run per API call.
- **Config:** System prompt (in `markdown-kv` format), Tools, Skills, MCP Servers, Permission Policy.

## Lifecycle

- `agents.create`: Register agent definition.
- `agents.update`: Modify existing agent. **WARNING: Replaces arrays wholesale.**
- `agents.invoke`: Run the agent once.

## The Wholesale-Replace Trap

`agents.update` replaces array fields (`tools`, `skills`, `mcp_servers`) wholesale. If you omit an existing item, it is silently deleted.
**Always:** Read current config -> Build new arrays -> Diff -> Update.

## Permission Policy

- **Default:** `always_ask`.
- **Escalation:** Reserve `always_allow` for a single, pinned, fully-trusted MCP server you control. Never apply `always_allow` broadly across an `agent_toolset`.

## Testing

Test thoroughly before wiring into an application:

1. Invoke directly with test inputs (including refusal cases).
2. Verify output contract stability (your calling code depends on it).
3. Ensure termination boundaries are respected.
