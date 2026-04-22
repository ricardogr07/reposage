"""Enforce a maximum line count per source file.

Usage:
    python scripts/check_line_counts.py [--max N] [--path DIR] [--exclude PATTERN ...]

Exits 1 if any file exceeds the limit; 0 otherwise.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check source file line counts.")
    parser.add_argument("--max", type=int, default=400, help="Maximum allowed lines per file")
    parser.add_argument(
        "--path", default="src/reposage", help="Root directory to scan (default: src/reposage)"
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Glob patterns to exclude (matched against filename only)",
    )
    args = parser.parse_args(argv)

    root = Path(args.path)
    if not root.exists():
        print(f"error: path not found: {root}", file=sys.stderr)
        return 1

    violations: list[tuple[Path, int]] = []
    for py_file in sorted(root.rglob("*.py")):
        if "__pycache__" in py_file.parts:
            continue
        if any(py_file.match(pattern) for pattern in args.exclude):
            continue
        line_count = len(py_file.read_text(encoding="utf-8").splitlines())
        if line_count > args.max:
            violations.append((py_file, line_count))

    if violations:
        print(f"Files exceeding {args.max}-line limit:")
        for path, count in violations:
            print(f"  {path}  ({count} lines)")
        return 1

    print(f"All files within {args.max}-line limit. ({len(list(root.rglob('*.py')))} files checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
