"""RepoSage grades its own repository (opt in via ``tox -e selfaudit``).

This is a structural self-audit: it dogfoods the audit engine end to end with
the repo's own config (exclude_globs and all) plus subprocess checks. For now it
only asserts the shape of the result. The exact grade gets pinned in a later
commit, once the observability work lands and stabilizes S5.
"""

from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path

import pytest

from reposage.standards.config import load_standards_config
from reposage.standards.pipeline import build_standards_report

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.self_audit
def test_self_audit_structure() -> None:
    if os.environ.get("REPOSAGE_INNER_AUDIT"):
        pytest.skip("running inside an inner audit; skip to avoid recursion")
    if not (REPO_ROOT / ".git").exists():
        pytest.skip("no .git; self-audit needs the repo's own history")

    config, _ = load_standards_config(REPO_ROOT)
    config = replace(config, run_subprocess_checks=True)
    report = build_standards_report(REPO_ROOT, config)

    assert len(report.standards) == 6
    assert isinstance(report.grade, int)
    assert 0 <= report.grade <= 6

    s1 = next(standard for standard in report.standards if standard.number == 1)
    assert s1.passed, f"S1 (Legible) should pass; checks: {s1.checks}"
