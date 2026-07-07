"""CLI integration tests for the audit subcommand."""

from __future__ import annotations

import json

from reposage.cli import main


def test_audit_returns_zero_and_prints_grade(tmp_path, capsys) -> None:
    exit_code = main(["audit", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "**Grade: " in captured.out


def test_audit_fail_under_returns_one(tmp_path, capsys) -> None:
    exit_code = main(["audit", str(tmp_path), "--fail-under", "6"])

    capsys.readouterr()
    assert exit_code == 1


def test_audit_json_format_parses(tmp_path, capsys) -> None:
    exit_code = main(["audit", str(tmp_path), "--format", "json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["grade"] == sum(1 for standard in payload["standards"] if standard["passed"])
    assert len(payload["standards"]) == 6


def test_audit_github_format_writes_step_summary(tmp_path, monkeypatch, capsys) -> None:
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    exit_code = main(["audit", str(tmp_path), "--format", "github"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "::notice::RepoSage grade:" in captured.out
    assert summary.exists()
    assert "# RepoSage Standards Audit" in summary.read_text(encoding="utf-8")


def test_audit_role_glob_flags_pin_roles(tmp_path, capsys) -> None:
    (tmp_path / "core.py").write_text("x = 1\n", encoding="utf-8")

    exit_code = main(["audit", str(tmp_path), "--training-glob", "core.py", "--format", "json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["is_ds_repo"] is True
    assert payload["training_files"] == 1


def test_audit_output_flag_writes_file(tmp_path) -> None:
    out_file = tmp_path / "audit.md"
    exit_code = main(["audit", str(tmp_path), "--output", str(out_file)])

    assert exit_code == 0
    assert out_file.exists()
    assert "RepoSage Standards Audit" in out_file.read_text(encoding="utf-8")
