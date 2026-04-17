"""Tests for the enrichment package: models, prompts, provider, and renderers."""

from __future__ import annotations

import json
import sys
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from reposage.enrichment.models import DebtItem, EnrichmentResult, Improvement, ModuleRole
from reposage.enrichment.provider import EnrichmentProvider, enrich_report
from reposage.models import AuditReport
from reposage.pipeline import build_audit_report
from reposage.reports.json_report import render_json_report
from reposage.reports.markdown import render_markdown_report
from tests.conftest import fixture_path

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_enrichment(roles: int = 1, debts: int = 1, improvements: int = 5) -> EnrichmentResult:
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
        model_id="claude-haiku-4-5-20251001",
    )


def _make_report() -> AuditReport:
    return build_audit_report(fixture_path("python_repo"))


# ---------------------------------------------------------------------------
# EnrichmentResult dataclass
# ---------------------------------------------------------------------------


def test_enrichment_result_defaults() -> None:
    result = EnrichmentResult()
    assert result.module_roles == []
    assert result.debt_items == []
    assert result.top_improvements == []
    assert result.model_id == ""


def test_module_role_fields() -> None:
    role = ModuleRole(module="src/foo", responsibility="handles foo", layer="domain")
    assert role.module == "src/foo"
    assert role.layer == "domain"


def test_debt_item_fields() -> None:
    item = DebtItem(
        title="No tests",
        severity="high",
        description="Missing coverage.",
        issue_title="Add tests",
        issue_body="## Context",
    )
    assert item.severity == "high"


def test_improvement_fields() -> None:
    imp = Improvement(rank=1, title="Add CI", rationale="Needed.", effort="low")
    assert imp.rank == 1
    assert imp.effort == "low"


# ---------------------------------------------------------------------------
# Provider Protocol and enrich_report dispatcher
# ---------------------------------------------------------------------------


class FakeProvider:
    """Minimal in-memory implementation that satisfies EnrichmentProvider."""

    def __init__(self, result: EnrichmentResult) -> None:
        self._result = result

    def enrich(self, report: AuditReport) -> EnrichmentResult:
        return self._result


def test_enrich_report_delegates_to_provider() -> None:
    expected = _make_enrichment()
    provider: EnrichmentProvider = FakeProvider(expected)
    report = _make_report()
    result = enrich_report(report, provider)
    assert result is expected


# ---------------------------------------------------------------------------
# Prompt builders — classify
# ---------------------------------------------------------------------------


def test_build_classification_prompt_contains_project_name() -> None:
    from reposage.enrichment.classify_prompt import build_classification_prompt

    report = _make_report()
    prompt = build_classification_prompt(report)
    assert report.inventory.project_name in prompt


def test_build_classification_prompt_contains_layer_enum() -> None:
    from reposage.enrichment.classify_prompt import build_classification_prompt

    report = _make_report()
    prompt = build_classification_prompt(report)
    assert "infrastructure" in prompt


def test_classification_schema_shape() -> None:
    from reposage.enrichment.classify_prompt import CLASSIFICATION_SCHEMA

    assert CLASSIFICATION_SCHEMA["type"] == "array"
    items = CLASSIFICATION_SCHEMA["items"]
    assert isinstance(items, dict)
    assert "module" in items["properties"]  # type: ignore[index]


# ---------------------------------------------------------------------------
# Prompt builders — debt
# ---------------------------------------------------------------------------


def test_build_debt_prompt_contains_project_name() -> None:
    from reposage.enrichment.debt_prompt import build_debt_prompt

    report = _make_report()
    prompt = build_debt_prompt(report)
    assert report.inventory.project_name in prompt


def test_debt_schema_max_items() -> None:
    from reposage.enrichment.debt_prompt import DEBT_SCHEMA

    assert DEBT_SCHEMA["maxItems"] == 5


# ---------------------------------------------------------------------------
# Prompt builders — synthesis
# ---------------------------------------------------------------------------


def test_build_synthesis_prompt_contains_project_name() -> None:
    from reposage.enrichment.synthesis_prompt import build_synthesis_prompt

    report = _make_report()
    prompt = build_synthesis_prompt(report)
    assert report.inventory.project_name in prompt


def test_synthesis_schema_five_items() -> None:
    from reposage.enrichment.synthesis_prompt import SYNTHESIS_SCHEMA

    assert SYNTHESIS_SCHEMA["minItems"] == 5
    assert SYNTHESIS_SCHEMA["maxItems"] == 5


# ---------------------------------------------------------------------------
# AnthropicEnricher — mocked SDK
# ---------------------------------------------------------------------------


def _make_fake_anthropic_module(tool_input: dict[str, Any]) -> ModuleType:
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


def test_anthropic_enricher_returns_enrichment_result() -> None:
    from reposage.enrichment.anthropic_provider import AnthropicEnricher

    tool_input: dict[str, Any] = {
        "module_roles": [{"module": "src/foo", "responsibility": "core logic", "layer": "domain"}],
        "debt_items": [
            {
                "title": "Missing tests",
                "severity": "high",
                "description": "No coverage.",
                "issue_title": "Add tests",
                "issue_body": "## Context",
            }
        ],
        "top_improvements": [
            {"rank": i + 1, "title": f"Improve {i}", "rationale": "Because.", "effort": "low"}
            for i in range(5)
        ],
    }
    fake_anthropic = _make_fake_anthropic_module(tool_input)
    report = _make_report()

    with patch.dict(sys.modules, {"anthropic": fake_anthropic}):
        enricher = AnthropicEnricher()
        result = enricher.enrich(report)

    assert isinstance(result, EnrichmentResult)
    assert len(result.module_roles) == 1
    assert result.module_roles[0].layer == "domain"
    assert len(result.debt_items) == 1
    assert len(result.top_improvements) == 5
    assert result.top_improvements[0].rank == 1


def test_anthropic_enricher_raises_on_missing_sdk() -> None:
    from reposage.enrichment.anthropic_provider import AnthropicEnricher

    report = _make_report()
    with patch.dict(sys.modules, {"anthropic": None}):  # type: ignore[dict-item]
        enricher = AnthropicEnricher()
        with pytest.raises(ImportError, match="reposage\\[ai\\]"):
            enricher.enrich(report)


def test_extract_tool_input_raises_when_no_tool_block() -> None:
    from reposage.enrichment.anthropic_provider import _extract_tool_input

    block = MagicMock()
    block.type = "text"

    message = MagicMock()
    message.content = [block]

    with pytest.raises(ValueError, match="audit_enrichment"):
        _extract_tool_input(message)


def test_parse_result_handles_empty_lists() -> None:
    from reposage.enrichment.anthropic_provider import _parse_result

    result = _parse_result(
        {"module_roles": [], "debt_items": [], "top_improvements": []},
        model_id="test-model",
    )
    assert result.module_roles == []
    assert result.debt_items == []
    assert result.top_improvements == []
    assert result.model_id == "test-model"


# ---------------------------------------------------------------------------
# Markdown renderer — enrichment sections
# ---------------------------------------------------------------------------


def test_markdown_report_with_enrichment_contains_new_sections() -> None:
    report = _make_report()
    enrichment = _make_enrichment()
    rendered = render_markdown_report(report, enrichment=enrichment)

    assert "## Module Responsibilities" in rendered
    assert "## Technical Debt" in rendered
    assert "## Top 5 Improvements" in rendered


def test_markdown_report_without_enrichment_has_no_enrichment_sections() -> None:
    report = _make_report()
    rendered = render_markdown_report(report)

    assert "## Module Responsibilities" not in rendered
    assert "## Technical Debt" not in rendered


def test_markdown_enrichment_empty_roles_shows_placeholder() -> None:
    report = _make_report()
    enrichment = EnrichmentResult()
    rendered = render_markdown_report(report, enrichment=enrichment)

    assert "_(no module roles returned)_" in rendered
    assert "_(no debt items returned)_" in rendered


def test_markdown_enrichment_shows_role_table() -> None:
    report = _make_report()
    enrichment = _make_enrichment(roles=1)
    rendered = render_markdown_report(report, enrichment=enrichment)

    assert "| Module | Layer | Responsibility |" in rendered
    assert "src/mod0" in rendered


def test_markdown_enrichment_shows_improvements() -> None:
    report = _make_report()
    enrichment = _make_enrichment(improvements=5)
    rendered = render_markdown_report(report, enrichment=enrichment)

    assert "1. **Improve 0**" in rendered


# ---------------------------------------------------------------------------
# JSON renderer — enrichment key
# ---------------------------------------------------------------------------


def test_json_report_without_enrichment_has_no_enrichment_key() -> None:
    report = _make_report()
    payload = json.loads(render_json_report(report))
    assert "enrichment" not in payload


def test_json_report_with_enrichment_has_enrichment_key() -> None:
    report = _make_report()
    enrichment = _make_enrichment()
    payload = json.loads(render_json_report(report, enrichment=enrichment))

    assert "enrichment" in payload
    assert "module_roles" in payload["enrichment"]
    assert "debt_items" in payload["enrichment"]
    assert "top_improvements" in payload["enrichment"]


# ---------------------------------------------------------------------------
# CLI --enrich flag
# ---------------------------------------------------------------------------


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
    fake_anthropic = _make_fake_anthropic_module(tool_input)
    env = {"ANTHROPIC_API_KEY": "test-key"}

    with patch.dict("os.environ", env), patch.dict(sys.modules, {"anthropic": fake_anthropic}):
        result = main(
            ["report", str(fixture_path("python_repo")), "--enrich", "--output", str(out_file)]
        )

    assert result == 0
    content = out_file.read_text(encoding="utf-8")
    assert "## Module Responsibilities" in content
