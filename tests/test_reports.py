"""Report rendering tests."""

from __future__ import annotations

import json

from reposage.pipeline import build_audit_report
from reposage.reports.json_report import render_json_report
from reposage.reports.markdown import render_markdown_report
from tests.conftest import fixture_path


def test_markdown_report_contains_expected_sections() -> None:
    report = build_audit_report(fixture_path("python_repo"))
    rendered = render_markdown_report(report)

    assert "## Project Summary" in rendered
    assert "## Architecture Guess" in rendered
    assert "## Engineering Quality Checklist" in rendered
    assert "## Risk Hotspots" in rendered
    assert "## Recommended Next Issues" in rendered


def test_json_report_has_expected_shape() -> None:
    report = build_audit_report(fixture_path("python_repo"))
    payload = json.loads(render_json_report(report))

    expected_keys = {"architecture", "dependencies", "inventory", "quality", "risk", "security"}
    assert set(payload) == expected_keys
    assert payload["inventory"]["project_name"] == "python_repo"
    assert payload["quality"]["has_tests"] is True
