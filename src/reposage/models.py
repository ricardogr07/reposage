"""Shared dataclasses used across the scan, analysis, and report pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    """Normalized severity values for risk reporting."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(slots=True)
class FileRecord:
    """Metadata collected for one scanned file."""

    path: str
    extension: str | None
    size_bytes: int
    line_count: int


@dataclass(slots=True)
class LanguageStat:
    """Per-language aggregate counts."""

    language: str
    file_count: int
    total_bytes: int


@dataclass(slots=True)
class Dependency:
    """A dependency declared by a repository manifest."""

    name: str
    version_spec: str
    ecosystem: str
    source_file: str
    group: str


@dataclass(slots=True)
class DependencySummary:
    """Collected dependency information for the repository."""

    ecosystems: list[str] = field(default_factory=list)
    manifests: list[str] = field(default_factory=list)
    dependencies: list[Dependency] = field(default_factory=list)
    counts_by_ecosystem: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class RepoInventory:
    """Top-level inventory extracted from the repository.

    Note: only scanned_files is tracked; a reliable total-file count (including
    ignored directories) would require re-walking those directories and is not
    provided.
    """

    project_name: str
    root_path: str
    scanned_files: int
    ignored_directories: list[str] = field(default_factory=list)
    top_level_entries: list[str] = field(default_factory=list)
    languages: list[LanguageStat] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    largest_files: list[FileRecord] = field(default_factory=list)


@dataclass(slots=True)
class QualitySignals:
    """Engineering quality signals inferred from repository contents."""

    score: int
    has_tests: bool
    test_files: list[str] = field(default_factory=list)
    ci_present: bool = False
    ci_files: list[str] = field(default_factory=list)
    documentation_present: bool = False
    documentation_files: list[str] = field(default_factory=list)
    packaging_present: bool = False
    packaging_files: list[str] = field(default_factory=list)
    lint_present: bool = False
    lint_files: list[str] = field(default_factory=list)
    typing_present: bool = False
    typing_files: list[str] = field(default_factory=list)
    checklist: list[str] = field(default_factory=list)
    missing_signals: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ArchitectureSummary:
    """Best-effort architecture observations."""

    main_modules: list[str] = field(default_factory=list)
    probable_layers: list[str] = field(default_factory=list)
    dependency_directions: list[str] = field(default_factory=list)
    god_modules: list[str] = field(default_factory=list)
    hotspots: list[str] = field(default_factory=list)
    architecture_notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RiskItem:
    """A concrete risk observation with a recommended action."""

    title: str
    severity: Severity
    rationale: str
    suggested_action: str


@dataclass(slots=True)
class RiskReport:
    """Risk synthesis based on extracted quality and architecture signals."""

    items: list[RiskItem] = field(default_factory=list)
    refactor_candidates: list[str] = field(default_factory=list)
    weak_points: list[str] = field(default_factory=list)
    issue_suggestions: list[str] = field(default_factory=list)
    roadmap_buckets: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AuditReport:
    """Complete deterministic repository audit."""

    inventory: RepoInventory
    dependencies: DependencySummary
    quality: QualitySignals
    architecture: ArchitectureSummary
    risk: RiskReport

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the report."""

        return asdict(self)
