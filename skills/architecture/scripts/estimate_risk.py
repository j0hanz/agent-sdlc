import os
import sys
import subprocess
from typing import List, Dict, Any
from utils.extractor import extract_imports, detect_lang
from utils.walk import walk_dir


def estimate_risk(target_files: List[str], root_dir: str) -> List[Dict[str, Any]]:
    abs_root = os.path.abspath(root_dir)
    all_files = walk_dir(abs_root)

    # Build reverse graph: for each target, how many files import it?
    caller_counts = {tf: 0 for tf in target_files}

    for src in all_files:
        if src in target_files:
            continue
        try:
            with open(src, "r", encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError):
            continue

        lang = detect_lang(src)
        imports = extract_imports(content, lang)
        for imp in imports:
            if not imp.startswith("."):
                continue

            resolved = os.path.abspath(os.path.join(os.path.dirname(src), imp))
            for tf in target_files:
                tf_no_ext, _ = os.path.splitext(tf)
                is_index = os.path.basename(tf_no_ext) == "index"

                if (
                    resolved == tf
                    or resolved == tf_no_ext
                    or (is_index and resolved == os.path.dirname(tf))
                ):
                    caller_counts[tf] += 1

    results = []
    for tf in target_files:
        callers = caller_counts[tf]
        base_name = os.path.splitext(os.path.basename(tf))[0]

        has_tests = False
        for f in all_files:
            if f == tf:
                continue
            fb = os.path.basename(f)
            if (
                fb.startswith(f"{base_name}.test.")
                or fb.startswith(f"{base_name}.spec.")
                or fb.startswith(f"{base_name}_test.")
                or fb == f"test_{base_name}.py"
            ):
                has_tests = True
                break

        churn = 0
        try:
            cmd = ["git", "log", "--oneline", "--since=90 days ago", "--", tf]
            output = subprocess.check_output(cmd, cwd=abs_root, encoding="utf-8")
            churn = len([line for line in output.splitlines() if line.strip()])
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        risk = "LOW"
        rationale = ""

        if callers > 5 or (callers > 2 and not has_tests):
            risk = "HIGH"
            rationale = (
                f"{callers} callers — touching this breaks many dependents"
                if callers > 5
                else f"{callers} callers and no test coverage"
            )
        elif callers > 1 or (not has_tests and churn > 3):
            risk = "MEDIUM"
            rationale = (
                "No tests — changes are hard to validate safely"
                if not has_tests
                else f"{callers} callers — moderate blast radius"
            )
        else:
            risk = "LOW"
            rationale = (
                f"{callers} caller(s){', has test coverage' if has_tests else ''}"
            )

        results.append(
            {
                "file": os.path.relpath(tf, os.getcwd()),
                "risk": risk,
                "callerCount": callers,
                "hasTests": has_tests,
                "churn": churn,
                "rationale": rationale,
            }
        )

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Estimate refactoring risk for files.")
    parser.add_argument("root_dir", help="Root directory to scan for callers")
    parser.add_argument("targets", nargs="+", help="Target files to score")

    args = parser.parse_args()
    target_paths = [os.path.abspath(t) for t in args.targets]

    try:
        results = estimate_risk(target_paths, args.root_dir)

        print("\n--- Refactoring Risk Estimate ---\n")
        # Simple table formatting
        header = f"{'Risk':<10} {'File':<40} {'Callers':<8} {'Tests':<6} {'Churn':<8} {'Rationale'}"
        print(header)
        print("-" * len(header))
        for r in results:
            print(
                f"{r['risk']:<10} {r['file']:<40} {r['callerCount']:<8} {'yes' if r['hasTests'] else 'no':<6} {r['churn']:<8} {r['rationale']}"
            )

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)
