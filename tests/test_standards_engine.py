"""Tests for the Six Standards orchestrator arithmetic and fix list."""

from __future__ import annotations

from reposage.standards.config import StandardsConfig
from reposage.standards.pipeline import build_standards_report


def test_empty_repo_report_shape(tmp_path) -> None:
    report = build_standards_report(tmp_path)

    # An empty repo: only S5 (accountability) is vacuously not-applicable and so
    # passes; every other standard has a concrete failure. s1.git_history is the
    # sole uncertain check (no git history to read).
    assert report.grade == 1
    assert len(report.standards) == 6
    assert report.uncertain_count == 1


def test_fix_list_sorted_ascending_by_standard(tmp_path) -> None:
    report = build_standards_report(tmp_path)

    numbers = [item.standard for item in report.fix_list]
    assert numbers == sorted(numbers)
    assert len(report.fix_list) == 10


def test_standard_three_first_fix_has_priority_note(tmp_path) -> None:
    report = build_standards_report(tmp_path)

    s3_fixes = [item for item in report.fix_list if item.standard == 3]
    assert s3_fixes
    assert s3_fixes[0].priority_note.startswith("Standard 3, Proven")
    assert all(item.priority_note == "" for item in s3_fixes[1:])


def test_skip_standard_makes_it_pass_with_note(tmp_path) -> None:
    # S4 (shipped) fails on an empty repo; skipping it forces the whole standard
    # to pass, lifting the grade from 1 (S5 only) to 2.
    config = StandardsConfig(skip=frozenset({"s4"}))
    report = build_standards_report(tmp_path, config)

    standard_four = next(s for s in report.standards if s.number == 4)
    assert standard_four.passed is True
    assert report.grade == 2
    assert "3 checks skipped by config" in report.notes


def test_skip_single_check(tmp_path) -> None:
    config = StandardsConfig(skip=frozenset({"s4.cicd"}))
    report = build_standards_report(tmp_path, config)

    standard_four = next(s for s in report.standards if s.number == 4)
    assert standard_four.passed is False
    assert standard_four.passed_count == 1
    assert "1 checks skipped by config" in report.notes
