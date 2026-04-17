"""Orchestration helpers for building RepoSage audit reports."""

from __future__ import annotations

from pathlib import Path

from reposage.analysis.architecture import analyze_architecture
from reposage.analysis.quality import analyze_quality
from reposage.analysis.risk import analyze_risk
from reposage.config import DEFAULT_SCAN_CONFIG, ScanConfig
from reposage.models import AuditReport
from reposage.scan.dependencies import summarize_dependencies
from reposage.scan.filesystem import scan_repository
from reposage.scan.languages import detect_languages
from reposage.scan.repo_meta import build_inventory


def build_audit_report(root: Path, config: ScanConfig | None = None) -> AuditReport:
    """Build a deterministic audit report for ``root``."""

    resolved_root = root.resolve()
    active_config = config or DEFAULT_SCAN_CONFIG

    file_records, ignored_directories = scan_repository(resolved_root, active_config)
    languages = detect_languages(file_records)
    dependencies = summarize_dependencies(resolved_root, file_records)
    inventory = build_inventory(
        resolved_root,
        file_records=file_records,
        ignored_directories=ignored_directories,
        languages=languages,
        dependencies=dependencies,
        config=active_config,
    )
    quality = analyze_quality(resolved_root, file_records)
    architecture = analyze_architecture(
        file_records=file_records,
        top_level_entries=inventory.top_level_entries,
        manifest_paths=dependencies.manifests,
        max_hotspots=active_config.max_hotspots,
    )
    risk = analyze_risk(quality, architecture, dependencies, config=active_config)

    return AuditReport(
        inventory=inventory,
        dependencies=dependencies,
        quality=quality,
        architecture=architecture,
        risk=risk,
    )
