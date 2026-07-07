"""Extract public symbols from Python source files using ``ast``."""

from __future__ import annotations

import ast
from pathlib import Path

from reposage.models import FileRecord, PublicSymbol


def extract_public_symbols(
    root: Path,
    python_files: list[FileRecord],
    all_exports: dict[str, set[str]],
) -> list[PublicSymbol]:
    """Return all public top-level symbols across the given Python files."""
    symbols: list[PublicSymbol] = []
    for record in python_files:
        abs_path = root / record.path
        module = _path_to_module(record.path)
        exported = _resolve_exports(module, all_exports)
        symbols.extend(_extract_from_file(abs_path, module, exported))
    return symbols


def _resolve_exports(module: str, all_exports: dict[str, set[str]]) -> set[str]:
    """Merge exports from the module itself and all ancestor package ``__all__``s."""
    result: set[str] = set(all_exports.get(module, set()))
    parts = module.split(".")
    for i in range(len(parts) - 1, 0, -1):
        parent = ".".join(parts[:i])
        result |= all_exports.get(parent, set())
    return result


def _extract_from_file(path: Path, module: str, exported: set[str]) -> list[PublicSymbol]:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError):
        return []

    symbols: list[PublicSymbol] = []
    for index, node in enumerate(tree.body):
        following = tree.body[index + 1] if index + 1 < len(tree.body) else None
        sym = _node_to_symbol(node, module, exported, following)
        if sym is not None:
            symbols.append(sym)
    return symbols


def _node_to_symbol(
    node: ast.stmt,
    module: str,
    exported: set[str],
    following: ast.stmt | None = None,
) -> PublicSymbol | None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        name = node.name
        if name.startswith("_"):
            return None
        return PublicSymbol(
            name=name,
            kind="function",
            module=module,
            has_docstring=_has_docstring(node.body),
            has_type_annotations=_function_is_typed(node),
            exported_via_all=name in exported,
        )
    if isinstance(node, ast.ClassDef):
        name = node.name
        if name.startswith("_"):
            return None
        return PublicSymbol(
            name=name,
            kind="class",
            module=module,
            has_docstring=_has_docstring(node.body),
            has_type_annotations=True,
            exported_via_all=name in exported,
        )
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        const_name = _assignment_name(node)
        if const_name is None or const_name.startswith("_") or not const_name[0].isupper():
            return None
        return PublicSymbol(
            name=const_name,
            kind="constant",
            module=module,
            # PEP 224 attribute docstring: a string literal on the next line.
            has_docstring=_is_string_expr(following),
            has_type_annotations=isinstance(node, ast.AnnAssign),
            exported_via_all=const_name in exported,
        )
    return None


def _has_docstring(body: list[ast.stmt]) -> bool:
    if not body:
        return False
    return _is_string_expr(body[0])


def _is_string_expr(node: ast.stmt | None) -> bool:
    return (
        node is not None
        and isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _function_is_typed(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    if node.returns is None:
        return False
    return all(a.annotation is not None for a in node.args.args)


def _assignment_name(node: ast.Assign | ast.AnnAssign) -> str | None:
    if isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name):
            return node.target.id
        return None
    if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    return None


def _path_to_module(path: str) -> str:
    parts = Path(path).with_suffix("").parts
    if parts and parts[0] in ("src", "lib"):
        parts = parts[1:]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)
