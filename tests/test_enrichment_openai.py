"""Tests for the OpenAI SDK enrichment provider."""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from reposage.enrichment.models import EnrichmentResult
from tests.conftest import make_fake_openai_module, make_report


def test_openai_enricher_returns_enrichment_result() -> None:
    from reposage.enrichment.openai_provider import OpenAIEnricher

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
    fake_openai = make_fake_openai_module(tool_input)
    report = make_report()

    with patch.dict(sys.modules, {"openai": fake_openai}):
        enricher = OpenAIEnricher()
        result = enricher.enrich(report)

    assert isinstance(result, EnrichmentResult)
    assert len(result.module_roles) == 1
    assert result.module_roles[0].layer == "domain"
    assert len(result.debt_items) == 1
    assert len(result.top_improvements) == 5
    assert result.top_improvements[0].rank == 1
    assert result.model_id == "gpt-4o-mini"


def test_openai_enricher_raises_on_missing_sdk() -> None:
    from reposage.enrichment.openai_provider import OpenAIEnricher

    report = make_report()
    with patch.dict(sys.modules, {"openai": None}):  # type: ignore[dict-item]
        enricher = OpenAIEnricher()
        with pytest.raises(ImportError, match="reposage\\[ai\\]"):
            enricher.enrich(report)


def test_openai_extract_tool_input_raises_when_no_tool_calls() -> None:
    from reposage.enrichment.openai_provider import _extract_tool_input

    message = MagicMock()
    message.tool_calls = None

    choice = MagicMock()
    choice.message = message

    completion = MagicMock()
    completion.choices = [choice]

    with pytest.raises(ValueError, match="audit_enrichment"):
        _extract_tool_input(completion)


def test_openai_enricher_uses_custom_model() -> None:
    from reposage.enrichment.openai_provider import OpenAIEnricher

    tool_input: dict[str, Any] = {
        "module_roles": [],
        "debt_items": [],
        "top_improvements": [],
    }
    fake_openai = make_fake_openai_module(tool_input)
    report = make_report()

    with patch.dict(sys.modules, {"openai": fake_openai}):
        enricher = OpenAIEnricher(model="gpt-4o")
        result = enricher.enrich(report)

    assert result.model_id == "gpt-4o"
