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
