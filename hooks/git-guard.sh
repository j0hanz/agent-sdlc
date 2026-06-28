#!/usr/bin/env bash
# PreToolUse(Bash) guard — restricts Bash to `git` invocations only. Generic
# and reusable: any agent frontmatter can point its `hooks.PreToolUse` at
# this script (currently used by agents/diff-reviewer.md) to get the same
# git-only restriction without each agent needing its own copy. Self-
# contained, no lib.sh dependency: a bug in the shared helper library must
# never silently disable this guard. Best-effort segment-splitting on
# ; & | && || (matches hooks/shell-safety.sh's approach), PLUS an explicit
# reject of any $(...)/`...`/<(...)/>(...) construct: unlike
# shell-safety.sh's denylist (a few catastrophic patterns, under-blocking by
# design), this is an allowlist whose entire guarantee would otherwise be
# defeated by a git-prefixed segment smuggling an arbitrary command through
# a subshell.
set -euo pipefail

input=$(cat)

extract_command() {
  local json="$1"
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$json" | jq -r '.tool_input.command // empty' 2>/dev/null
    return
  fi
  node -e 'try { console.log(JSON.parse(process.argv[1]).tool_input.command); } catch (e) {}' "$json" 2>/dev/null
}

command=$(extract_command "$input") || command=""
[ -z "$command" ] && exit 0

deny() {
  printf "[git-guard] Blocked: %s. This agent's Bash tool is restricted to git invocations.\n" "$1" >&2
  exit 2
}

# Split on ; && || | & — best-effort, not a full shell parser (matches
# hooks/shell-safety.sh's approach). Real newlines from a genuinely
# multi-line command already survive JSON decoding (jq, or the fallback
# above, both produce actual newline bytes from a JSON \n) and still split
# awk into separate records here. Use %s, not %b: by this point $command is
# plain decoded text, not an escape-sequence string to re-interpret — %b
# would wrongly eat a literal \n/\t/\f inside e.g. a Windows path
# (C:\new\file.txt) as if it were an escape sequence, corrupting it.
IFS=$'\n' read -r -d '' -a segments < <(printf '%s' "$command" | awk '
  {
    str = $0; pos = 1; len = length(str)
    while (pos <= len) {
      match_pos = match(substr(str, pos), /\|\||&&|[&|;]/)
      if (match_pos == 0) { segment = substr(str, pos); if (segment != "") print segment; break }
      segment = substr(str, pos, match_pos - 1)
      if (segment != "") print segment
      pos = pos + match_pos + RLENGTH - 1
    }
  }
') || true

for segment in "${segments[@]}"; do
  trimmed="$(printf '%s' "$segment" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
  [ -z "$trimmed" ] && continue

  # A segment that starts with `git` can still smuggle an arbitrary command
  # through command/process substitution (executed by the shell before the
  # outer `git` ever runs), which the splitter above can't see since none of
  # $( ` <( >( are listed metacharacters. Reject outright rather than try to
  # inspect their contents.
  if [[ "$trimmed" == *'$('* || "$trimmed" == *'`'* || "$trimmed" == *'<('* || "$trimmed" == *'>('* ]]; then
    deny "command/process substitution is not permitted ('$trimmed')"
  fi

  if [[ ! "$trimmed" =~ ^git([[:space:]]|$) ]]; then
    deny "non-git command ('$trimmed')"
  fi
done

exit 0
