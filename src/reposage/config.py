"""Shared configuration defaults for RepoSage scans."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_IGNORED_DIRECTORIES = frozenset(
    {
        ".git",
        ".hg",
        ".idea",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".svn",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "htmlcov",
        "node_modules",
        "site",
        "target",
        "venv",
    }
)


@dataclass(frozen=True, slots=True)
class ScanConfig:
    """Stable configuration for filesystem scanning."""

    ignored_directories: frozenset[str] = DEFAULT_IGNORED_DIRECTORIES
    max_hotspots: int = 5
    dependency_count_risk_threshold: int = 25


DEFAULT_SCAN_CONFIG = ScanConfig()


@dataclass(frozen=True, slots=True)
class EnrichConfig:
    """Configuration for optional AI enrichment."""

    # Opus-class model: enrichment is one synthesis call per audit, so the
    # richer read of module roles and debt is worth the per-call cost.
    model: str = "claude-opus-4-8"
    timeout_seconds: int = 60
    max_debt_items: int = 5


DEFAULT_ENRICH_CONFIG = EnrichConfig()
