"""Tests for the standards Markdown and JSON renderers."""

from __future__ import annotations

import json

from reposage.reports.standards_github import render_standards_github
from reposage.reports.standards_json import render_standards_json
from reposage.reports.standards_markdown import render_standards_markdown
from reposage.standards.models import (
    CheckResult,
    CheckStatus,
    StandardsReport,
    build_standard_result,
)
from reposage.standards.pipeline import build_standards_report


def _github_report(checks: list[CheckResult], grade: int = 0) -> StandardsReport:
    standard = build_standard_result(0, "Reproducible", checks)
    return StandardsReport(
        root_path=".",
        standards=[standard],
        grade=grade,
        fix_list=[],
        uncertain_count=0,
        subprocess_checks_ran=False,
    )


def test_markdown_has_grade_and_six_sections(tmp_path) -> None:
    report = build_standards_report(tmp_path)
    rendered = render_standards_markdown(report)

    assert "# RepoSage Standards Audit" in rendered
    assert f"**Grade: {report.grade}/6**" in rendered
    for number in range(6):
        assert f"## Standard {number}:" in rendered
    assert "## Fix list" in rendered


def test_markdown_profile_line_general(tmp_path) -> None:
    rendered = render_standards_markdown(build_standards_report(tmp_path))

    assert "- Profile: general" in rendered


def test_markdown_profile_line_ds(tmp_path) -> None:
    (tmp_path / "train.py").write_text("import sklearn\n", encoding="utf-8")
    rendered = render_standards_markdown(build_standards_report(tmp_path))

    assert "- Profile: data science / ML (1 training, 0 serving file(s))" in rendered


def test_json_includes_ds_profile(tmp_path) -> None:
    (tmp_path / "train.py").write_text("import sklearn\n", encoding="utf-8")
    payload = json.loads(render_standards_json(build_standards_report(tmp_path)))

    assert payload["is_ds_repo"] is True
    assert payload["training_files"] == 1
    assert payload["serving_files"] == 0


def test_json_round_trips(tmp_path) -> None:
    report = build_standards_report(tmp_path)
    payload = json.loads(render_standards_json(report))

    assert payload["grade"] == sum(1 for standard in payload["standards"] if standard["passed"])
    assert payload["uncertain_count"] == report.uncertain_count
    assert len(payload["standards"]) == 6
    statuses = {
        check["status"] for standard in payload["standards"] for check in standard["checks"]
    }
    assert statuses <= {"pass", "fail", "uncertain", "not_applicable"}


def test_github_renderer_emits_annotations() -> None:
    checks = [
        CheckResult("s0.a", "Env spec", CheckStatus.FAIL, ["missing thing"], "Add it."),
        CheckResult("s0.b", "Determinism", CheckStatus.UNCERTAIN, ["inconclusive"], "Re-run."),
        CheckResult("s0.c", "Gate", CheckStatus.NOT_APPLICABLE, ["not a model repo"], "n/a rem"),
        CheckResult("s0.d", "Ok", CheckStatus.PASS, ["fine"]),
    ]
    out = render_standards_github(_github_report(checks, grade=3))

    assert "::error title=S0 Env spec::missing thing. Add it." in out
    assert "::warning title=S0 Determinism::inconclusive. Re-run." in out
    assert "::notice title=S0 Gate::not a model repo" in out
    assert "n/a rem" not in out  # NOT_APPLICABLE uses evidence only, not remediation
    assert "Ok" not in out  # PASS checks are silent
    assert "::notice::RepoSage grade: 3/6" in out


def test_github_renderer_escapes_special_chars() -> None:
    check = CheckResult("s0.a", "X", CheckStatus.FAIL, ["100% down\r\nhere"], "fix")
    out = render_standards_github(_github_report([check]))

    assert "100%25 down%0D%0Ahere. fix" in out
    assert "100% down" not in out
