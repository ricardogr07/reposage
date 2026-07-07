"""Tests for the standards Markdown and JSON renderers."""

from __future__ import annotations

import json

from reposage.reports.standards_json import render_standards_json
from reposage.reports.standards_markdown import render_standards_markdown
from reposage.standards.pipeline import build_standards_report


def test_markdown_has_grade_and_six_sections(tmp_path) -> None:
    report = build_standards_report(tmp_path)
    rendered = render_standards_markdown(report)

    assert "# RepoSage Standards Audit" in rendered
    assert "**Grade: 0/6**" in rendered
    for number in range(6):
        assert f"## Standard {number}:" in rendered
    assert "## Fix list" in rendered


def test_json_round_trips(tmp_path) -> None:
    report = build_standards_report(tmp_path)
    payload = json.loads(render_standards_json(report))

    assert payload["grade"] == 0
    assert payload["uncertain_count"] == 18
    assert len(payload["standards"]) == 6
    assert payload["standards"][0]["checks"][0]["status"] == "uncertain"
