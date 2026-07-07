"""RepoSage grades its own repository (opt in via ``tox -e selfaudit``).

This dogfoods the audit engine end to end with the repo's own config
(exclude_globs and all) plus subprocess checks, and pins the real result.

The pinned grade is 6/6. The scanner's own tests plant credential-shaped bait
in scanned test modules, so the repo's config scopes the secret scan away from
tests/ via secrets_exclude_globs; the scope is annotated in the check's
evidence rather than hidden, and this test asserts the annotation is present.
"""

from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path

import pytest

from reposage.standards.config import load_standards_config
from reposage.standards.models import CheckStatus, StandardResult, StandardsReport
from reposage.standards.pipeline import build_standards_report

REPO_ROOT = Path(__file__).resolve().parents[1]


def _standard(report: StandardsReport, number: int) -> StandardResult:
    return next(standard for standard in report.standards if standard.number == number)


def _status(standard: StandardResult, check_id: str) -> CheckStatus:
    return next(check.status for check in standard.checks if check.check_id == check_id)


@pytest.mark.self_audit
def test_self_audit_grade_and_standards() -> None:
    if os.environ.get("REPOSAGE_INNER_AUDIT"):
        pytest.skip("running inside an inner audit; skip to avoid recursion")
    if not (REPO_ROOT / ".git").exists():
        pytest.skip("no .git; self-audit needs the repo's own history")

    config, _ = load_standards_config(REPO_ROOT)
    config = replace(config, run_subprocess_checks=True)
    report = build_standards_report(REPO_ROOT, config)

    assert len(report.standards) == 6

    # Standard 5 (Accountable) is fully satisfied by the observability work:
    # structured logs with a request_id, OpenTelemetry metrics, and an alert rule.
    s5 = _standard(report, 5)
    assert s5.passed, f"S5 should pass; checks: {s5.checks}"
    assert _status(s5, "s5.logs") is CheckStatus.PASS
    assert _status(s5, "s5.metrics") is CheckStatus.PASS
    assert _status(s5, "s5.alerting") is CheckStatus.PASS

    # Reproducible, Legible, Proven, and Shipped all pass.
    for number in (0, 1, 3, 4):
        assert _standard(report, number).passed, f"S{number} should pass"

    # Standard 2 passes with the secret scan visibly scoped away from the
    # scanner's own planted test bait (secrets_exclude_globs in pyproject.toml).
    s2 = _standard(report, 2)
    assert s2.passed, f"S2 should pass; checks: {s2.checks}"
    config_check = next(c for c in s2.checks if c.check_id == "s2.config_external")
    assert config_check.status is CheckStatus.PASS
    assert any("secret scan scoped" in line for line in config_check.evidence)

    assert report.grade == 6
