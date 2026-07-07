"""Tests for exclude_globs: excluded trees are invisible to every check."""

from __future__ import annotations

from dataclasses import replace

from reposage.standards.config import DEFAULT_STANDARDS_CONFIG
from reposage.standards.context import build_context
from reposage.standards.models import CheckStatus
from reposage.standards.pipeline import build_standards_report


def _write(path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_excluded_files_dropped_from_records(tmp_path) -> None:
    _write(tmp_path / "src" / "app.py", "x = 1\n")
    _write(tmp_path / "tests" / "fixtures" / "planted.py", "y = 2\n")

    config = replace(DEFAULT_STANDARDS_CONFIG, exclude_globs=("tests/fixtures/**",))
    ctx = build_context(tmp_path, config)

    paths = {record.path for record in ctx.file_records}
    assert "src/app.py" in paths
    assert "tests/fixtures/planted.py" not in paths
    assert "tests/fixtures/planted.py" not in ctx.python_asts


def test_excluded_workflow_not_counted(tmp_path) -> None:
    _write(tmp_path / ".github" / "workflows" / "ci.yml", "on: [push]\njobs: {}\n")

    excluded = replace(DEFAULT_STANDARDS_CONFIG, exclude_globs=(".github/workflows/**",))
    assert build_context(tmp_path, excluded).workflow_files == []
    # Sanity: without the exclusion the same file is picked up.
    assert build_context(tmp_path, DEFAULT_STANDARDS_CONFIG).workflow_files == [
        ".github/workflows/ci.yml"
    ]


def test_excluded_secret_not_flagged(tmp_path) -> None:
    _write(
        tmp_path / "tests" / "fixtures" / "leak.py",
        'API_KEY = "abcd1234efgh5678ijkl"\n',
    )
    _write(
        tmp_path / "pyproject.toml",
        '[tool.reposage.audit]\nexclude_globs = ["tests/fixtures/**"]\n',
    )

    report = build_standards_report(tmp_path)

    s2 = next(standard for standard in report.standards if standard.number == 2)
    check = next(c for c in s2.checks if c.check_id == "s2.config_external")
    assert check.status is not CheckStatus.FAIL

    # Without exclusion the planted secret is flagged, proving the test is real.
    unfiltered = build_standards_report(tmp_path, DEFAULT_STANDARDS_CONFIG)
    s2_raw = next(standard for standard in unfiltered.standards if standard.number == 2)
    raw_check = next(c for c in s2_raw.checks if c.check_id == "s2.config_external")
    assert raw_check.status is CheckStatus.FAIL
