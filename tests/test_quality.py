"""Quality and risk heuristic tests."""

from __future__ import annotations

import pytest

from reposage.analysis.tests import detect_test_files
from reposage.models import FileRecord
from reposage.pipeline import build_audit_report
from tests.conftest import fixture_path


def test_missing_signal_fixture_flags_quality_gaps() -> None:
    report = build_audit_report(fixture_path("missing_signals_repo"))

    assert report.quality.has_tests is False
    assert report.quality.ci_present is False
    assert report.quality.documentation_present is False
    assert any(
        item == "Automated tests were not detected." for item in report.quality.missing_signals
    )
    assert any(risk_item.title == "Low regression confidence" for risk_item in report.risk.items)


def test_monorepo_fixture_notes_multiple_manifest_roots() -> None:
    report = build_audit_report(fixture_path("monorepo_repo"))

    assert any("monorepo" in note.lower() for note in report.architecture.architecture_notes)


def test_is_test_file_ignores_non_code_extensions() -> None:
    records = [
        FileRecord(path="test_data.csv", extension=".csv", size_bytes=100, line_count=5),
        FileRecord(path="test_readme.md", extension=".md", size_bytes=200, line_count=10),
        FileRecord(path="test_fixtures.json", extension=".json", size_bytes=50, line_count=3),
        FileRecord(path="test_output.txt", extension=".txt", size_bytes=30, line_count=2),
        FileRecord(path="test_service.py", extension=".py", size_bytes=300, line_count=20),
    ]

    result = detect_test_files(records)

    assert result == ["test_service.py"]


@pytest.mark.parametrize(
    "lint_config_name",
    ["eslint.config.js", "eslint.config.mjs", "eslint.config.cjs"],
)
def test_eslint_v9_flat_config_files_count_as_lint_signals(
    tmp_path, lint_config_name: str
) -> None:
    (tmp_path / lint_config_name).write_text("export default [];\n", encoding="utf-8")

    report = build_audit_report(tmp_path)

    assert report.quality.lint_present is True
    assert report.quality.lint_files == [lint_config_name]
