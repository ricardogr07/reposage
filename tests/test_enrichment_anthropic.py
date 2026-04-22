"""Tests for the Anthropic SDK enrichment provider."""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from reposage.enrichment.models import EnrichmentResult
from tests.conftest import make_fake_anthropic_module, make_report


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
    fake_anthropic = make_fake_anthropic_module(tool_input)
    report = make_report()

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

    report = make_report()
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
