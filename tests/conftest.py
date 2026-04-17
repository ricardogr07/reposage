"""Shared pytest helpers."""

from __future__ import annotations


def fixture_path(name: str):
    """Return the path to a named test fixture repository."""

    from pathlib import Path

    project_root = Path(__file__).resolve().parents[1]
    return project_root / "tests" / "fixtures" / name
