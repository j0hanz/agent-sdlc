#!/usr/bin/env python3
# Context pruning and formatting tool.
# Compresses log files, filters stack traces, converts JSON to markdown-kv,
# and maintains rolling context summaries.
# """

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Hoisted error patterns to prevent recompilation on every call
_ERROR_PATTERNS = [
    re.compile(r"fail", re.I),
    re.compile(r"error", re.I),
    re.compile(r"exception", re.I),
    re.compile(r"traceback", re.I),
    re.compile(r"critical", re.I),
    re.compile(r"\b(at)\s+\S+:\d+", re.I),
    re.compile(r"^E\s+.*", re.M),
]


def to_markdown_kv(data: Any, prefix: str = "", depth: int = 0) -> list[str]:
    """Recursively converts dictionaries and lists into a flat, compact markdown-kv string."""
    if depth > 50:
        raise ValueError("Exceeded maximum nesting depth of 50 in JSON object")

    lines = []
    if isinstance(data, dict):
        for k, v in data.items():
            new_key = f"{prefix}_{k}" if prefix else k
            lines.extend(to_markdown_kv(v, new_key, depth + 1))
    elif isinstance(data, list):
        if not data:
            lines.append(f"{prefix}: (empty)")
        elif all(isinstance(x, (str, int, float, bool)) for x in data):
            val_str = ", ".join(str(x) for x in data)
            lines.append(f"{prefix}: {val_str}")
        else:
            for idx, item in enumerate(data):
                new_key = f"{prefix}_{idx}"
                lines.extend(to_markdown_kv(item, new_key, depth + 1))
    else:
        lines.append(f"{prefix}: {data}")
    return lines


def filter_logs(logs_text: str) -> str:
    """Filters logs to retain only failure signals, tracebacks, and test failures."""
    lines = [line.rstrip() for line in logs_text.splitlines()]
    if not lines:
        return "empty log"

    error_indices = []
    for idx, line in enumerate(lines):
        if any(pat.search(line) for pat in _ERROR_PATTERNS):
            error_indices.append(idx)

    if not error_indices:
        if len(lines) <= 10:
            return "\n".join(lines)
        return (
            "\n".join(lines[:5])
            + f"\n... [omitted {len(lines) - 10} lines of passing logs] ...\n"
            + "\n".join(lines[-5:])
        )

    keep_indices = set()
    for err_idx in error_indices:
        start = max(0, err_idx - 2)
        end = min(len(lines), err_idx + 8)
        for i in range(start, end):
            keep_indices.add(i)

    sorted_indices = sorted(keep_indices)  # Removed redundant list() call
    output_parts = []
    last_idx = -1

    for idx in sorted_indices:
        if last_idx != -1 and idx > last_idx + 1:
            output_parts.append(f"... [omitted {idx - last_idx - 1} lines] ...")
        output_parts.append(lines[idx])
        last_idx = idx

    result = "\n".join(output_parts)
    result_lines = result.splitlines()
    # Corrected truncation guard threshold to match exact output window limits (50 lines total)
    if len(result_lines) > 50:
        return (
            "\n".join(result_lines[:40])
            + f"\n... [omitted {len(result_lines) - 50} lines of error details] ...\n"
            + "\n".join(result_lines[-10:])
        )
    return result


def update_rolling_summary(
    summary_path: Path,
    timestamp: str,
    done: str,
    blocking: str,
    next_step: str,
    decisions: str,
) -> str:
    """Updates the rolling summary file, archiving previous sessions."""
    existing_entries: list[str] = []
    if summary_path.exists():
        content = summary_path.read_text(encoding="utf-8")
        # Split on markdown section headers for Session
        parts = re.split(r"^## Session:\s*", content, flags=re.M)
        for part in parts[1:]:
            existing_entries.append(part.strip())

    new_block = (
        f"timestamp: {timestamp}\n"
        f"done: {done}\n"
        f"blocking: {blocking}\n"
        f"next: {next_step}\n"
        f"key_decisions: {decisions}"
    )

    merged_history = []
    for idx, entry in enumerate(existing_entries):
        lines = entry.splitlines()
        if not lines:
            continue
        header_line = lines[0].strip()
        ts_match = re.match(r"^([^\s(]+)", header_line)
        ts = ts_match.group(1) if ts_match else header_line

        # Archive after the second session, keep full detail for recent sessions
        body = "\n".join(lines[1:]).strip()

        if idx < 2:
            merged_history.append(f"## Session: {header_line}\n{body}")
        else:
            # Check if it was already marked as archived to avoid prepending/losing labels
            display_header = (
                header_line if "Archived" in header_line else f"{ts} (Archived)"
            )
            done_line = "No actions recorded"
            for line in lines[1:]:
                if line.startswith("done:"):
                    done_line = line.replace("done:", "").strip()
                    break
            merged_history.append(f"## Session: {display_header}\n- {done_line}")

    output = [
        "# Rolling Task Summary\n",
        f"## Session: {timestamp} (Current)",
        new_block,
        "",
    ]
    if merged_history:
        output.extend(merged_history)

    final_content = "\n".join(output)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(final_content, encoding="utf-8")
    return final_content


def main() -> None:
    parser = argparse.ArgumentParser(description="Prune and optimize context input.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--logs", action="store_true", help="Filter raw logs from stdin")
    group.add_argument(
        "--to-kv", action="store_true", help="Convert JSON input to flat KV"
    )
    group.add_argument(
        "--summary", action="store_true", help="Update the rolling summary file"
    )

    parser.add_argument(
        "--path",
        type=Path,
        default=Path(".claude/rolling_summary.md"),
        help="Summary path",
    )
    parser.add_argument("--timestamp", default="", help="Timestamp of current session")
    parser.add_argument("--done", default="None", help="Completed tasks")
    parser.add_argument("--blocking", default="None", help="Blocking issues")
    parser.add_argument("--next-step", default="None", help="Immediate next action")
    parser.add_argument("--decisions", default="None", help="Key decisions made")

    args = parser.parse_args()

    if args.logs:
        text = sys.stdin.read()
        print(filter_logs(text))
    elif args.to_kv:
        try:
            raw = json.loads(sys.stdin.read())
            kv_lines = to_markdown_kv(raw)
            print("\n".join(kv_lines))
        except json.JSONDecodeError as exc:
            sys.stderr.write(f"error: invalid JSON input - {exc}\n")
            sys.exit(1)
    elif args.summary:
        if not args.timestamp or not args.timestamp.strip():
            sys.stderr.write(
                "error: --timestamp is required for updating the summary\n"
            )
            sys.exit(1)
        result = update_rolling_summary(
            args.path,
            args.timestamp,
            args.done,
            args.blocking,
            args.next_step,
            args.decisions,
        )
        print(f"Summary written to {args.path}. Content:")
        print(result)


if __name__ == "__main__":
    main()
