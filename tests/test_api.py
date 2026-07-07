"""Tests for M11 API surface analysis."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from reposage.api._all_extractor import extract_all_exports
from reposage.api._git_history import get_removed_symbols
from reposage.api._symbol_extractor import extract_public_symbols
from reposage.api.surface import analyze_api_surface
from reposage.cli import main
from reposage.config import DEFAULT_SCAN_CONFIG
from reposage.models import APISurface, FileRecord, RemovedSymbol
from reposage.pipeline import build_audit_report
from reposage.reports.agent_brief import render_agent_brief
from reposage.reports.markdown import render_markdown_report
from reposage.scan.filesystem import scan_repository
from tests.conftest import fixture_path


def _api_repo_python_files() -> tuple[list[FileRecord], object]:
    root = fixture_path("api_repo")
    file_records, _ = scan_repository(root, DEFAULT_SCAN_CONFIG)
    python_files = [r for r in file_records if r.extension == ".py"]
    return python_files, root


# ── _all_extractor ────────────────────────────────────────────────────────────


def test_extract_all_exports_fixture() -> None:
    python_files, root = _api_repo_python_files()
    exports = extract_all_exports(python_files, root)  # type: ignore[arg-type]
    all_names: set[str] = set()
    for names in exports.values():
        all_names.update(names)
    assert "PublicClass" in all_names
    assert "typed_function" in all_names


def test_extract_all_exports_no_init(tmp_path: Path) -> None:
    (tmp_path / "foo.py").write_text("x = 1", encoding="utf-8")
    fr = FileRecord(path="foo.py", extension=".py", size_bytes=5, line_count=1)
    result = extract_all_exports([fr], tmp_path)
    assert result == {}


def test_extract_all_exports_invalid_file(tmp_path: Path) -> None:
    (tmp_path / "__init__.py").write_text("def (", encoding="utf-8")
    fr = FileRecord(path="__init__.py", extension=".py", size_bytes=5, line_count=1)
    result = extract_all_exports([fr], tmp_path)
    assert result == {}


# ── _symbol_extractor ─────────────────────────────────────────────────────────


def test_extract_public_symbols_fixture() -> None:
    python_files, root = _api_repo_python_files()
    exports = extract_all_exports(python_files, root)  # type: ignore[arg-type]
    symbols = extract_public_symbols(root, python_files, exports)  # type: ignore[arg-type]

    by_name = {s.name: s for s in symbols}
    assert "PublicClass" in by_name
    assert by_name["PublicClass"].kind == "class"
    assert by_name["PublicClass"].has_docstring is True

    assert "typed_function" in by_name
    assert by_name["typed_function"].kind == "function"
    assert by_name["typed_function"].has_type_annotations is True
    assert by_name["typed_function"].has_docstring is True

    assert "untyped_function" in by_name
    assert by_name["untyped_function"].has_type_annotations is False

    assert "CONSTANT" in by_name
    assert by_name["CONSTANT"].kind == "constant"

    assert "_private_helper" not in by_name


def test_extract_public_symbols_exported_via_all() -> None:
    python_files, root = _api_repo_python_files()
    exports = extract_all_exports(python_files, root)  # type: ignore[arg-type]
    symbols = extract_public_symbols(root, python_files, exports)  # type: ignore[arg-type]

    by_name = {s.name: s for s in symbols}
    assert by_name["PublicClass"].exported_via_all is True
    assert by_name["typed_function"].exported_via_all is True
    assert by_name["untyped_function"].exported_via_all is False
    assert by_name["CONSTANT"].exported_via_all is False


def test_extract_public_symbols_missing_file(tmp_path: Path) -> None:
    fr = FileRecord(path="nonexistent.py", extension=".py", size_bytes=0, line_count=0)
    result = extract_public_symbols(tmp_path, [fr], {})
    assert result == []


def test_constant_attribute_docstring_counts(tmp_path: Path) -> None:
    source = 'FLOOR = 0.8\n"""The gate floor."""\n\nBARE = 1\nx = FLOOR\n'
    (tmp_path / "consts.py").write_text(source, encoding="utf-8")
    fr = FileRecord(path="consts.py", extension=".py", size_bytes=len(source), line_count=5)

    by_name = {s.name: s for s in extract_public_symbols(tmp_path, [fr], {})}

    assert by_name["FLOOR"].has_docstring is True
    assert by_name["BARE"].has_docstring is False


# ── _git_history ──────────────────────────────────────────────────────────────


def test_get_removed_symbols_no_git(tmp_path: Path) -> None:
    (tmp_path / "foo.py").write_text("def gone(): pass", encoding="utf-8")
    fr = FileRecord(path="foo.py", extension=".py", size_bytes=16, line_count=1)
    removed, truncated = get_removed_symbols(tmp_path, [fr])
    assert removed == []
    assert truncated is False


def test_get_removed_symbols_detects_removal(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    py_file = tmp_path / "mod.py"
    py_file.write_text("def gone_function(): pass\n", encoding="utf-8")
    subprocess.run(["git", "add", "mod.py"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "add"], cwd=tmp_path, check=True, capture_output=True)
    py_file.write_text("", encoding="utf-8")
    subprocess.run(["git", "add", "mod.py"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "remove"], cwd=tmp_path, check=True, capture_output=True)
    fr = FileRecord(path="mod.py", extension=".py", size_bytes=0, line_count=0)
    removed, truncated = get_removed_symbols(tmp_path, [fr])
    assert any(s.name == "gone_function" for s in removed)
    assert truncated is False


# ── surface orchestrator ──────────────────────────────────────────────────────


def test_analyze_api_surface_fixture() -> None:
    root = fixture_path("api_repo")
    report = build_audit_report(root)
    surface = analyze_api_surface(root, report)
    assert len(surface.public_symbols) > 0
    assert surface.undocumented_count >= 1


def test_analyze_api_surface_no_python_files(tmp_path: Path) -> None:
    (tmp_path / "README.txt").write_text("hello", encoding="utf-8")
    report = build_audit_report(tmp_path)
    surface = analyze_api_surface(tmp_path, report)
    assert surface.public_symbols == []
    assert surface.removed_symbols == []


def test_analyze_api_surface_not_git(tmp_path: Path) -> None:
    (tmp_path / "mod.py").write_text(
        "def foo(x: int) -> str:\n    return str(x)\n", encoding="utf-8"
    )
    report = build_audit_report(tmp_path)
    surface = analyze_api_surface(tmp_path, report)
    assert surface.removed_symbols == []
    assert surface.notes == []


# ── CLI integration ───────────────────────────────────────────────────────────


def test_cli_api_surface_flag(capsys: pytest.CaptureFixture[str]) -> None:
    root = str(fixture_path("api_repo"))
    result = main(["report", root, "--api-surface", "--format", "json"])
    assert result == 0
    captured = capsys.readouterr()
    assert '"api_surface"' in captured.out
    assert '"public_symbols"' in captured.out


def test_cli_no_api_surface_flag(capsys: pytest.CaptureFixture[str]) -> None:
    root = str(fixture_path("api_repo"))
    result = main(["report", root, "--format", "json"])
    assert result == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["api_surface"] is None


# ── renderers ─────────────────────────────────────────────────────────────────


def test_markdown_renders_api_surface() -> None:
    report = build_audit_report(fixture_path("api_repo"))
    report.api_surface = APISurface(
        public_symbols=[],
        undocumented_count=2,
        untyped_count=1,
    )
    output = render_markdown_report(report)
    assert "API Surface" in output
    assert "2 undocumented" in output


def test_breaking_changes_in_agent_brief() -> None:
    report = build_audit_report(fixture_path("api_repo"))
    report.api_surface = APISurface(
        breaking_changes=[
            RemovedSymbol(name="gone", module="mylib.core", last_seen_commit="abc1234")
        ],
    )
    output = render_agent_brief(report)
    assert "[breaking/high]" in output
    assert "gone" in output
