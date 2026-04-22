"""Tests for enrichment prompt builders and JSON schemas."""

from __future__ import annotations

from tests.conftest import make_report


def test_build_classification_prompt_contains_project_name() -> None:
    from reposage.enrichment.classify_prompt import build_classification_prompt

    report = make_report()
    prompt = build_classification_prompt(report)
    assert report.inventory.project_name in prompt


def test_build_classification_prompt_contains_layer_enum() -> None:
    from reposage.enrichment.classify_prompt import build_classification_prompt

    report = make_report()
    prompt = build_classification_prompt(report)
    assert "infrastructure" in prompt


def test_classification_schema_shape() -> None:
    from reposage.enrichment.classify_prompt import CLASSIFICATION_SCHEMA

    assert CLASSIFICATION_SCHEMA["type"] == "array"
    items = CLASSIFICATION_SCHEMA["items"]
    assert isinstance(items, dict)
    assert "module" in items["properties"]  # type: ignore[index]


def test_build_debt_prompt_contains_project_name() -> None:
    from reposage.enrichment.debt_prompt import build_debt_prompt

    report = make_report()
    prompt = build_debt_prompt(report)
    assert report.inventory.project_name in prompt


def test_debt_schema_max_items() -> None:
    from reposage.enrichment.debt_prompt import DEBT_SCHEMA

    assert DEBT_SCHEMA["maxItems"] == 5


def test_build_synthesis_prompt_contains_project_name() -> None:
    from reposage.enrichment.synthesis_prompt import build_synthesis_prompt

    report = make_report()
    prompt = build_synthesis_prompt(report)
    assert report.inventory.project_name in prompt


def test_synthesis_schema_five_items() -> None:
    from reposage.enrichment.synthesis_prompt import SYNTHESIS_SCHEMA

    assert SYNTHESIS_SCHEMA["minItems"] == 5
    assert SYNTHESIS_SCHEMA["maxItems"] == 5
