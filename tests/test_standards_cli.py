"""CLI integration tests for the audit subcommand."""

from __future__ import annotations

import json

from reposage.cli import main


def test_audit_returns_zero_and_prints_grade(tmp_path, capsys) -> None:
    exit_code = main(["audit", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "**Grade: 0/6**" in captured.out


def test_audit_fail_under_returns_one(tmp_path, capsys) -> None:
    exit_code = main(["audit", str(tmp_path), "--fail-under", "6"])

    capsys.readouterr()
    assert exit_code == 1


def test_audit_json_format_parses(tmp_path, capsys) -> None:
    exit_code = main(["audit", str(tmp_path), "--format", "json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["grade"] == 0
    assert len(payload["standards"]) == 6


def test_audit_output_flag_writes_file(tmp_path) -> None:
    out_file = tmp_path / "audit.md"
    exit_code = main(["audit", str(tmp_path), "--output", str(out_file)])

    assert exit_code == 0
    assert out_file.exists()
    assert "RepoSage Standards Audit" in out_file.read_text(encoding="utf-8")
