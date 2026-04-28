"""Regex-based heuristic analyzer for TypeScript source files."""

from __future__ import annotations

import re
from pathlib import Path

from reposage.models import FileRecord, TSCodeSignals

# Matches `: any` or `as any` — explicit `any` type annotations/casts.
_ANY_RE = re.compile(r":\s*any\b|as\s+any\b")

# Matches exported functions whose parameter list closes with `)` followed
# immediately (modulo whitespace) by `{`, meaning there is NO return-type
# annotation between `)` and `{`.
_UNTYPED_EXPORT_RE = re.compile(r"export\s+(?:async\s+)?function\s+\w+\s*\([^)]*\)\s*\{")

# Matches type assertions of the form `) as <Type>` where <Type> is not `any`.
# Accepts both identifier types (`as Foo`) and object/tuple types (`as {`).
_TYPE_ASSERTION_RE = re.compile(r"\)\s+as\s+(?!any\b)[\w{]")


def analyze_typescript(root: Path, ts_files: list[FileRecord]) -> TSCodeSignals:
    """Run regex heuristics over .ts/.tsx files and return aggregate signals."""
    any_count = 0
    untyped_count = 0
    assertion_count = 0

    for record in ts_files:
        if record.extension not in {".ts", ".tsx"}:
            continue
        try:
            text = (root / record.path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        any_count += len(_ANY_RE.findall(text))
        untyped_count += len(_UNTYPED_EXPORT_RE.findall(text))
        assertion_count += len(_TYPE_ASSERTION_RE.findall(text))

    return TSCodeSignals(
        any_usage_count=any_count,
        untyped_exports=untyped_count,
        type_assertion_count=assertion_count,
    )
