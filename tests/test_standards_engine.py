"""Tests for the Six Standards orchestrator arithmetic and fix list."""

from __future__ import annotations

from reposage.standards.config import StandardsConfig
from reposage.standards.pipeline import build_standards_report


def test_all_uncertain_stubs_grade_zero(tmp_path) -> None:
    report = build_standards_report(tmp_path)

    assert report.grade == 0
    assert len(report.standards) == 6
    assert report.uncertain_count == 18


def test_fix_list_sorted_ascending_by_standard(tmp_path) -> None:
    report = build_standards_report(tmp_path)

    numbers = [item.standard for item in report.fix_list]
    assert numbers == sorted(numbers)
    assert len(report.fix_list) == 18


def test_standard_three_first_fix_has_priority_note(tmp_path) -> None:
    report = build_standards_report(tmp_path)

    s3_fixes = [item for item in report.fix_list if item.standard == 3]
    assert s3_fixes
    assert s3_fixes[0].priority_note.startswith("Standard 3, Proven")
    assert all(item.priority_note == "" for item in s3_fixes[1:])


def test_skip_standard_makes_it_pass_with_note(tmp_path) -> None:
    config = StandardsConfig(skip=frozenset({"s5"}))
    report = build_standards_report(tmp_path, config)

    standard_five = next(s for s in report.standards if s.number == 5)
    assert standard_five.passed is True
    assert report.grade == 1
    assert "3 checks skipped by config" in report.notes
    assert report.uncertain_count == 15


def test_skip_single_check(tmp_path) -> None:
    config = StandardsConfig(skip=frozenset({"s5.logs"}))
    report = build_standards_report(tmp_path, config)

    standard_five = next(s for s in report.standards if s.number == 5)
    assert standard_five.passed is False
    assert standard_five.passed_count == 1
    assert "1 checks skipped by config" in report.notes
