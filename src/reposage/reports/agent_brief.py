"""Agent-actionable brief renderer for RepoSage."""

from __future__ import annotations

from pathlib import PurePosixPath

from reposage.enrichment.models import EnrichmentResult
from reposage.models import AuditReport

_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_LOCK_FILES = {
    "poetry.lock",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "go.sum",
    "Gemfile.lock",
    "composer.lock",
    "uv.lock",
}


def render_agent_brief(report: AuditReport, enrichment: EnrichmentResult | None = None) -> str:
    """Return a Markdown agent brief derived from the audit report and optional enrichment."""
    model_tag = f" · Model: {enrichment.model_id}" if enrichment and enrichment.model_id else ""
    header = (
        f"# Agent Brief: {report.inventory.project_name}\n\n"
        f"> RepoSage · Quality Score: {report.quality.score}/100{model_tag}\n"
    )
    sections = [
        header,
        _render_context(report),
        _render_module_map(enrichment),
        _render_tasks(report, enrichment),
        _render_verification(report),
        _render_do_not_touch(report),
    ]
    return "\n".join(s for s in sections if s)


def _render_context(report: AuditReport) -> str:
    inv = report.inventory
    dep = report.dependencies

    languages = " · ".join(ls.language for ls in inv.languages) or "unknown"
    frameworks = ", ".join(inv.frameworks) if inv.frameworks else "none detected"
    arch_modules = report.architecture.main_modules
    modules = ", ".join(arch_modules[:5]) if arch_modules else "—"
    eco_parts = ", ".join(
        f"{count} {eco} packages" for eco, count in sorted(dep.counts_by_ecosystem.items())
    )
    dep_counts = eco_parts or "none"

    return (
        "## Repository Context\n\n"
        f"- **Stack:** {languages}\n"
        f"- **Frameworks:** {frameworks}\n"
        f"- **Main Modules:** {modules}\n"
        f"- **Dependencies:** {dep_counts}\n"
    )


def _render_module_map(enrichment: EnrichmentResult | None) -> str:
    if not enrichment or not enrichment.module_roles:
        return ""
    rows = "\n".join(
        f"| {r.module} | {r.layer} | {r.responsibility} |" for r in enrichment.module_roles
    )
    return f"## Module Map\n\n| Module | Layer | Responsibility |\n|---|---|---|\n{rows}\n"


_VULN_SEVERITY_ORDER = {"critical": -1, "high": 0, "medium": 1, "low": 2, "unknown": 3}


def _render_tasks(report: AuditReport, enrichment: EnrichmentResult | None) -> str:
    lines: list[str] = []

    if report.security:
        for vuln in sorted(
            report.security.vulnerabilities,
            key=lambda v: _VULN_SEVERITY_ORDER.get(v.severity, 99),
        ):
            fix = f" (fix: {vuln.fix_version})" if vuln.fix_version else ""
            lines.append(f"- [ ] [vuln/{vuln.severity}] {vuln.package} {vuln.cve}{fix}")
        if report.security.coverage_percent is not None and report.security.coverage_percent < 80:
            pct = report.security.coverage_percent
            lines.append(f"- [ ] [signal] Coverage: {pct:.1f}% (below 80% threshold)")

    if enrichment:
        for debt in sorted(
            enrichment.debt_items, key=lambda d: _SEVERITY_ORDER.get(d.severity, 99)
        ):
            lines.append(f"- [ ] [debt/{debt.severity}] {debt.title} — {debt.description}")
        for imp in sorted(enrichment.top_improvements, key=lambda i: i.rank):
            tag = f"[improvement/{imp.effort}] #{imp.rank}: {imp.title}"
            lines.append(f"- [ ] {tag} — {imp.rationale}")
    else:
        for risk in sorted(
            report.risk.items, key=lambda r: _SEVERITY_ORDER.get(str(r.severity), 99)
        ):
            lines.append(f"- [ ] [risk/{risk.severity}] {risk.title} — {risk.rationale}")
        for signal in report.quality.missing_signals:
            lines.append(f"- [ ] [signal] {signal}")

    if not lines:
        lines.append("- [ ] No issues detected — review the full audit report for details")

    return "## Tasks\n\n" + "\n".join(lines) + "\n"


def _render_verification(report: AuditReport) -> str:
    q = report.quality
    commands: list[str] = []

    if q.has_tests:
        commands.append("- `pytest` — run full test suite")

    if q.lint_present:
        if any("ruff" in f for f in q.lint_files):
            commands.append("- `ruff check .` — lint check")
        elif any("eslint" in f for f in q.lint_files):
            commands.append("- `eslint .` — lint check")

    if q.typing_present:
        if any("mypy" in f for f in q.typing_files):
            commands.append("- `mypy src` — type check")
        elif any("tsconfig" in f for f in q.typing_files):
            commands.append("- `tsc --noEmit` — type check")

    if not commands:
        return ""

    return "## Verification\n\n" + "\n".join(commands) + "\n"


def _render_do_not_touch(report: AuditReport) -> str:
    entries: list[str] = []

    if report.quality.ci_present:
        ci_entries: set[str] = set()
        for ci_file in report.quality.ci_files:
            if ".github/workflows" in ci_file:
                ci_entries.add(".github/workflows/")
            else:
                ci_entries.add(PurePosixPath(ci_file).name)
        for entry in sorted(ci_entries):
            entries.append(f"- `{entry}` — CI/CD pipeline configuration")

    seen_pkg: set[str] = set()
    for pf in report.quality.packaging_files:
        fname = PurePosixPath(pf).name
        if fname not in seen_pkg:
            seen_pkg.add(fname)
            entries.append(f"- `{fname}` — package metadata and dependency pins")

    top_entries = set(report.inventory.top_level_entries)
    found_locks = sorted(top_entries & _LOCK_FILES)
    if found_locks:
        joined = ", ".join(f"`{lf}`" for lf in found_locks)
        entries.append(f"- {joined} — lock files (regenerate via package manager)")

    if not entries:
        return ""

    return "## Do Not Touch\n\n" + "\n".join(entries) + "\n"
