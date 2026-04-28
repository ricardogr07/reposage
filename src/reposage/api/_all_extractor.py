"""Extract ``__all__`` export sets from Python ``__init__.py`` files."""

from __future__ import annotations

import ast
from pathlib import Path

from reposage.models import FileRecord


def extract_all_exports(python_files: list[FileRecord], root: Path) -> dict[str, set[str]]:
    """Return a map of module dotted-path → set of names in ``__all__``.

    Only processes ``__init__.py`` files. Silently skips files that cannot
    be read or parsed.
    """
    result: dict[str, set[str]] = {}
    for record in python_files:
        pure = Path(record.path)
        if pure.name != "__init__.py":
            continue
        abs_path = root / record.path
        names = _extract_from_init(abs_path)
        if names:
            module = _path_to_module(record.path)
            result[module] = names
    return result


def _extract_from_init(path: Path) -> set[str]:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError):
        return set()

    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                return _extract_list_strings(node.value)
    return set()


def _extract_list_strings(node: ast.expr) -> set[str]:
    if not isinstance(node, (ast.List, ast.Tuple)):
        return set()
    result: set[str] = set()
    for elt in node.elts:
        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
            result.add(elt.value)
    return result


def _path_to_module(path: str) -> str:
    """Convert a file path like ``src/mylib/__init__.py`` to ``mylib``."""
    parts = Path(path).with_suffix("").parts
    if parts and parts[0] in ("src", "lib"):
        parts = parts[1:]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)
