"""Parser for tsconfig.json files, with extends-chain resolution."""

from __future__ import annotations

import json
from pathlib import Path

from reposage.models import TSConfig


def parse_tsconfig(path: Path) -> TSConfig:
    """Parse tsconfig.json at path, following extends chain up to 5 levels."""
    return _parse(path.resolve(), visited=set(), depth=0)


def _parse(path: Path, visited: set[Path], depth: int) -> TSConfig:
    if depth >= 5 or path in visited:
        return TSConfig()
    visited.add(path)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return TSConfig()

    if not isinstance(data, dict):
        return TSConfig()

    raw_opts = data.get("compilerOptions")
    options: dict[str, object] = raw_opts if isinstance(raw_opts, dict) else {}

    # Resolve extends chain
    base = TSConfig()
    extends_val = data.get("extends")
    if isinstance(extends_val, str) and not extends_val.startswith(("http://", "https://")):
        base_path = (path.parent / extends_val).resolve()
        # Ensure it resolves to a .json file (add extension if missing)
        if base_path.suffix == "":
            base_path = base_path.with_suffix(".json")
        if base_path.exists() and base_path.suffix == ".json":
            base = _parse(base_path, visited, depth + 1)

    return _merge(base, options)


def _merge(base: TSConfig, options: dict[str, object]) -> TSConfig:
    """Build a TSConfig where current options override base defaults."""
    strict = bool(options.get("strict", False)) or base.strict
    no_implicit_any = bool(options.get("noImplicitAny", False)) or strict or base.no_implicit_any
    strict_null_checks = (
        bool(options.get("strictNullChecks", False)) or strict or base.strict_null_checks
    )
    no_unchecked = (
        bool(options.get("noUncheckedIndexedAccess", False)) or base.no_unchecked_indexed_access
    )
    target = str(options.get("target", "")) or base.target
    module = str(options.get("module", "")) or base.module
    path_aliases = bool("paths" in options) or base.path_aliases

    return TSConfig(
        strict=strict,
        no_implicit_any=no_implicit_any,
        strict_null_checks=strict_null_checks,
        no_unchecked_indexed_access=no_unchecked,
        target=target,
        module=module,
        path_aliases=path_aliases,
    )
