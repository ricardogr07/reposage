"""Engineering quality heuristics."""

from __future__ import annotations

import tomllib
from pathlib import Path, PurePosixPath

from reposage.analysis.tests import detect_test_files
from reposage.models import FileRecord, QualitySignals, TSConfig

CI_FILE_NAMES = {".gitlab-ci.yml", "azure-pipelines.yml"}
PACKAGING_FILES = {"pyproject.toml", "package.json", "setup.cfg", "setup.py"}
LINT_FILE_NAMES = {
    ".eslintrc",
    ".eslintrc.json",
    "eslint.config.js",
    "eslint.config.mjs",
    "eslint.config.cjs",
    ".ruff.toml",
    "ruff.toml",
}
TYPE_FILE_NAMES = {"mypy.ini", "pyrightconfig.json", "py.typed", "tsconfig.json"}


def analyze_quality(
    root: Path,
    file_records: list[FileRecord],
    ts_config: TSConfig | None = None,
) -> QualitySignals:
    """Build engineering quality signals from repository contents."""

    all_paths = {file_record.path for file_record in file_records}
    test_files = detect_test_files(file_records)
    ci_files = sorted(
        path
        for path in all_paths
        if path.startswith(".github/workflows/") or PurePosixPath(path).name in CI_FILE_NAMES
    )
    documentation_files = sorted(
        path
        for path in all_paths
        if path.lower().startswith("docs/") or PurePosixPath(path).name.lower().startswith("readme")
    )
    packaging_files = sorted(
        path for path in all_paths if PurePosixPath(path).name in PACKAGING_FILES
    )
    lint_files = sorted(path for path in all_paths if PurePosixPath(path).name in LINT_FILE_NAMES)
    typing_files = sorted(path for path in all_paths if PurePosixPath(path).name in TYPE_FILE_NAMES)

    if "pyproject.toml" in all_paths:
        pyproject_path = root / "pyproject.toml"
        lint_files, typing_files = _augment_with_pyproject(pyproject_path, lint_files, typing_files)

    checklist: list[str] = []
    missing_signals: list[str] = []

    _record_signal(
        bool(test_files),
        "Automated tests detected.",
        "Automated tests were not detected.",
        checklist,
        missing_signals,
    )
    _record_signal(
        bool(ci_files),
        "CI configuration detected.",
        "CI workflow configuration was not detected.",
        checklist,
        missing_signals,
    )
    _record_signal(
        bool(documentation_files),
        "Repository documentation detected.",
        "Repository documentation was not detected.",
        checklist,
        missing_signals,
    )
    _record_signal(
        bool(packaging_files),
        "Packaging metadata detected.",
        "Packaging metadata was not detected.",
        checklist,
        missing_signals,
    )
    _record_signal(
        bool(lint_files),
        "Lint configuration detected.",
        "Lint configuration was not detected.",
        checklist,
        missing_signals,
    )
    _record_signal(
        bool(typing_files),
        "Typing configuration detected.",
        "Typing configuration was not detected.",
        checklist,
        missing_signals,
    )

    if ts_config is not None:
        if not ts_config.strict:
            missing_signals.append("TypeScript strict mode not enabled — allows silent type holes.")
        if not ts_config.no_implicit_any:
            missing_signals.append(
                "TypeScript noImplicitAny not enabled"
                " — untyped parameters are the largest source of TS runtime errors."
            )
        if not ts_config.strict_null_checks:
            missing_signals.append(
                "TypeScript strictNullChecks not enabled"
                " — null and undefined are assignable to any type."
            )
        if not ts_config.no_unchecked_indexed_access:
            missing_signals.append(
                "TypeScript noUncheckedIndexedAccess not enabled"
                " — array index access can silently be undefined."
            )

    present_count = sum(
        [
            bool(test_files),
            bool(ci_files),
            bool(documentation_files),
            bool(packaging_files),
            bool(lint_files),
            bool(typing_files),
        ]
    )
    score = int((present_count / 6) * 100)

    return QualitySignals(
        score=score,
        has_tests=bool(test_files),
        test_files=test_files[:10],
        ci_present=bool(ci_files),
        ci_files=ci_files,
        documentation_present=bool(documentation_files),
        documentation_files=documentation_files,
        packaging_present=bool(packaging_files),
        packaging_files=packaging_files,
        lint_present=bool(lint_files),
        lint_files=lint_files,
        typing_present=bool(typing_files),
        typing_files=typing_files,
        checklist=checklist,
        missing_signals=missing_signals,
    )


def _augment_with_pyproject(
    pyproject_path: Path,
    lint_files: list[str],
    typing_files: list[str],
) -> tuple[list[str], list[str]]:
    try:
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return lint_files, typing_files

    tool_section = data.get("tool", {})
    if "ruff" in tool_section and "pyproject.toml" not in lint_files:
        lint_files = sorted([*lint_files, "pyproject.toml"])
    if "mypy" in tool_section and "pyproject.toml" not in typing_files:
        typing_files = sorted([*typing_files, "pyproject.toml"])
    return lint_files, typing_files


def _record_signal(
    present: bool,
    positive_message: str,
    negative_message: str,
    checklist: list[str],
    missing_signals: list[str],
) -> None:
    if present:
        checklist.append(positive_message)
    else:
        missing_signals.append(negative_message)
