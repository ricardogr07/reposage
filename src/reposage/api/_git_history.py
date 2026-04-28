"""Detect public symbols removed from the repository's git history."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from reposage.models import FileRecord, RemovedSymbol

_MAX_CALLS = 500
_GIT_TIMEOUT = 5


def get_removed_symbols(
    root: Path,
    python_files: list[FileRecord],
    depth: int = 50,
) -> tuple[list[RemovedSymbol], bool]:
    """Return symbols present in history but absent from the current tree.

    Returns ``(removed, truncated)`` where ``truncated`` is ``True`` if the
    500-call cap was reached before all commits were scanned.
    """
    if not (root / ".git").exists():
        return [], False

    shas = _get_shas(root, depth)
    if not shas:
        return [], False

    current_names = _current_symbol_names(root, python_files)
    seen: dict[tuple[str, str], str] = {}  # (name, module) → sha
    call_count = 0
    truncated = False

    for sha in shas:
        for record in python_files:
            if call_count >= _MAX_CALLS:
                truncated = True
                break
            names = _symbols_at(root, sha, record.path)
            call_count += 1
            module = _path_to_module(record.path)
            for name in names:
                key = (name, module)
                if key not in seen:
                    seen[key] = sha
        if truncated:
            break

    removed = [
        RemovedSymbol(name=name, module=module, last_seen_commit=sha)
        for (name, module), sha in seen.items()
        if name not in current_names.get(module, set())
    ]
    return removed, truncated


def _get_shas(root: Path, depth: int) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={depth}", "--format=%h"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        return result.stdout.strip().splitlines()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return []


def _symbols_at(root: Path, sha: str, relative_path: str) -> set[str]:
    try:
        result = subprocess.run(
            ["git", "show", f"{sha}:{relative_path}"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT,
            check=True,
        )
        tree = ast.parse(result.stdout, filename=relative_path)
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        SyntaxError,
        FileNotFoundError,
    ):
        return set()
    names: set[str] = set()
    for node in tree.body:
        name = _node_name(node)
        if name and not name.startswith("_"):
            names.add(name)
    return names


def _node_name(node: ast.stmt) -> str | None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name
    if (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    ):
        return node.targets[0].id
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    return None


def _current_symbol_names(root: Path, python_files: list[FileRecord]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for record in python_files:
        module = _path_to_module(record.path)
        abs_path = root / record.path
        try:
            source = abs_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source)
        except (OSError, SyntaxError):
            continue
        names: set[str] = set()
        for node in tree.body:
            name = _node_name(node)
            if name and not name.startswith("_"):
                names.add(name)
        result[module] = names
    return result


def _path_to_module(path: str) -> str:
    parts = Path(path).with_suffix("").parts
    if parts and parts[0] in ("src", "lib"):
        parts = parts[1:]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)
