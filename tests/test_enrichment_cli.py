"""Tests for the CLI --enrich flag."""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import patch

from tests.conftest import fixture_path, make_fake_anthropic_module


def test_cli_run_command_success(capsys: Any) -> None:
    from reposage.cli import main

    result = main(["run", str(fixture_path("python_repo"))])
    assert result == 0
    assert "RepoSage Audit" in capsys.readouterr().out


def test_cli_returns_error_for_file_path(tmp_path: Any) -> None:
    from reposage.cli import main

    file_path = tmp_path / "not_a_dir.txt"
    file_path.write_text("hi")
    result = main(["report", str(file_path)])
    assert result == 2


def test_cli_enrich_flag_exits_2_without_api_key(tmp_path: Any) -> None:
    from reposage.cli import main

    with patch.dict("os.environ", {}, clear=True):
        result = main(["report", str(fixture_path("python_repo")), "--enrich"])
    assert result == 2


def test_cli_enrich_flag_exits_2_without_sdk(tmp_path: Any) -> None:
    from reposage.cli import main

    env = {"ANTHROPIC_API_KEY": "test-key"}
    with patch.dict("os.environ", env), patch.dict(sys.modules, {"anthropic": None}):  # type: ignore[dict-item]
        result = main(["report", str(fixture_path("python_repo")), "--enrich"])
    assert result == 2


def test_cli_enrich_produces_enriched_markdown(tmp_path: Any) -> None:
    from reposage.cli import main

    out_file = tmp_path / "report.md"
    tool_input: dict[str, Any] = {
        "module_roles": [{"module": "src/x", "responsibility": "handles x", "layer": "domain"}],
        "debt_items": [],
        "top_improvements": [
            {"rank": i + 1, "title": f"T{i}", "rationale": "R.", "effort": "low"} for i in range(5)
        ],
    }
    fake_anthropic = make_fake_anthropic_module(tool_input)
    env = {"ANTHROPIC_API_KEY": "test-key"}

    with patch.dict("os.environ", env), patch.dict(sys.modules, {"anthropic": fake_anthropic}):
        result = main(
            ["report", str(fixture_path("python_repo")), "--enrich", "--output", str(out_file)]
        )

    assert result == 0
    content = out_file.read_text(encoding="utf-8")
    assert "## Module Responsibilities" in content
