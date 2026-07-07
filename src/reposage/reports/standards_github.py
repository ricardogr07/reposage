"""GitHub Actions workflow-command rendering for Six Standards audits."""

from __future__ import annotations

from reposage.standards.models import CheckResult, CheckStatus, StandardsReport

# Non-passing status -> the workflow command that surfaces it as an annotation.
_COMMANDS = {
    CheckStatus.FAIL: "error",
    CheckStatus.UNCERTAIN: "warning",
    CheckStatus.NOT_APPLICABLE: "notice",
}


def render_standards_github(report: StandardsReport) -> str:
    """Render the audit as GitHub Actions workflow-command annotations.

    PASS checks are silent. FAIL/UNCERTAIN/NOT_APPLICABLE become
    ``::error``/``::warning``/``::notice`` lines. A final ``::notice`` reports
    the grade.
    """

    lines: list[str] = []
    for standard in report.standards:
        for check in standard.checks:
            command = _COMMANDS.get(check.status)
            if command is None:
                continue
            title = _escape(f"S{standard.number} {check.name}")
            lines.append(f"::{command} title={title}::{_message(check)}")
    lines.append(f"::notice::RepoSage grade: {report.grade}/6")
    return "\n".join(lines) + "\n"


def _message(check: CheckResult) -> str:
    evidence = check.evidence[0] if check.evidence else ""
    if check.status is CheckStatus.NOT_APPLICABLE:
        return _escape(evidence)
    parts = [part for part in (evidence, check.remediation) if part]
    return _escape(". ".join(parts))


def _escape(text: str) -> str:
    """Escape workflow-command special characters. Percent must go first."""

    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
