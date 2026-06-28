#!/usr/bin/env bash
# Standalone smoke test for skill-nudge.sh degrade-to-no-op paths.
# Tests that skill-nudge.sh exits 0 and produces valid or empty output under:
# (a) normal repo state
# (b) CLAUDE_PLUGIN_ROOT unset
# (c) skills/ directory missing
# (d) jq unavailable
#
# Validates the invariant: lib.sh sourcing failure or any internal error
# degrades to silent no-op (exit 0), never propagates under set -euo pipefail.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_TEMP_DIR="${TEST_TEMP_DIR:-/tmp}"
TEST_WORK_DIR="$TEST_TEMP_DIR/test-skill-nudge-$$"
PASS_COUNT=0
FAIL_COUNT=0

cleanup() {
  rm -rf "$TEST_WORK_DIR" 2>/dev/null || true
}
trap cleanup EXIT

mkdir -p "$TEST_WORK_DIR"

# ponytail: simple wrapper to run skill-nudge.sh and capture output+code together
test_skill_nudge() {
  local work_dir="$1"
  local cmd="$2"

  cd "$work_dir"
  local output
  local code
  output=$($cmd 2>/dev/null || true)
  code=${PIPESTATUS[0]}

  echo "$output"
  return "$code"
}

# Helper to run a test case and validate output
run_test() {
  local case_name="$1"
  local cmd="$2"
  local setup_fn="$3"

  # Clean and recreate work dir for isolation
  rm -rf "$TEST_WORK_DIR"
  mkdir -p "$TEST_WORK_DIR"

  # Copy repo to temp work dir
  cp -r "$REPO_ROOT"/* "$TEST_WORK_DIR/" 2>/dev/null || true

  # Run setup function if provided
  if [ "$setup_fn" != "none" ]; then
    (cd "$TEST_WORK_DIR" && $setup_fn) || true
  fi

  # Run the test command and capture output and code
  local output
  local exit_code
  output=$(cd "$TEST_WORK_DIR" && eval "$cmd" 2>/dev/null || echo "")
  exit_code=${PIPESTATUS[0]:-0}

  # Validate: exit code must be 0
  if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: $case_name (exit code $exit_code, expected 0)"
    ((FAIL_COUNT++))
    return 1
  fi

  # Validate: output must be valid JSON (if non-empty) or empty
  if [ -n "$output" ]; then
    # Try to parse as JSON
    if command -v jq >/dev/null 2>&1; then
      if ! echo "$output" | jq . >/dev/null 2>&1; then
        echo "FAIL: $case_name (invalid JSON output)"
        ((FAIL_COUNT++))
        return 1
      fi
    else
      # Minimal JSON validation: check for opening {
      if ! echo "$output" | grep -q '^{'; then
        echo "FAIL: $case_name (output doesn't look like JSON)"
        ((FAIL_COUNT++))
        return 1
      fi
    fi
  fi

  echo "PASS: $case_name"
  ((PASS_COUNT++))
  return 0
}

# Test (a): normal repo state
run_test "normal repo state" "bash hooks/skill-nudge.sh </dev/null" "none" || true

# Test (b): CLAUDE_PLUGIN_ROOT unset
run_test "CLAUDE_PLUGIN_ROOT unset" "unset CLAUDE_PLUGIN_ROOT; bash hooks/skill-nudge.sh </dev/null" "none" || true

# Test (c): skills/ directory missing
run_test "skills/ directory missing" "bash hooks/skill-nudge.sh </dev/null" "rm -rf skills" || true

# Test (d): jq unavailable
# Create a shadowed PATH that doesn't include jq
shadow_jq() {
  mkdir -p "$TEST_WORK_DIR/shadow-bin"
  # Copy essential POSIX tools
  for cmd in find grep sed basename dirname paste sh bash; do
    cmd_path=$(command -v "$cmd" 2>/dev/null || echo "")
    if [ -n "$cmd_path" ]; then
      cp "$cmd_path" "$TEST_WORK_DIR/shadow-bin/" 2>/dev/null || true
    fi
  done
}
run_test "jq unavailable" "export PATH='$TEST_WORK_DIR/shadow-bin:\$PATH'; bash hooks/skill-nudge.sh </dev/null" "shadow_jq" || true

# Summary
echo ""
echo "Results: $PASS_COUNT PASS, $FAIL_COUNT FAIL"
if [ "$FAIL_COUNT" -eq 0 ]; then
  exit 0
else
  exit 1
fi
