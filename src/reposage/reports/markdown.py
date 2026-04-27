"""Markdown rendering for RepoSage audits."""

from __future__ import annotations

from reposage.enrichment.models import EnrichmentResult
from reposage.models import AuditReport, Dependency, LanguageStat, SecuritySummary


def render_markdown_report(report: AuditReport, enrichment: EnrichmentResult | None = None) -> str:
    """Render a deterministic Markdown report."""

    inventory = report.inventory
    dependency_summary = report.dependencies
    quality = report.quality
    architecture = report.architecture
    risk = report.risk

    lines = [
        f"# RepoSage Audit: {inventory.project_name}",
        "",
        "## Project Summary",
        f"- Root path: `{inventory.root_path}`",
        f"- Scanned files: {inventory.scanned_files}",
        f"- Ignored directories: {_format_list(inventory.ignored_directories)}",
        f"- Top-level layout: {_format_list(inventory.top_level_entries)}",
        f"- Languages: {_format_languages(inventory.languages)}",
        f"- Framework signals: {_format_list(inventory.frameworks)}",
        f"- Dependency ecosystems: {_format_list(dependency_summary.ecosystems)}",
        f"- Dependency manifests: {_format_list(dependency_summary.manifests)}",
        "",
        "## Architecture Guess",
        f"- Main modules: {_format_list(architecture.main_modules)}",
        f"- Probable layers: {_format_list(architecture.probable_layers)}",
        f"- Dependency directions: {_format_list(architecture.dependency_directions)}",
        f"- Possible god modules: {_format_list(architecture.god_modules)}",
        f"- Hotspots: {_format_list(architecture.hotspots)}",
        f"- Notes: {_format_list(architecture.architecture_notes)}",
        "",
        "## Engineering Quality Checklist",
        f"- Quality score: {quality.score}/100",
        f"- Positive signals: {_format_list(quality.checklist)}",
        f"- Missing signals: {_format_list(quality.missing_signals)}",
        f"- Test files: {_format_list(quality.test_files)}",
        f"- CI files: {_format_list(quality.ci_files)}",
        f"- Docs files: {_format_list(quality.documentation_files)}",
        f"- Packaging files: {_format_list(quality.packaging_files)}",
        f"- Lint files: {_format_list(quality.lint_files)}",
        f"- Typing files: {_format_list(quality.typing_files)}",
        "",
        "## Risk Hotspots",
    ]

    for item in risk.items:
        lines.extend(
            [
                f"- [{item.severity}] {item.title}: {item.rationale}",
                f"  Suggested action: {item.suggested_action}",
            ]
        )

    lines.extend(
        [
            "",
            "## Recommended Next Issues",
            *[f"1. {suggestion}" for suggestion in risk.issue_suggestions],
            "",
            "## Dependency Summary",
            *[f"- {entry}" for entry in _format_dependencies(dependency_summary.dependencies[:15])],
        ]
    )

    if report.security is not None:
        lines.extend(["", *_render_security(report.security).splitlines()])

    if enrichment is not None:
        lines.extend(_render_enrichment(enrichment))

    return "\n".join(lines).rstrip() + "\n"


def _render_security(security: SecuritySummary) -> str:
    lines = ["## Security & Quality", ""]

    if security.coverage_percent is not None:
        lines.append(f"**Coverage:** {security.coverage_percent:.1f}% ({security.coverage_source})")
        lines.append("")

    if security.vulnerabilities:
        lines += ["### Vulnerabilities", ""]
        lines.append("| Package | Ecosystem | Severity | CVE | Fix |")
        lines.append("|---|---|---|---|---|")
        for v in security.vulnerabilities:
            fix = v.fix_version or "none"
            lines.append(f"| {v.package} | {v.ecosystem} | {v.severity} | {v.cve} | {fix} |")
        lines.append("")

    if security.lint_summaries:
        lines += ["### Lint Findings", ""]
        lines.append("| Tool | Errors | Warnings | Top Categories |")
        lines.append("|---|---|---|---|")
        for ls in security.lint_summaries:
            cats = ", ".join(ls.top_categories) or "—"
            lines.append(f"| {ls.tool} | {ls.error_count} | {ls.warning_count} | {cats} |")
        lines.append("")

    if security.tools_skipped:
        lines += ["### Skipped Tools", ""]
        for name, reason in security.tools_skipped:
            lines.append(f"- `{name}`: {reason}")
        lines.append("")

    return "\n".join(lines)


def _render_enrichment(enrichment: EnrichmentResult) -> list[str]:
    out: list[str] = ["", "## Module Responsibilities", ""]

    if enrichment.module_roles:
        out.append("| Module | Layer | Responsibility |")
        out.append("| --- | --- | --- |")
        for role in enrichment.module_roles:
            out.append(f"| `{role.module}` | {role.layer} | {role.responsibility} |")
    else:
        out.append("_(no module roles returned)_")

    out += ["", "## Technical Debt", ""]
    if enrichment.debt_items:
        for item in enrichment.debt_items:
            severity_label = f"[{item.severity.upper()}]"
            out.append(f"### {severity_label} {item.title}")
            out.append("")
            out.append(item.description)
            out.append("")
            out.append(f"**GitHub issue title:** {item.issue_title}")
            out.append("")
            out.append("<details><summary>Issue body</summary>")
            out.append("")
            out.append(item.issue_body)
            out.append("")
            out.append("</details>")
            out.append("")
    else:
        out.append("_(no debt items returned)_")

    out += ["", "## Top 5 Improvements", ""]
    for imp in enrichment.top_improvements:
        effort_label = f"(effort: {imp.effort})"
        out.append(f"{imp.rank}. **{imp.title}** {effort_label}")
        out.append(f"   {imp.rationale}")
        out.append("")

    return out


def _format_list(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


def _format_languages(values: list[LanguageStat]) -> str:
    if not values:
        return "none"
    return ", ".join(f"{item.language} ({item.file_count})" for item in values)


def _format_dependencies(values: list[Dependency]) -> list[str]:
    if not values:
        return ["none"]
    return [
        (
            f"{dependency.name} {dependency.version_spec} "
            f"[{dependency.ecosystem}/{dependency.group}] from {dependency.source_file}"
        )
        for dependency in values
    ]
