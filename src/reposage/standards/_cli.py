"""CLI handler for the ``audit`` subcommand, kept out of the main cli module."""

from __future__ import annotations

import argparse
import os
from dataclasses import replace
from pathlib import Path

from reposage.reports.standards_github import render_standards_github
from reposage.reports.standards_json import render_standards_json
from reposage.reports.standards_markdown import render_standards_markdown
from reposage.standards.config import load_standards_config
from reposage.standards.pipeline import build_standards_report


def run_audit(args: argparse.Namespace) -> int:
    """Run the Six Standards audit and return an exit code."""

    root = Path(args.path)
    config, warnings = load_standards_config(root)
    if args.run_subprocess_checks:
        config = replace(config, run_subprocess_checks=True)

    report = build_standards_report(root, config)
    if warnings:
        report.notes = [*warnings, *report.notes]

    if args.format == "json":
        output = render_standards_json(report)
    elif args.format == "github":
        output = render_standards_github(report)
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with Path(summary).open("a", encoding="utf-8") as handle:
                handle.write(render_standards_markdown(report))
    else:
        output = render_standards_markdown(report)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)

    return 1 if report.grade < args.fail_under else 0
