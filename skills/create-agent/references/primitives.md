# Agent Primitives — Choosing and Composing

The ways to run agent work, compared on the axes that drive the choice.

## At a glance

| Primitive         | Invoked by               | Context         | Best for                                              |
| :---------------- | :----------------------- | :-------------- | :---------------------------------------------------- |
| **Subagent**      | Claude, via `Agent` tool | Fresh, isolated | Delegated side tasks; narrow reusable roles           |
| **Agent team**    | Parent agent             | Per-teammate    | Parallel independent tasks                            |
| **Agent view**    | You, from dashboard      | Persistent      | Steered background jobs                               |
| **Workflow**      | JS script                | Script-held     | Complex multi-agent orchestration, state sharing, TDD |
| **Managed Agent** | External API             | One per call    | API-callable service                                  |

## Advanced Orchestration (Workflows & Multi-Agent Coordination)

For advanced scenarios, workflows and specialized multi-agent coordination are essential. They provide structural guarantees that simple subagents cannot:

- **Scatter-Gather:** Distribute queries to parallel agents, implement timeout handling so slow responders don't block the aggregator, and collect partial results.
- **Saga Pattern / Distributed Transactions:** Orchestrate logic across semi-independent actors. Setup checkpoints and explicit compensation logic (e.g., if step C fails, how does step A rollback?).
- **State Machines:** Manage multiple explicit states with strict validation before transitions.
- **TDD Governance:** Enforce Red-Green-Refactor cycles comprehensively across multiple test phases.

## Subagent

- **Use when:** A task would flood the main thread context, or it needs a completely clean slate.
- **Limitations:** Re-derives context cold. One parent, one child. No shared state without manual passing.

## Agent Team

- **Use when:** Several independent hypotheses or parallel reviews need to run simultaneously.
- **Limitations:** Sequential dependent tasks fail here; a simple chain or workflow is better.

## Managed Agent

- **Use when:** You need to call an agent from a webhook or backend service.
- **Update Trap:** `agents.update` replaces array fields wholesale. Read, diff, then update to avoid silently dropping tools.

## Composition

- **Skills:** Preload using `skills: [name]` to inject capabilities natively.
- **Hooks:** Attach `SubagentStop` lifecycle guards to enforce determinism.
