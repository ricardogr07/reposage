"""bandit integration for Python security linting."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from reposage.models import LintSummary
from reposage.security._runner import run_or_load


def scan_bandit(root: Path, src_dir: Path | None = None) -> tuple[LintSummary | None, str]:
    """Run bandit or parse fallback report. Returns (summary, skip_reason)."""
    target = str(src_dir or root)
    cmd = ["bandit", "-r", target, "-f", "json", "-q"]
    fallback = root / "bandit-report.json"
    raw = run_or_load(cmd, fallback)
    if raw is None:
        return None, "not installed and no bandit-report.json found"

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"parse error: {exc}"

    results = data.get("results", [])
    error_count = sum(
        1 for r in results if r.get("issue_severity", "").upper() in ("HIGH", "MEDIUM")
    )
    warning_count = sum(1 for r in results if r.get("issue_severity", "").upper() == "LOW")
    counts = Counter(r.get("issue_type", "") for r in results)
    top_categories = [cat for cat, _ in counts.most_common(3) if cat]

    return LintSummary(
        tool="bandit",
        error_count=error_count,
        warning_count=warning_count,
        top_categories=top_categories,
    ), ""
