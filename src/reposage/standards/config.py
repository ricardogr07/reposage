"""Configuration for the Six Standards audit engine."""

from __future__ import annotations

import tomllib
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class StandardsConfig:
    """Stable configuration for a standards audit."""

    run_subprocess_checks: bool = False
    skip: frozenset[str] = frozenset()
    min_commits: int = 5
    min_docstring_coverage: float = 0.7
    min_behavioral_assert_ratio: float = 0.5
    history_scan_depth: int = 200
    pytest_timeout: int = 300
    install_timeout: int = 300
    git_timeout: int = 10
    serving_globs: tuple[str, ...] = ()
    training_globs: tuple[str, ...] = ()


DEFAULT_STANDARDS_CONFIG = StandardsConfig()

# Recognized field name -> converter from a raw toml value to the field type.
_FIELDS: dict[str, Callable[[Any], Any]] = {
    "run_subprocess_checks": bool,
    "skip": lambda v: frozenset(v),
    "min_commits": int,
    "min_docstring_coverage": float,
    "min_behavioral_assert_ratio": float,
    "history_scan_depth": int,
    "pytest_timeout": int,
    "install_timeout": int,
    "git_timeout": int,
    "serving_globs": lambda v: tuple(v),
    "training_globs": lambda v: tuple(v),
}

# Nested sub-tables whose keys are flattened onto the top-level field namespace.
_NESTED_TABLES = ("thresholds", "classify")


def load_standards_config(root: Path) -> tuple[StandardsConfig, list[str]]:
    """Load audit config for ``root``, returning the config and any warnings.

    Precedence (later overrides earlier, so the reposage.toml table is
    strongest): ``[tool.reposage.audit]`` in pyproject.toml, then ``[audit]``
    in reposage.toml. Malformed toml contributes a warning and no overrides.
    """

    warnings: list[str] = []
    py_over = _read_table(root / "pyproject.toml", ("tool", "reposage", "audit"), warnings)
    rs_over = _read_table(root / "reposage.toml", ("audit",), warnings)

    merged = {**py_over, **rs_over}
    config = replace(DEFAULT_STANDARDS_CONFIG, **merged)
    return config, warnings


def _read_table(path: Path, keys: tuple[str, ...], warnings: list[str]) -> dict[str, Any]:
    """Read a nested toml table and return recognized field overrides."""

    if not path.exists():
        return {}
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except (tomllib.TOMLDecodeError, OSError):
        warnings.append(f"malformed toml ignored: {path.name}")
        return {}

    table: Any = data
    for key in keys:
        if not isinstance(table, dict) or key not in table:
            return {}
        table = table[key]
    if not isinstance(table, dict):
        return {}

    return _flatten_overrides(table, path.name, warnings)


def _flatten_overrides(table: dict[str, Any], source: str, warnings: list[str]) -> dict[str, Any]:
    """Flatten nested threshold/classify tables and convert recognized keys."""

    flat: dict[str, Any] = {}
    for key, value in table.items():
        if key in _NESTED_TABLES and isinstance(value, dict):
            for sub_key, sub_value in value.items():
                flat[sub_key] = sub_value
        else:
            flat[key] = value

    overrides: dict[str, Any] = {}
    for name, value in flat.items():
        converter = _FIELDS.get(name)
        if converter is None:
            warnings.append(f"unknown audit key in {source}: {name}")
            continue
        overrides[name] = converter(value)
    return overrides
