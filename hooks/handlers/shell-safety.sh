#!/usr/bin/env bash
# PreToolUse(Bash): warn when a risky shell pattern is detected.
# Additive only — returns additionalContext, never blocks.
set -euo pipefail
source "${BASH_SOURCE[0]%/*}/../lib.sh"

INPUT=$(cat)
EVENT=$(jq -r '.hook_event_name // "PreToolUse"' <<< "$INPUT")
COMMAND=$(jq -r '.tool_input.command // empty' <<< "$INPUT")

STARTED=$(date +%s%3N)

warn=""
if [[ -n "$COMMAND" ]]; then
  declare -A _checks
  checks=(
    'rm\s+-rf:force-remove pattern'
    'git\s+push\s+(-f|--force):force-push pattern'
    'DROP\s+TABLE:SQL DROP TABLE'
    'TRUNCATE\s+TABLE:SQL TRUNCATE TABLE'
    'git\s+reset\s+--hard:hard reset pattern'
    'git\s+checkout\s+--:checkout -- discard changes'
    '>\s*/dev/null.*rm:redirect to null with rm'
  )
  for entry in "${checks[@]}"; do
    pattern="${entry%%:*}"
    label="${entry##*:}"
    if echo "$COMMAND" | grep -qiE "$pattern"; then
      warn="Shell safety: detected a ${label} — confirm intent before this runs."
      break
    fi
  done
fi

ENDED=$(date +%s%3N)
DURATION=$(( ENDED - STARTED ))

if [[ -n "$warn" ]]; then
  emit_context "$EVENT" "$warn"
fi

write_telemetry "shell-safety" "check" "$EVENT" "$DURATION" "success"
exit 0
