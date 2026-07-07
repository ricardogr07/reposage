"""Markdown rendering for Six Standards audits."""

from __future__ import annotations

from reposage.standards.models import (
    CheckStatus,
    FixItem,
    StandardResult,
    StandardsReport,
)

_STATUS_LABELS = {
    CheckStatus.PASS: "PASS",
    CheckStatus.FAIL: "FAIL",
    CheckStatus.UNCERTAIN: "UNCERTAIN",
    CheckStatus.NOT_APPLICABLE: "N/A",
}


def render_standards_markdown(report: StandardsReport) -> str:
    """Render a deterministic Markdown standards report."""

    grade_line = f"**Grade: {report.grade}/6**"
    if any("skipped by config" in note for note in report.notes):
        grade_line += " (includes checks skipped by config)"

    profile = "general"
    if report.is_ds_repo:
        profile = (
            f"data science / ML ({report.training_files} training, "
            f"{report.serving_files} serving file(s))"
        )

    lines = [
        "# RepoSage Standards Audit",
        "",
        f"- Root path: `{report.root_path}`",
        f"- Profile: {profile}",
        f"- Uncertain checks: {report.uncertain_count}",
        "",
        grade_line,
        "",
    ]

    for standard in report.standards:
        lines.extend(_render_standard(standard))

    lines.extend(_render_fix_list(report.fix_list))

    if report.notes:
        lines.extend(["## Notes", ""])
        lines.extend(f"- {note}" for note in report.notes)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_standard(standard: StandardResult) -> list[str]:
    verdict = "PASS" if standard.passed else "FAIL"
    total = len(standard.checks)
    lines = [
        f"## Standard {standard.number}: {standard.name} - {verdict} "
        f"({standard.passed_count}/{total})",
        "",
        "| Check | Status | Evidence | Remediation |",
        "| --- | --- | --- | --- |",
    ]
    for check in standard.checks:
        status = _STATUS_LABELS[check.status]
        evidence = check.evidence[0] if check.evidence else ""
        lines.append(f"| {check.name} | {status} | {evidence} | {check.remediation} |")
    lines.append("")
    return lines


def _render_fix_list(fix_list: list[FixItem]) -> list[str]:
    lines = ["## Fix list", ""]
    if not fix_list:
        lines.extend(["_No fixes required._", ""])
        return lines
    for index, item in enumerate(fix_list, start=1):
        lines.append(f"{index}. Standard {item.standard} ({item.check_id}): {item.title}")
        if item.priority_note:
            lines.append(f"   Priority: {item.priority_note}")
    lines.append("")
    return lines
