"""Tests for the agent brief renderer."""

from __future__ import annotations

from reposage.cli import main
from reposage.enrichment.models import EnrichmentResult
from reposage.reports.agent_brief import render_agent_brief
from tests.conftest import fixture_path, make_enrichment, make_report


def test_lightweight_contains_context() -> None:
    report = make_report()
    brief = render_agent_brief(report)

    assert f"# Agent Brief: {report.inventory.project_name}" in brief
    assert f"Quality Score: {report.quality.score}/100" in brief
    assert "## Repository Context" in brief
    assert "## Tasks" in brief


def test_lightweight_tasks_from_risk() -> None:
    report = make_report()
    brief = render_agent_brief(report)

    if report.risk.items:
        assert "[risk/" in brief


def test_missing_signals_become_tasks() -> None:
    report = make_report()
    brief = render_agent_brief(report)

    for signal in report.quality.missing_signals:
        assert f"[signal] {signal}" in brief


def test_enriched_uses_debt_and_improvements() -> None:
    report = make_report()
    enrichment = make_enrichment(debts=2, improvements=3)
    brief = render_agent_brief(report, enrichment=enrichment)

    assert "[debt/medium] Debt 0" in brief
    assert "[improvement/low] #1: Improve 0" in brief


def test_module_map_omitted_without_enrichment() -> None:
    report = make_report()
    brief = render_agent_brief(report)

    assert "## Module Map" not in brief


def test_module_map_present_with_enrichment() -> None:
    report = make_report()
    enrichment = make_enrichment(roles=2)
    brief = render_agent_brief(report, enrichment=enrichment)

    assert "## Module Map" in brief
    assert "| Module | Layer | Responsibility |" in brief
    assert "src/mod0" in brief


def test_model_id_in_header_when_enriched() -> None:
    report = make_report()
    enrichment = make_enrichment()
    brief = render_agent_brief(report, enrichment=enrichment)

    assert "claude-haiku-4-5-20251001" in brief


def test_do_not_touch_section_present() -> None:
    report = make_report()
    brief = render_agent_brief(report)

    assert "## Do Not Touch" in brief


def test_do_not_touch_lists_ci_when_ci_present() -> None:
    report = make_report()
    brief = render_agent_brief(report)

    if report.quality.ci_present:
        assert "CI/CD" in brief


def test_verification_present_when_tests_exist() -> None:
    report = make_report()
    brief = render_agent_brief(report)

    if report.quality.has_tests:
        assert "## Verification" in brief
        assert "pytest" in brief


def test_empty_enrichment_falls_back_gracefully() -> None:
    report = make_report()
    enrichment = EnrichmentResult()
    brief = render_agent_brief(report, enrichment=enrichment)

    assert "## Tasks" in brief
    assert "No issues detected" in brief


def test_cli_agent_file_flag_writes_file(tmp_path) -> None:
    out_file = tmp_path / "AGENTS.md"
    exit_code = main(["report", str(fixture_path("python_repo")), "--agent-file", str(out_file)])

    assert exit_code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "# Agent Brief: python_repo" in content
    assert "## Tasks" in content


def test_cli_agent_file_independent_of_format(tmp_path) -> None:
    out_file = tmp_path / "CLAUDE.md"
    report_file = tmp_path / "report.json"
    exit_code = main(
        [
            "report",
            str(fixture_path("python_repo")),
            "--format",
            "json",
            "--output",
            str(report_file),
            "--agent-file",
            str(out_file),
        ]
    )

    assert exit_code == 0
    assert report_file.exists()
    assert out_file.exists()
    assert "# Agent Brief" in out_file.read_text(encoding="utf-8")
