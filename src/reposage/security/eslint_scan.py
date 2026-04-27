"""ESLint integration for JavaScript/TypeScript linting."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from reposage.models import LintSummary
from reposage.security._runner import run_or_load


def scan_eslint(root: Path) -> tuple[LintSummary | None, str]:
    """Run eslint or parse fallback report. Returns (summary, skip_reason)."""
    cmd = ["eslint", ".", "--format", "json"]
    fallback = root / "eslint-report.json"
    raw = run_or_load(cmd, fallback)
    if raw is None:
        return None, "not installed and no eslint-report.json found"

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"parse error: {exc}"

    if not isinstance(data, list):
        return None, "unexpected format: expected JSON array"

    total_errors = sum(f.get("errorCount", 0) for f in data)
    total_warnings = sum(f.get("warningCount", 0) for f in data)

    rule_counts: Counter[str] = Counter()
    for file_result in data:
        for msg in file_result.get("messages", []):
            rule_id = msg.get("ruleId") or ""
            prefix = rule_id.split("/")[0] if "/" in rule_id else rule_id
            if prefix:
                rule_counts[prefix] += 1

    top_categories = [cat for cat, _ in rule_counts.most_common(3)]

    return LintSummary(
        tool="eslint",
        error_count=total_errors,
        warning_count=total_warnings,
        top_categories=top_categories,
    ), ""
