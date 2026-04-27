"""Security and quality scan orchestrator."""

from __future__ import annotations

from pathlib import Path

from reposage.models import AuditReport, SecuritySummary
from reposage.security.bandit_scan import scan_bandit
from reposage.security.coverage_parser import parse_coverage
from reposage.security.eslint_scan import scan_eslint
from reposage.security.npm_audit import scan_npm_audit
from reposage.security.pip_audit import scan_pip_audit
from reposage.security.ruff_scan import scan_ruff


def scan_security(root: Path, report: AuditReport) -> SecuritySummary:
    """Run all available security and quality tools. Never raises.

    Uses detected ecosystems from report.dependencies to decide which tools to run.
    All tool failures are recorded in tools_skipped; the scan always completes.
    """
    summary = SecuritySummary()
    ecosystems = set(report.dependencies.ecosystems)

    if "python" in ecosystems:
        _run_pip_audit(root, summary)
        _run_bandit(root, summary)
        _run_ruff(root, summary)

    if "npm" in ecosystems:
        _run_npm_audit(root, summary)
        _run_eslint(root, summary)

    _run_coverage(root, summary)

    return summary


def _run_pip_audit(root: Path, summary: SecuritySummary) -> None:
    try:
        findings, reason = scan_pip_audit(root)
        if reason:
            summary.tools_skipped.append(("pip-audit", reason))
        else:
            summary.vulnerabilities.extend(findings)
            summary.tools_run.append("pip-audit")
    except Exception as exc:  # noqa: BLE001
        summary.tools_skipped.append(("pip-audit", f"unexpected error: {exc}"))


def _run_bandit(root: Path, summary: SecuritySummary) -> None:
    try:
        lint, reason = scan_bandit(root)
        if reason:
            summary.tools_skipped.append(("bandit", reason))
        else:
            if lint is not None:
                summary.lint_summaries.append(lint)
            summary.tools_run.append("bandit")
    except Exception as exc:  # noqa: BLE001
        summary.tools_skipped.append(("bandit", f"unexpected error: {exc}"))


def _run_ruff(root: Path, summary: SecuritySummary) -> None:
    try:
        lint, reason = scan_ruff(root)
        if reason:
            summary.tools_skipped.append(("ruff", reason))
        else:
            if lint is not None:
                summary.lint_summaries.append(lint)
            summary.tools_run.append("ruff")
    except Exception as exc:  # noqa: BLE001
        summary.tools_skipped.append(("ruff", f"unexpected error: {exc}"))


def _run_npm_audit(root: Path, summary: SecuritySummary) -> None:
    try:
        findings, reason = scan_npm_audit(root)
        if reason:
            summary.tools_skipped.append(("npm-audit", reason))
        else:
            summary.vulnerabilities.extend(findings)
            summary.tools_run.append("npm-audit")
    except Exception as exc:  # noqa: BLE001
        summary.tools_skipped.append(("npm-audit", f"unexpected error: {exc}"))


def _run_eslint(root: Path, summary: SecuritySummary) -> None:
    try:
        lint, reason = scan_eslint(root)
        if reason:
            summary.tools_skipped.append(("eslint", reason))
        else:
            if lint is not None:
                summary.lint_summaries.append(lint)
            summary.tools_run.append("eslint")
    except Exception as exc:  # noqa: BLE001
        summary.tools_skipped.append(("eslint", f"unexpected error: {exc}"))


def _run_coverage(root: Path, summary: SecuritySummary) -> None:
    try:
        percent, source = parse_coverage(root)
        summary.coverage_percent = percent
        summary.coverage_source = source
    except Exception as exc:  # noqa: BLE001
        summary.tools_skipped.append(("coverage", f"unexpected error: {exc}"))
