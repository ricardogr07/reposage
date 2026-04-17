"""Risk synthesis based on deterministic RepoSage signals."""

from __future__ import annotations

from reposage.config import ScanConfig
from reposage.models import (
    ArchitectureSummary,
    DependencySummary,
    QualitySignals,
    RiskItem,
    RiskReport,
    Severity,
)


def analyze_risk(
    quality: QualitySignals,
    architecture: ArchitectureSummary,
    dependencies: DependencySummary,
    config: ScanConfig | None = None,
) -> RiskReport:
    """Build a concise risk report from quality and architecture signals."""

    active_config = config or ScanConfig()
    items: list[RiskItem] = []
    refactor_candidates = list(architecture.god_modules[:3])
    weak_points = list(quality.missing_signals)
    issue_suggestions: list[str] = []
    roadmap_buckets: list[str] = []

    if not quality.has_tests:
        items.append(
            RiskItem(
                title="Low regression confidence",
                severity=Severity.HIGH,
                rationale=(
                    "No automated tests were detected, so behavior changes may be hard to verify."
                ),
                suggested_action=("Add a minimal smoke test suite around the highest-risk paths."),
            )
        )
        issue_suggestions.append("Create a baseline automated test suite for critical workflows.")
        roadmap_buckets.append("Build confidence")

    if not quality.ci_present:
        items.append(
            RiskItem(
                title="No CI enforcement",
                severity=Severity.HIGH,
                rationale="Without CI, linting, typing, and tests depend on manual discipline.",
                suggested_action="Add a CI workflow that runs lint, type checks, and core tests.",
            )
        )
        issue_suggestions.append("Introduce CI checks for linting, typing, and tests.")
        roadmap_buckets.append("Automate quality")

    if architecture.god_modules:
        items.append(
            RiskItem(
                title="Large modules detected",
                severity=Severity.MEDIUM,
                rationale=(
                    "The largest files are large enough to become coordination and review hotspots."
                ),
                suggested_action=(
                    "Split oversized modules by responsibility and add focused tests "
                    "around the seams."
                ),
            )
        )
        issue_suggestions.append(
            "Refactor the largest modules into smaller, responsibility-focused units."
        )
        roadmap_buckets.append("Clarify architecture")

    if not quality.documentation_present:
        items.append(
            RiskItem(
                title="Documentation gaps",
                severity=Severity.MEDIUM,
                rationale="Missing docs increase onboarding and maintenance cost.",
                suggested_action=(
                    "Add a README and targeted docs for core workflows and architecture."
                ),
            )
        )
        issue_suggestions.append(
            "Document the core architecture, setup flow, and operating assumptions."
        )
        roadmap_buckets.append("Improve onboarding")

    if len(dependencies.dependencies) >= active_config.dependency_count_risk_threshold:
        items.append(
            RiskItem(
                title="Dependency surface area is growing",
                severity=Severity.LOW,
                rationale=(
                    "A larger dependency set increases upgrade and security maintenance cost."
                ),
                suggested_action=(
                    "Review dependencies for overlap, abandoned packages, and version sprawl."
                ),
            )
        )
        issue_suggestions.append("Audit and rationalize the dependency set.")
        roadmap_buckets.append("Manage dependencies")

    if not items:
        items.append(
            RiskItem(
                title="No major structural risks detected",
                severity=Severity.LOW,
                rationale="RepoSage found the baseline quality signals expected for a healthy MVP.",
                suggested_action=(
                    "Keep the current quality bar and expand coverage as the codebase grows."
                ),
            )
        )
        issue_suggestions.append("Preserve the current quality baseline as new modules are added.")
        roadmap_buckets.append("Sustain quality")

    return RiskReport(
        items=items,
        refactor_candidates=refactor_candidates,
        weak_points=weak_points,
        issue_suggestions=issue_suggestions[:5],
        roadmap_buckets=sorted(set(roadmap_buckets)),
    )
