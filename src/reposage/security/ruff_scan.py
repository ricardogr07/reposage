"""ruff integration for Python lint scanning."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from reposage.models import LintSummary
from reposage.security._runner import run_or_load

_CODE_CATEGORY: dict[str, str] = {
    "ANN": "annotations",
    "RUF": "ruff",
    "UP": "pyupgrade",
    "E": "pycodestyle",
    "F": "pyflakes",
    "S": "security",
    "W": "warnings",
    "B": "bugbear",
    "N": "naming",
    "C": "complexity",
    "I": "imports",
}


def _category(code: str) -> str:
    """Map a ruff rule code to a human-readable category label."""
    for prefix, label in _CODE_CATEGORY.items():
        if code.startswith(prefix):
            return label
    return code[:1] if code else "unknown"


def scan_ruff(root: Path) -> tuple[LintSummary | None, str]:
    """Run ruff or parse fallback report. Returns (summary, skip_reason)."""
    cmd = ["ruff", "check", str(root), "--output-format", "json"]
    fallback = root / "ruff-report.json"
    raw = run_or_load(cmd, fallback)
    if raw is None:
        return None, "not installed and no ruff-report.json found"

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"parse error: {exc}"

    if not isinstance(data, list):
        return None, "unexpected format: expected JSON array"

    category_counts: Counter[str] = Counter(_category(entry.get("code", "")) for entry in data)
    top_categories = [cat for cat, _ in category_counts.most_common(3)]

    return LintSummary(
        tool="ruff",
        error_count=len(data),
        warning_count=0,
        top_categories=top_categories,
    ), ""
