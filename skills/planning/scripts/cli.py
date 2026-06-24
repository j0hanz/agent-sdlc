#!/usr/bin/env python3
"""cli.py — Single entry point for the planning skill's scripts.

Subcommands:
    scaffold  Write paired <name>.specs.md + <name>.plan.md files
    validate  Validate a spec, or check the review gate (--review)
    sync      Sync spec requirements into plan task stubs
    pipeline  Run validate(spec) -> sync -> validate(plan) -> validate(cross)

Usage:
    python cli.py scaffold <name> [--depth sketch|contract|blueprint] [--dir DIR]
                                   [--goal GOAL] [--force]
    python cli.py validate <name> [--spec] [--review] [--level sketch|contract|blueprint]
    python cli.py sync <spec> [--plan FILE]
    python cli.py pipeline --name <name> [--dir DIR] [--depth sketch|contract|blueprint]

Note: `validate --spec` (the default) checks the spec only — used for sketch
depth. For contract/blueprint, use `pipeline` instead, which runs
spec -> sync -> plan -> cross in one gated sequence. `validate --review`
checks the review gate before handoff.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scaffold import _NAME_RE
from scaffold import scaffold
from sync import sync
from validate import (
    _print_results,
    _resolve_paths,
    feature_name,
    validate_cross,
    validate_plan,
    validate_review,
    validate_spec,
)


def _validate_pipeline_name(name: str) -> None:
    # pipeline builds paths from `name` directly (no scaffold() call), so this
    # is the only guard against path traversal via --name on this code path.
    if not _NAME_RE.fullmatch(name or ""):
        raise ValueError(f"Invalid --name {name!r}: must be a plain filename stem")


def _cmd_scaffold(args: argparse.Namespace) -> int:
    goal = args.goal or "One sentence: what capability or outcome?"
    spec_path, plan_path = scaffold(
        args.name, args.depth, args.dir, goal, force=args.force
    )
    print(f"Created: {spec_path}")
    print(f"Created: {plan_path}")
    print(f"\nNext: fill in {spec_path.name}, then run:")
    print(f"  python cli.py sync {spec_path}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    spec_path, _plan_path = _resolve_paths(args.name)

    all_errors: list[str] = []

    if args.review:
        print(f"\n--- Review: {feature_name(spec_path)}.review.md ---")
        errs, warns = validate_review(spec_path)
        _print_results("Review", errs, warns)
        all_errors.extend(errs)
    else:
        print(f"\n--- Spec: {spec_path} [level={args.level}] ---")
        errs, warns = validate_spec(spec_path, args.level)
        _print_results("Spec", errs, warns)
        all_errors.extend(errs)

    if all_errors:
        print(f"\nTotal errors: {len(all_errors)} - INVALID")
        return 1
    print("\nAll checks passed - VALID")
    return 0


def _cmd_sync(args: argparse.Namespace) -> int:
    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"cli.py sync: spec file not found: {spec_path}", file=sys.stderr)
        return 1

    plan_path = (
        Path(args.plan)
        if args.plan
        else spec_path.parent / (feature_name(spec_path) + ".plan.md")
    )

    _added, sync_warnings = sync(spec_path, plan_path)
    for w in sync_warnings:
        print(f"  [!] {w}", file=sys.stderr)
    return 0


def _print_step(label: str, errs: list[str], warns: list[str]) -> None:
    print(f"[*] {label}...")
    for w in warns:
        print(f"  [!] {w}")
    for err in errs:
        print(f"  [X] {err}")
    if errs:
        print(f"\n[!] {label} failed.")


def _cmd_pipeline(args: argparse.Namespace) -> int:
    name = args.name
    _validate_pipeline_name(name)

    plan_dir = Path(args.dir).resolve()
    spec_path = plan_dir / f"{name}.specs.md"
    plan_path = plan_dir / f"{name}.plan.md"

    for path_obj in (spec_path, plan_path):
        if not path_obj.exists():
            print(f"[!] {path_obj} not found. Run scaffold and author it first.")
            return 1

    errs, warns = validate_spec(spec_path, args.depth)
    _print_step("Validating Spec", errs, warns)
    if errs:
        return 1

    print("[*] Syncing...")
    _added, sync_warnings = sync(spec_path, plan_path)
    _print_step("Syncing", sync_warnings, [])
    if sync_warnings:
        return 1

    errs, warns = validate_plan(plan_path)
    _print_step("Validating Plan", errs, warns)
    if errs:
        return 1

    errs, warns, _matrix = validate_cross(spec_path, plan_path, args.depth)
    _print_step("Cross-Validating", errs, warns)
    if errs:
        return 1

    print("\n[+] Pipeline completed successfully. All validations passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_scaffold = sub.add_parser(
        "scaffold", help="Scaffold paired <name>.specs.md + <name>.plan.md files."
    )
    p_scaffold.add_argument("name", help="Stem name (e.g. 'auth-jwt')")
    p_scaffold.add_argument(
        "--depth", choices=["sketch", "contract", "blueprint"], default="contract"
    )
    p_scaffold.add_argument("--dir", default="plan", metavar="DIR")
    p_scaffold.add_argument("--goal", default=None)
    p_scaffold.add_argument("--force", action="store_true")
    p_scaffold.set_defaults(handler=_cmd_scaffold)

    p_validate = sub.add_parser(
        "validate",
        help="Validate a spec (default) or the review gate (--review).",
    )
    p_validate.add_argument("name", help="Stem name or path to either artifact")
    p_validate.add_argument("--review", action="store_true")
    p_validate.add_argument(
        "--level", choices=["sketch", "contract", "blueprint"], default="contract"
    )
    p_validate.set_defaults(handler=_cmd_validate)

    p_sync = sub.add_parser(
        "sync", help="Sync spec requirements into plan task stubs (idempotent)."
    )
    p_sync.add_argument("spec", help="Path to <name>.specs.md")
    p_sync.add_argument("--plan", default=None, metavar="FILE")
    p_sync.set_defaults(handler=_cmd_sync)

    p_pipeline = sub.add_parser(
        "pipeline",
        help="Run validate(spec) -> sync -> validate(plan) -> validate(cross).",
    )
    p_pipeline.add_argument("--name", required=True)
    p_pipeline.add_argument("--dir", default="plan", metavar="DIR")
    p_pipeline.add_argument(
        "--depth", choices=["sketch", "contract", "blueprint"], default="contract"
    )
    p_pipeline.set_defaults(handler=_cmd_pipeline)

    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"cli.py: {e}", file=sys.stderr)
        sys.exit(1)
