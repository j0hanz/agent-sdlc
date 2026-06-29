# Claude Code Plugins Reference

A **plugin** is a self-contained directory that extends Claude Code with skills, agents, hooks, MCP servers, LSP servers, monitors, and themes.

---

## Components

### Skills

Shortcuts (`/name`) that Claude or users can invoke.

**Default locations:** `skills/<name>/SKILL.md` or `commands/<name>.md`
**Single-skill shorthand:** A `SKILL.md` at the plugin root loads as one skill (v2.1.142+). Set `name` in frontmatter to pin the invocation name; otherwise the install directory name is used.

```
skills/
├── pdf-processor/
│   ├── SKILL.md
│   └── scripts/
└── code-reviewer/
    └── SKILL.md
```

---

### Agents

Specialized subagents Claude can invoke automatically.

**Default location:** `agents/<name>.md`

**Frontmatter fields:**

| Field             | Description                          |
| ----------------- | ------------------------------------ |
| `name`            | Agent identifier                     |
| `description`     | When Claude should invoke this agent |
| `model`           | Model to use (e.g. `sonnet`)         |
| `effort`          | `low` \| `medium` \| `high`          |
| `maxTurns`        | Max agentic turns                    |
| `tools`           | Allowed tools                        |
| `disallowedTools` | Blocked tools                        |
| `skills`          | Skills available to this agent       |
| `memory`          | Memory configuration                 |
| `background`      | Background context                   |
| `isolation`       | `"worktree"` only                    |

> `hooks`, `mcpServers`, and `permissionMode` are not supported in plugin-shipped agents.

---

### Hooks

Event handlers that respond to Claude Code lifecycle events.

**Default location:** `hooks/hooks.json` or inline in `plugin.json`

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{ "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/scripts/format.sh" }]
      }
    ]
  }
}
```

**Hook types:** `command` · `http` · `mcp_tool` · `prompt` · `agent`

**Events:**

| Event                 | Fires when                                                           |
| --------------------- | -------------------------------------------------------------------- |
| `SessionStart`        | Session begins or resumes                                            |
| `Setup`               | `--init-only` / `--init` / `--maintenance` mode                      |
| `UserPromptSubmit`    | Prompt submitted, before Claude processes it                         |
| `UserPromptExpansion` | User command expands; can block expansion                            |
| `PreToolUse`          | Before tool call; can block it                                       |
| `PermissionRequest`   | Permission dialog appears                                            |
| `PermissionDenied`    | Tool denied by auto classifier; return `{retry:true}` to allow retry |
| `PostToolUse`         | After successful tool call                                           |
| `PostToolUseFailure`  | After failed tool call                                               |
| `PostToolBatch`       | After full parallel tool batch, before next model call               |
| `Notification`        | Claude Code sends a notification                                     |
| `MessageDisplay`      | While assistant message text is displayed                            |
| `SubagentStart`       | Subagent spawned                                                     |
| `SubagentStop`        | Subagent finishes                                                    |
| `TaskCreated`         | Task created via `TaskCreate`                                        |
| `TaskCompleted`       | Task marked complete                                                 |
| `Stop`                | Claude finishes responding                                           |
| `StopFailure`         | Turn ends due to API error (output and exit code ignored)            |
| `TeammateIdle`        | Agent team teammate about to go idle                                 |
| `InstructionsLoaded`  | `CLAUDE.md` or `.claude/rules/*.md` loaded                           |
| `ConfigChange`        | Config file changes during session                                   |
| `CwdChanged`          | Working directory changes                                            |
| `FileChanged`         | Watched file changes (`matcher` specifies filenames)                 |
| `WorktreeCreate`      | Worktree created; replaces default git behavior                      |
| `WorktreeRemove`      | Worktree removed at session exit or subagent finish                  |
| `PreCompact`          | Before context compaction                                            |
| `PostCompact`         | After context compaction                                             |
| `Elicitation`         | MCP server requests user input                                       |
| `ElicitationResult`   | User responds to MCP elicitation                                     |
| `SessionEnd`          | Session terminates                                                   |

---

### MCP Servers

**Default location:** `.mcp.json` or inline in `plugin.json`

```json
{
  "mcpServers": {
    "plugin-db": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
      "env": { "DB_PATH": "${CLAUDE_PLUGIN_ROOT}/data" }
    }
  }
}
```

Servers start automatically when the plugin is enabled and appear as standard MCP tools.

---

### LSP Servers

**Default location:** `.lsp.json` or inline in `plugin.json`

```json
{
  "go": {
    "command": "gopls",
    "args": ["serve"],
    "extensionToLanguage": { ".go": "go" }
  }
}
```

**Required fields:**

| Field                 | Description                                  |
| --------------------- | -------------------------------------------- |
| `command`             | LSP binary to execute (must be in PATH)      |
| `extensionToLanguage` | Maps file extensions to language identifiers |

**Optional fields:**

| Field                   | Description                                   |
| ----------------------- | --------------------------------------------- |
| `args`                  | Command-line arguments                        |
| `transport`             | `stdio` (default) or `socket`                 |
| `env`                   | Environment variables                         |
| `initializationOptions` | Passed at server initialization               |
| `settings`              | Passed via `workspace/didChangeConfiguration` |
| `workspaceFolder`       | Workspace folder path                         |
| `startupTimeout`        | Max startup wait (ms)                         |
| `maxRestarts`           | Max restarts before giving up                 |
| `diagnostics`           | Push diagnostics after edits (default `true`) |

> The language server binary must be installed separately. LSP plugins only configure the connection.

**Available marketplace plugins:**

| Plugin              | Language server            | Install                                                |
| ------------------- | -------------------------- | ------------------------------------------------------ |
| `pyright-lsp`       | Pyright (Python)           | `pip install pyright` or `npm install -g pyright`      |
| `typescript-lsp`    | TypeScript Language Server | `npm install -g typescript-language-server typescript` |
| `rust-analyzer-lsp` | rust-analyzer              | See rust-analyzer docs                                 |

---

### Monitors

Background processes that run for the session lifetime; each stdout line is delivered to Claude as a notification. Requires v2.1.105+.

**Default location:** `monitors/monitors.json` or inline via `experimental.monitors` in `plugin.json`

```json
[
  {
    "name": "deploy-status",
    "command": "\"${CLAUDE_PLUGIN_ROOT}\"/scripts/poll-deploy.sh ${user_config.api_endpoint}",
    "description": "Deployment status changes"
  },
  {
    "name": "error-log",
    "command": "tail -F ./logs/error.log",
    "description": "Application error log",
    "when": "on-skill-invoke:debug"
  }
]
```

**Required fields:**

| Field         | Description                                          |
| ------------- | ---------------------------------------------------- |
| `name`        | Unique identifier within the plugin                  |
| `command`     | Shell command run as a persistent background process |
| `description` | Summary shown in the task panel                      |

**Optional fields:**

| Field  | Description                                              |
| ------ | -------------------------------------------------------- |
| `when` | `"always"` (default) or `"on-skill-invoke:<skill-name>"` |

Monitors only run in interactive CLI sessions and share the trust level of hooks. Disabling a plugin mid-session does not stop already-running monitors.

---

### Themes

_Experimental._ Color themes that appear in `/theme`.

**Default location:** `themes/<name>.json`

```json
{
  "name": "Dracula",
  "base": "dark",
  "overrides": {
    "claude": "#bd93f9",
    "error": "#ff5555",
    "success": "#50fa7b"
  }
}
```

Plugin themes are read-only. Pressing `Ctrl+E` copies one to `~/.claude/themes/` for editing. Selected theme persists as `custom:<plugin-name>:<slug>`.

---

## Plugin Manifest Schema

**Location:** `.claude-plugin/plugin.json` (optional — Claude Code auto-discovers components in default locations without it)

### Full Schema

```json
{
  "name": "plugin-name",
  "displayName": "Plugin Name",
  "version": "1.2.0",
  "description": "Brief description",
  "author": { "name": "Author", "email": "author@example.com", "url": "https://github.com/author" },
  "homepage": "https://docs.example.com/plugin",
  "repository": "https://github.com/author/plugin",
  "license": "MIT",
  "keywords": ["keyword1"],
  "defaultEnabled": true,
  "skills": "./custom/skills/",
  "commands": ["./custom/commands/special.md"],
  "agents": ["./custom/agents/reviewer.md"],
  "hooks": "./config/hooks.json",
  "mcpServers": "./mcp-config.json",
  "outputStyles": "./styles/",
  "lspServers": "./.lsp.json",
  "experimental": {
    "themes": "./themes/",
    "monitors": "./monitors.json"
  },
  "userConfig": {},
  "channels": [],
  "dependencies": ["helper-lib", { "name": "secrets-vault", "version": "~2.1.0" }]
}
```

### Metadata Fields

| Field            | Type    | Description                                                                |
| ---------------- | ------- | -------------------------------------------------------------------------- |
| `name`           | string  | **Required.** Unique kebab-case identifier; used for component namespacing |
| `$schema`        | string  | JSON Schema URL for editor validation (ignored at runtime)                 |
| `displayName`    | string  | Human-readable name shown in UI (v2.1.143+)                                |
| `version`        | string  | Semver string. If omitted, falls back to git commit SHA                    |
| `description`    | string  | Brief plugin purpose                                                       |
| `author`         | object  | `{ name, email, url }`                                                     |
| `homepage`       | string  | Documentation URL                                                          |
| `repository`     | string  | Source code URL                                                            |
| `license`        | string  | License identifier (e.g. `"MIT"`)                                          |
| `keywords`       | array   | Discovery tags                                                             |
| `defaultEnabled` | boolean | Start disabled on install (v2.1.154+). Defaults to `true`                  |

### Component Path Fields

All paths must be relative to the plugin root and start with `./`.

| Field                   | Type                  | Behavior                                      | Example                                |
| ----------------------- | --------------------- | --------------------------------------------- | -------------------------------------- |
| `skills`                | string\|array         | **Adds** to default `skills/` scan            | `"./custom/skills/"`                   |
| `commands`              | string\|array         | **Replaces** default `commands/`              | `"./cmd.md"`                           |
| `agents`                | string\|array         | **Replaces** default `agents/`                | `"./agents/reviewer.md"`               |
| `hooks`                 | string\|array\|object | Merged with other hook sources                | `"./hooks.json"`                       |
| `mcpServers`            | string\|array\|object | Merged with other MCP sources                 | `"./.mcp.json"`                        |
| `outputStyles`          | string\|array         | **Replaces** default `output-styles/`         | `"./styles/"`                          |
| `lspServers`            | string\|array\|object | Merged with other LSP sources                 | `"./.lsp.json"`                        |
| `experimental.themes`   | string\|array         | **Replaces** default `themes/`                | `"./themes/"`                          |
| `experimental.monitors` | string\|array         | **Replaces** default `monitors/monitors.json` | `"./monitors.json"`                    |
| `userConfig`            | object                | User-prompted config values                   | See below                              |
| `channels`              | array                 | MCP-backed message channels                   | See below                              |
| `dependencies`          | array                 | Required plugins with optional semver         | `[{ "name": "x", "version": "~2.0" }]` |

### User Configuration

Prompts users for values at enable time. Available as `${user_config.KEY}` in commands/configs and exported as `CLAUDE_PLUGIN_OPTION_<KEY>`.

```json
{
  "userConfig": {
    "api_endpoint": {
      "type": "string",
      "title": "API endpoint",
      "description": "Your team's API endpoint"
    },
    "api_token": {
      "type": "string",
      "title": "API token",
      "description": "Authentication token",
      "sensitive": true
    }
  }
}
```

| Field         | Required | Description                                                       |
| ------------- | -------- | ----------------------------------------------------------------- |
| `type`        | Yes      | `string` · `number` · `boolean` · `directory` · `file`            |
| `title`       | Yes      | Label in the config dialog                                        |
| `description` | Yes      | Help text                                                         |
| `sensitive`   | No       | Masks input; stores in system keychain instead of `settings.json` |
| `required`    | No       | Fails validation when empty                                       |
| `default`     | No       | Value when user provides nothing                                  |
| `multiple`    | No       | Allow array of strings (`string` type only)                       |
| `min` / `max` | No       | Bounds for `number` type                                          |

Non-sensitive values stored in `settings.json` under `pluginConfigs[<plugin-id>].options`. Sensitive values go to system keychain (≈2 KB total limit).

### Channels

Binds a plugin's MCP server to a message injection channel.

```json
{
  "channels": [
    {
      "server": "telegram",
      "userConfig": {
        "bot_token": { "type": "string", "title": "Bot token", "sensitive": true },
        "owner_id": {
          "type": "string",
          "title": "Owner ID",
          "description": "Your Telegram user ID"
        }
      }
    }
  ]
}
```

`server` must match a key in `mcpServers`. Per-channel `userConfig` follows the same schema as the top-level field.

---

## Environment Variables

Available for substitution in skill/agent content, hook commands, monitor commands, MCP/LSP server configs, and exported to all plugin subprocesses.

| Variable                | Resolves to                                                                                                                                            |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `${CLAUDE_PLUGIN_ROOT}` | Absolute path to the plugin's installation directory. Changes on update. Wrap in quotes in shell commands: `"${CLAUDE_PLUGIN_ROOT}"`.                  |
| `${CLAUDE_PLUGIN_DATA}` | Persistent data directory (`~/.claude/plugins/data/<id>/`). Survives updates. Created on first reference. Deleted on uninstall (unless `--keep-data`). |
| `${CLAUDE_PROJECT_DIR}` | The project root (same as the hook `CLAUDE_PROJECT_DIR` variable).                                                                                     |

---

## Installation Scopes

| Scope     | Settings file                 | Use case                         |
| --------- | ----------------------------- | -------------------------------- |
| `user`    | `~/.claude/settings.json`     | Personal, all projects (default) |
| `project` | `.claude/settings.json`       | Team plugins via version control |
| `local`   | `.claude/settings.local.json` | Project-specific, gitignored     |
| `managed` | Managed settings              | Admin-controlled, read-only      |

---

## Directory Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Manifest (optional)
├── skills/                  # Skills (subdirectory per skill)
├── commands/                # Skills as flat .md files
├── agents/                  # Subagent definitions
├── output-styles/           # Output style definitions
├── themes/                  # Color themes
├── monitors/
│   └── monitors.json
├── hooks/
│   └── hooks.json
├── bin/                     # Executables added to Bash tool PATH
├── settings.json            # Default settings (agent/subagentStatusLine keys only)
├── .mcp.json
└── .lsp.json
```

> All component directories must be at the plugin root — not inside `.claude-plugin/`. Only `plugin.json` goes in `.claude-plugin/`.

### File Locations Reference

| Component     | Default Location             |
| ------------- | ---------------------------- |
| Manifest      | `.claude-plugin/plugin.json` |
| Skills        | `skills/<name>/SKILL.md`     |
| Commands      | `commands/<name>.md`         |
| Agents        | `agents/<name>.md`           |
| Output styles | `output-styles/`             |
| Themes        | `themes/`                    |
| Hooks         | `hooks/hooks.json`           |
| MCP servers   | `.mcp.json`                  |
| LSP servers   | `.lsp.json`                  |
| Monitors      | `monitors/monitors.json`     |
| Executables   | `bin/`                       |
| Settings      | `settings.json`              |

---

## CLI Commands

### `plugin init`

Scaffold a new plugin at `~/.claude/skills/<name>/`.

```bash
claude plugin init <name> [options]
```

| Option                   | Description                                                                                 |
| ------------------------ | ------------------------------------------------------------------------------------------- |
| `--description <text>`   | Manifest description                                                                        |
| `--author <name>`        | Author name (default: `git config user.name`)                                               |
| `--author-email <email>` | Author email (default: `git config user.email`)                                             |
| `--with <components...>` | Scaffold extras: `skills` · `agents` · `hooks` · `mcp` · `lsp` · `output-style` · `channel` |
| `-f, --force`            | Overwrite existing `.claude-plugin/`                                                        |

Aliases: `new`

---

### `plugin install`

```bash
claude plugin install <plugin> [options]
```

| Option                | Description                  | Default |
| --------------------- | ---------------------------- | ------- |
| `-s, --scope <scope>` | `user` · `project` · `local` | `user`  |

---

### `plugin uninstall`

```bash
claude plugin uninstall <plugin> [options]
```

| Option                | Description                                      |
| --------------------- | ------------------------------------------------ |
| `-s, --scope <scope>` | `user` · `project` · `local` (default `user`)    |
| `--keep-data`         | Preserve `${CLAUDE_PLUGIN_DATA}`                 |
| `--prune`             | Also remove orphaned auto-installed dependencies |
| `-y, --yes`           | Skip confirmation (required when not a TTY)      |

Aliases: `remove`, `rm`

---

### `plugin prune`

Remove auto-installed dependencies no longer required by any plugin.

```bash
claude plugin prune [options]
```

| Option                | Description                                   |
| --------------------- | --------------------------------------------- |
| `-s, --scope <scope>` | `user` · `project` · `local` (default `user`) |
| `--dry-run`           | List what would be removed                    |
| `-y, --yes`           | Skip confirmation                             |

Aliases: `autoremove` · Requires v2.1.121+

---

### `plugin enable`

```bash
claude plugin enable <plugin> [-s <scope>]
```

Enables transitively required dependencies at the same scope.

---

### `plugin disable`

```bash
claude plugin disable <plugin> [-s <scope>]
```

Fails if another enabled plugin depends on this one. Error message includes the chained disable command.

---

### `plugin update`

```bash
claude plugin update <plugin> [-s <scope>]
```

Scope values: `user` · `project` · `local` · `managed`

---

### `plugin list`

```bash
claude plugin list [--json] [--available]
```

`--available` requires `--json`. Interactive alias: `/plugin list` (supports `--enabled` / `--disabled`).

---

### `plugin details`

Show component inventory and projected token cost.

```bash
claude plugin details <name>
```

Output includes always-on token cost (added every session) and per-component on-invoke cost.

---

### `plugin validate`

```bash
claude plugin validate <path> [--strict]
```

Checks `plugin.json`, skill/agent/command frontmatter, and `hooks/hooks.json`. `--strict` treats unrecognized-field warnings as errors.

---

### `plugin tag`

Create a release git tag from inside the plugin directory.

```bash
claude plugin tag [--push] [--dry-run] [-f]
```

---

## Versioning

Version resolution order (first set wins):

1. `version` in `plugin.json`
2. `version` in the marketplace entry
3. Git commit SHA (for `github` / `url` / `git-subdir` / relative-path sources)
4. `unknown` (npm sources or non-git local directories)

| Approach   | Set                                   | Update behavior                              |
| ---------- | ------------------------------------- | -------------------------------------------- |
| Explicit   | `"version": "2.1.0"` in `plugin.json` | Users update only when you bump the field    |
| Commit-SHA | Omit `version` everywhere             | Every new commit is treated as a new version |

> If `version` is set, you **must** bump it for users to receive changes. Pushing new commits alone has no effect.

---

## Debugging

Run `claude --debug` to see plugin loading, manifest errors, component registration, and MCP initialization.

### Common Issues

| Symptom                    | Cause                     | Fix                                              |
| -------------------------- | ------------------------- | ------------------------------------------------ |
| Plugin not loading         | Invalid `plugin.json`     | Run `claude plugin validate`                     |
| Skills not appearing       | Wrong directory structure | Move `skills/` / `commands/` to plugin root      |
| Hooks not firing           | Script not executable     | `chmod +x script.sh`                             |
| MCP server fails           | Missing path variable     | Use `${CLAUDE_PLUGIN_ROOT}` for all plugin paths |
| Path errors                | Absolute paths used       | All paths must be relative, starting with `./`   |
| LSP `Executable not found` | Binary not installed      | Install the language server binary separately    |

### Error Messages

| Message                                     | Meaning                                                       |
| ------------------------------------------- | ------------------------------------------------------------- |
| `Invalid JSON syntax: Unexpected token ...` | Missing/extra comma or unquoted string in JSON                |
| `Validation errors: name: Required`         | Required manifest field missing                               |
| `JSON parse error`                          | JSON syntax error in manifest                                 |
| `No commands found in custom directory`     | Path exists but contains no valid `.md` files                 |
| `Plugin directory not found at path`        | `source` path in `marketplace.json` is wrong                  |
| `conflicting manifests`                     | Component defined in both `plugin.json` and marketplace entry |

### Hook Troubleshooting

1. Script must be executable: `chmod +x ./scripts/script.sh`
2. Shebang required: `#!/bin/bash` or `#!/usr/bin/env bash`
3. Path must use variable: `"${CLAUDE_PLUGIN_ROOT}"/scripts/script.sh`
4. Event names are case-sensitive: `PostToolUse` not `postToolUse`
5. Matcher must match the tool: `"matcher": "Write|Edit"`

### MCP Server Troubleshooting

1. Verify command exists and is executable
2. All paths must use `${CLAUDE_PLUGIN_ROOT}`
3. Check `claude --debug` for initialization errors
4. Confirm server implements the MCP protocol correctly

---

## Skills-Directory Plugins

Any folder under a skills directory containing `.claude-plugin/plugin.json` loads automatically as `<name>@skills-dir`.

| Path                           | Scope    | Notes                                   |
| ------------------------------ | -------- | --------------------------------------- |
| `~/.claude/skills/<name>/`     | personal | Loads in every project                  |
| `<cwd>/.claude/skills/<name>/` | project  | Loads after workspace trust is accepted |

Project-scope plugins: MCP servers require per-server approval; LSP servers require workspace trust; monitors do not load.

To disable a skills-directory plugin:

```bash
claude plugin disable my-tool@skills-dir
```

Changes to `SKILL.md` take effect immediately. Changes to hooks, `.mcp.json`, or agents require `/reload-plugins` or a restart.
