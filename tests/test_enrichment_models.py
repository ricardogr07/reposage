"""Tests for enrichment data models (EnrichmentResult, ModuleRole, DebtItem, Improvement)."""

from __future__ import annotations

from reposage.enrichment.models import DebtItem, EnrichmentResult, Improvement, ModuleRole


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
