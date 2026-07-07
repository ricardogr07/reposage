"""Shared pytest helpers."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock

import pytest

from reposage.enrichment.models import DebtItem, EnrichmentResult, Improvement, ModuleRole
from reposage.models import AuditReport
from reposage.pipeline import build_audit_report


@pytest.fixture(autouse=True)
def _isolate_inner_audit_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear REPOSAGE_INNER_AUDIT so the s3 recursion guard cannot leak into tests.

    When RepoSage audits its own repository it runs the suite in a subprocess
    with REPOSAGE_INNER_AUDIT=1 set. Without this, the s3 unit tests that call
    ``s3_proven.evaluate`` would see the guard fire and get UNCERTAIN instead of
    the status they assert. Tests that need the guard set it explicitly.
    """
    monkeypatch.delenv("REPOSAGE_INNER_AUDIT", raising=False)


def fixture_path(name: str) -> Path:
    """Return the path to a named test fixture repository."""
    project_root = Path(__file__).resolve().parents[1]
    return project_root / "tests" / "fixtures" / name


def make_enrichment(roles: int = 1, debts: int = 1, improvements: int = 5) -> EnrichmentResult:
    return EnrichmentResult(
        module_roles=[
            ModuleRole(module=f"src/mod{i}", responsibility="does things", layer="domain")
            for i in range(roles)
        ],
        debt_items=[
            DebtItem(
                title=f"Debt {i}",
                severity="medium",
                description="Something to fix.",
                issue_title=f"Fix debt {i}",
                issue_body="## Context\nNeeds work.",
            )
            for i in range(debts)
        ],
        top_improvements=[
            Improvement(rank=i + 1, title=f"Improve {i}", rationale="Because.", effort="low")
            for i in range(improvements)
        ],
        model_id="claude-opus-4-8",
    )


def make_report() -> AuditReport:
    return build_audit_report(fixture_path("python_repo"))


def make_fake_anthropic_module(tool_input: dict[str, Any]) -> ModuleType:
    """Return a mock anthropic module whose client returns tool_input."""
    block = MagicMock()
    block.type = "tool_use"
    block.name = "audit_enrichment"
    block.input = tool_input

    message = MagicMock()
    message.content = [block]

    client_instance = MagicMock()
    client_instance.messages.create.return_value = message

    anthropic_mod = MagicMock()
    anthropic_mod.Anthropic.return_value = client_instance
    return anthropic_mod  # type: ignore[return-value]


def make_fake_openai_module(tool_input: dict[str, Any]) -> ModuleType:
    """Return a mock openai module whose client returns tool_input as a function call."""
    func_call = MagicMock()
    func_call.arguments = json.dumps(tool_input)

    tool_call = MagicMock()
    tool_call.function = func_call

    message = MagicMock()
    message.tool_calls = [tool_call]

    choice = MagicMock()
    choice.message = message

    completion = MagicMock()
    completion.choices = [choice]

    client_instance = MagicMock()
    client_instance.chat.completions.create.return_value = completion

    openai_mod = MagicMock()
    openai_mod.OpenAI.return_value = client_instance
    return openai_mod  # type: ignore[return-value]


def make_git_repo(
    tmp_path: Path,
    files: dict[str, str],
    commits: list[list[str]] | None = None,
) -> Path:
    """Create a git repo under ``tmp_path`` and commit ``files`` in groups.

    ``commits`` is a list of file-path groups, each committed together in order;
    None commits everything as a single "initial" commit. Skips if git absent.
    """
    if shutil.which("git") is None:
        pytest.skip("git not available")

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True)

    git("init", "-b", "main")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.com")

    groups = commits if commits is not None else [list(files)]
    for index, group in enumerate(groups):
        for rel in group:
            path = tmp_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(files[rel], encoding="utf-8")
        git("add", "-A")
        git("commit", "-m", "initial" if commits is None else f"Add sources for step {index + 1}")
    return tmp_path
