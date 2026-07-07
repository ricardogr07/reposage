"""Command-line interface for RepoSage."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from reposage.enrichment.models import EnrichmentResult
from reposage.models import AuditReport
from reposage.pipeline import build_audit_report
from reposage.reports.json_report import render_json_report
from reposage.reports.markdown import render_markdown_report


def build_parser() -> argparse.ArgumentParser:
    """Construct the RepoSage CLI parser."""

    parser = argparse.ArgumentParser(
        prog="reposage",
        description="Generate deterministic repository audits.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    report_parser = subparsers.add_parser("report", help="Render a repository report.")
    report_parser.add_argument("path", help="Path to the repository to analyze.")
    report_parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format.",
    )
    report_parser.add_argument("--output", help="Optional path for report output.")
    report_parser.add_argument(
        "--enrich",
        action="store_true",
        default=False,
        help="Enrich the report with AI analysis (requires ANTHROPIC_API_KEY and reposage[ai]).",
    )
    report_parser.add_argument(
        "--agent-file",
        metavar="PATH",
        default=None,
        help="Write an agent-actionable brief to PATH (e.g. AGENTS.md, CLAUDE.md).",
    )
    report_parser.add_argument(
        "--security",
        action="store_true",
        default=False,
        help="Run security and quality tool integrations (pip-audit, bandit, ruff, npm audit, eslint).",  # noqa: E501
    )
    report_parser.add_argument(
        "--api-surface",
        action="store_true",
        default=False,
        help="Analyze Python public API surface and detect breaking changes.",
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Run the default human-readable audit workflow.",
    )
    run_parser.add_argument("path", help="Path to the repository to analyze.")
    run_parser.add_argument("--output", help="Optional path for Markdown output.")
    run_parser.add_argument(
        "--enrich",
        action="store_true",
        default=False,
        help="Enrich the report with AI analysis (requires ANTHROPIC_API_KEY and reposage[ai]).",
    )
    run_parser.add_argument(
        "--agent-file",
        metavar="PATH",
        default=None,
        help="Write an agent-actionable brief to PATH (e.g. AGENTS.md, CLAUDE.md).",
    )
    run_parser.add_argument(
        "--security",
        action="store_true",
        default=False,
        help="Run security and quality tool integrations (pip-audit, bandit, ruff, npm audit, eslint).",  # noqa: E501
    )
    run_parser.add_argument(
        "--api-surface",
        action="store_true",
        default=False,
        help="Analyze Python public API surface and detect breaking changes.",
    )

    audit_parser = subparsers.add_parser(
        "audit",
        help="Grade a repository against the Six Standards.",
    )
    audit_parser.add_argument("path", help="Path to the repository to audit.")
    audit_parser.add_argument(
        "--format",
        choices=("markdown", "json", "github"),
        default="markdown",
        help="Output format.",
    )
    audit_parser.add_argument("--output", help="Optional path for audit output.")
    audit_parser.add_argument(
        "--run-subprocess-checks",
        action="store_true",
        default=False,
        help="Allow checks that shell out (pytest, dependency install) to run.",
    )
    audit_parser.add_argument(
        "--fail-under",
        type=int,
        default=0,
        help="Exit non-zero when the grade is below this value.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    parser = build_parser()
    args = parser.parse_args(argv)
    target_path = Path(args.path)

    if not target_path.exists():
        print(f"error: path does not exist: {target_path}", file=sys.stderr)
        return 2
    if not target_path.is_dir():
        print(f"error: path is not a directory: {target_path}", file=sys.stderr)
        return 2

    if args.command == "audit":
        from reposage.standards._cli import run_audit

        return run_audit(args)

    report = build_audit_report(target_path)

    if getattr(args, "security", False):
        from reposage.security.scan import scan_security

        report.security = scan_security(target_path, report)

    if getattr(args, "api_surface", False):
        from reposage.api.surface import analyze_api_surface

        report.api_surface = analyze_api_surface(target_path, report)

    enrichment = None
    if getattr(args, "enrich", False):
        enrichment = _run_enrichment(report)
        if enrichment is None:
            return 2

    if args.command == "report":
        output = (
            render_markdown_report(report, enrichment=enrichment)
            if args.format == "markdown"
            else render_json_report(report, enrichment=enrichment)
        )
    else:
        output = render_markdown_report(report, enrichment=enrichment)

    output_path = getattr(args, "output", None)
    if output_path:
        Path(output_path).write_text(output, encoding="utf-8")
    else:
        print(output)

    agent_file = getattr(args, "agent_file", None)
    if agent_file is not None:
        from reposage.reports.agent_brief import render_agent_brief

        Path(agent_file).write_text(render_agent_brief(report, enrichment), encoding="utf-8")

    return 0


def _run_enrichment(report: AuditReport) -> EnrichmentResult | None:
    """Validate prerequisites and run enrichment; return None on failure."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "error: --enrich requires ANTHROPIC_API_KEY to be set",
            file=sys.stderr,
        )
        return None

    try:
        import anthropic as _anthropic_check  # noqa: F401
    except ImportError:
        print(
            "error: --enrich requires the 'anthropic' package. "
            "Install it with: pip install 'reposage[ai]'",
            file=sys.stderr,
        )
        return None

    from reposage.enrichment.anthropic_provider import AnthropicEnricher
    from reposage.enrichment.provider import enrich_report

    enricher = AnthropicEnricher()
    return enrich_report(report, enricher)
