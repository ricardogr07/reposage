"""Orchestrate Python public API surface analysis."""

from __future__ import annotations

from pathlib import Path

from reposage.api._all_extractor import extract_all_exports
from reposage.api._git_history import get_removed_symbols
from reposage.api._symbol_extractor import extract_public_symbols
from reposage.config import DEFAULT_SCAN_CONFIG
from reposage.models import APISurface, AuditReport
from reposage.scan.filesystem import scan_repository


def analyze_api_surface(root: Path, report: AuditReport) -> APISurface:
    """Analyze the Python public API surface of the repository at ``root``.

    Always returns ``APISurface`` — empty if no Python files are found.
    Re-scans the filesystem because ``AuditReport`` does not expose file records.
    """
    file_records, _ = scan_repository(root.resolve(), DEFAULT_SCAN_CONFIG)
    python_files = [r for r in file_records if r.extension == ".py"]

    if not python_files:
        return APISurface()

    all_exports = extract_all_exports(python_files, root)
    public_symbols = extract_public_symbols(root, python_files, all_exports)
    removed, truncated = get_removed_symbols(root, python_files)

    exported_names: set[str] = set()
    for names in all_exports.values():
        exported_names.update(names)
    breaking = [s for s in removed if s.name in exported_names]

    undocumented = sum(1 for s in public_symbols if not s.has_docstring)
    untyped = sum(1 for s in public_symbols if not s.has_type_annotations and s.kind == "function")

    notes: list[str] = []
    if truncated:
        notes.append("Git history scan truncated at 500 subprocess calls.")

    return APISurface(
        public_symbols=public_symbols,
        removed_symbols=removed,
        undocumented_count=undocumented,
        untyped_count=untyped,
        breaking_changes=breaking,
        notes=notes,
    )
