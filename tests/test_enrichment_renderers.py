"""Tests for Markdown and JSON renderers with enrichment output."""

from __future__ import annotations

import json

from reposage.enrichment.models import EnrichmentResult
from reposage.reports.json_report import render_json_report
from reposage.reports.markdown import render_markdown_report
from tests.conftest import make_enrichment, make_report


def test_markdown_report_with_enrichment_contains_new_sections() -> None:
    report = make_report()
    enrichment = make_enrichment()
    rendered = render_markdown_report(report, enrichment=enrichment)

    assert "## Module Responsibilities" in rendered
    assert "## Technical Debt" in rendered
    assert "## Top 5 Improvements" in rendered


def test_markdown_report_without_enrichment_has_no_enrichment_sections() -> None:
    report = make_report()
    rendered = render_markdown_report(report)

    assert "## Module Responsibilities" not in rendered
    assert "## Technical Debt" not in rendered


def test_markdown_enrichment_empty_roles_shows_placeholder() -> None:
    report = make_report()
    enrichment = EnrichmentResult()
    rendered = render_markdown_report(report, enrichment=enrichment)

    assert "_(no module roles returned)_" in rendered
    assert "_(no debt items returned)_" in rendered


def test_markdown_enrichment_shows_role_table() -> None:
    report = make_report()
    enrichment = make_enrichment(roles=1)
    rendered = render_markdown_report(report, enrichment=enrichment)

    assert "| Module | Layer | Responsibility |" in rendered
    assert "src/mod0" in rendered


def test_markdown_enrichment_shows_improvements() -> None:
    report = make_report()
    enrichment = make_enrichment(improvements=5)
    rendered = render_markdown_report(report, enrichment=enrichment)

    assert "1. **Improve 0**" in rendered


def test_json_report_without_enrichment_has_no_enrichment_key() -> None:
    report = make_report()
    payload = json.loads(render_json_report(report))
    assert "enrichment" not in payload


def test_json_report_with_enrichment_has_enrichment_key() -> None:
    report = make_report()
    enrichment = make_enrichment()
    payload = json.loads(render_json_report(report, enrichment=enrichment))

    assert "enrichment" in payload
    assert "module_roles" in payload["enrichment"]
    assert "debt_items" in payload["enrichment"]
    assert "top_improvements" in payload["enrichment"]
