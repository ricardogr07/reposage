"""Tests for M8 security and quality tool integrations."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from reposage.cli import main
from reposage.models import SecuritySummary
from reposage.security._runner import run_or_load, run_tool
from reposage.security.bandit_scan import scan_bandit
from reposage.security.coverage_parser import parse_coverage
from reposage.security.eslint_scan import scan_eslint
from reposage.security.npm_audit import scan_npm_audit
from reposage.security.pip_audit import scan_pip_audit
from reposage.security.ruff_scan import scan_ruff
from reposage.security.scan import scan_security
from tests.conftest import fixture_path, make_report

SECURITY_FIXTURES = Path(__file__).parent / "fixtures" / "security"


# --- runner ---


def test_run_tool_returns_none_for_missing_command() -> None:
    result = run_tool(["__nonexistent_tool_xyz__"])
    assert result is None


def test_run_or_load_uses_fallback_file(tmp_path: Path) -> None:
    fallback = tmp_path / "fallback.json"
    fallback.write_text('{"ok": true}', encoding="utf-8")
    result = run_or_load(["__nonexistent_tool_xyz__"], fallback)
    assert result == '{"ok": true}'


def test_run_or_load_returns_none_when_no_tool_and_no_file(tmp_path: Path) -> None:
    result = run_or_load(["__nonexistent_tool_xyz__"], tmp_path / "missing.json")
    assert result is None


# --- pip-audit ---


def test_parse_pip_audit_fixture(tmp_path: Path) -> None:
    from unittest.mock import patch

    fixture_content = (SECURITY_FIXTURES / "pip-audit-report.json").read_text(encoding="utf-8")
    with patch("reposage.security.pip_audit.run_or_load", return_value=fixture_content):
        findings, skip_reason = scan_pip_audit(tmp_path)
    assert skip_reason == ""
    assert len(findings) == 2
    assert all(f.ecosystem == "python" for f in findings)
    packages = {f.package for f in findings}
    assert packages == {"requests", "urllib3"}


def test_parse_pip_audit_empty_vulns(tmp_path: Path) -> None:
    (tmp_path / "pip-audit-report.json").write_text(
        json.dumps({"dependencies": []}), encoding="utf-8"
    )
    findings, skip_reason = scan_pip_audit(tmp_path)
    assert findings == []
    assert skip_reason == ""


def test_parse_pip_audit_missing_returns_skip_reason(tmp_path: Path) -> None:
    findings, skip_reason = scan_pip_audit(tmp_path)
    assert findings == []
    assert skip_reason != ""


# --- bandit ---


def test_parse_bandit_fixture(tmp_path: Path) -> None:
    shutil.copy(SECURITY_FIXTURES / "bandit-report.json", tmp_path / "bandit-report.json")
    lint, skip_reason = scan_bandit(tmp_path)
    assert skip_reason == ""
    assert lint is not None
    assert lint.tool == "bandit"
    assert lint.error_count == 2  # HIGH + MEDIUM
    assert lint.warning_count == 1  # LOW


def test_parse_bandit_invalid_json(tmp_path: Path) -> None:
    (tmp_path / "bandit-report.json").write_text("not json", encoding="utf-8")
    lint, skip_reason = scan_bandit(tmp_path)
    assert lint is None
    assert "parse error" in skip_reason


# --- npm audit ---


def test_parse_npm_audit_fixture(tmp_path: Path) -> None:
    from unittest.mock import patch

    fixture_content = (SECURITY_FIXTURES / "npm-audit.json").read_text(encoding="utf-8")
    with patch("reposage.security.npm_audit.run_or_load", return_value=fixture_content):
        findings, skip_reason = scan_npm_audit(tmp_path)
    assert skip_reason == ""
    assert len(findings) == 1
    vuln = findings[0]
    assert vuln.ecosystem == "npm"
    assert vuln.severity == "high"
    assert vuln.package == "lodash"


# --- eslint ---


def test_parse_eslint_fixture(tmp_path: Path) -> None:
    from unittest.mock import patch

    fixture_content = (SECURITY_FIXTURES / "eslint-report.json").read_text(encoding="utf-8")
    with patch("reposage.security.eslint_scan.run_or_load", return_value=fixture_content):
        lint, skip_reason = scan_eslint(tmp_path)
    assert skip_reason == ""
    assert lint is not None
    assert lint.error_count == 1
    assert lint.warning_count == 2


# --- ruff ---


def test_parse_ruff_fixture(tmp_path: Path) -> None:
    from unittest.mock import patch

    fixture_content = (SECURITY_FIXTURES / "ruff-report.json").read_text(encoding="utf-8")
    # Patch run_or_load to return fixture content regardless of whether ruff is installed
    with patch("reposage.security.ruff_scan.run_or_load", return_value=fixture_content):
        lint, skip_reason = scan_ruff(tmp_path)
    assert skip_reason == ""
    assert lint is not None
    assert lint.error_count == 4
    assert lint.warning_count == 0
    assert "security" in lint.top_categories


# --- coverage ---


def test_parse_coverage_xml_fixture(tmp_path: Path) -> None:
    shutil.copy(SECURITY_FIXTURES / "coverage.xml", tmp_path / "coverage.xml")
    percent, source = parse_coverage(tmp_path)
    assert source == "coverage.xml"
    assert percent == pytest.approx(82.0)


def test_parse_lcov_fixture(tmp_path: Path) -> None:
    shutil.copy(SECURITY_FIXTURES / "lcov.info", tmp_path / "lcov.info")
    percent, source = parse_coverage(tmp_path)
    assert source == "lcov.info"
    # LH:150+2=152, LF:200+2=202 → 152/202*100 ≈ 75.25
    assert percent == pytest.approx(75.25, abs=0.1)


def test_parse_coverage_returns_none_for_empty_dir(tmp_path: Path) -> None:
    percent, source = parse_coverage(tmp_path)
    assert percent is None
    assert source == ""


def test_parse_coverage_xml_wins_over_lcov(tmp_path: Path) -> None:
    shutil.copy(SECURITY_FIXTURES / "coverage.xml", tmp_path / "coverage.xml")
    shutil.copy(SECURITY_FIXTURES / "lcov.info", tmp_path / "lcov.info")
    percent, source = parse_coverage(tmp_path)
    assert source == "coverage.xml"


# --- scan orchestrator ---


def test_scan_security_returns_valid_summary_when_all_tools_skipped(tmp_path: Path) -> None:
    report = make_report()
    report.dependencies.ecosystems = []  # no ecosystems → no tools attempted
    result = scan_security(tmp_path, report)
    assert isinstance(result, SecuritySummary)
    assert result.vulnerabilities == []
    assert result.lint_summaries == []


def test_scan_security_reads_pip_audit_fallback(tmp_path: Path) -> None:
    shutil.copy(SECURITY_FIXTURES / "pip-audit-report.json", tmp_path / "pip-audit-report.json")
    report = make_report()
    report.dependencies.ecosystems = ["python"]
    result = scan_security(tmp_path, report)
    assert "pip-audit" in result.tools_run
    assert len(result.vulnerabilities) == 2


def test_scan_security_skips_npm_tools_for_python_only_repo(tmp_path: Path) -> None:
    report = make_report()
    report.dependencies.ecosystems = ["python"]
    result = scan_security(tmp_path, report)
    assert "npm-audit" not in result.tools_run
    assert "eslint" not in result.tools_run


# --- CLI integration ---


def test_cli_security_flag_exits_zero() -> None:
    exit_code = main(["report", str(fixture_path("python_repo")), "--security"])
    assert exit_code == 0


def test_cli_security_flag_independent_of_format(tmp_path: Path) -> None:
    out_file = tmp_path / "report.json"
    exit_code = main(
        [
            "report",
            str(fixture_path("python_repo")),
            "--format",
            "json",
            "--output",
            str(out_file),
            "--security",
        ]
    )
    assert exit_code == 0
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert "security" in payload
