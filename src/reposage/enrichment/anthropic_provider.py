"""Anthropic SDK implementation of EnrichmentProvider (optional dependency)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import anthropic as _anthropic

from reposage.config import EnrichConfig
from reposage.enrichment.classify_prompt import CLASSIFICATION_SCHEMA, build_classification_prompt
from reposage.enrichment.debt_prompt import DEBT_SCHEMA, build_debt_prompt
from reposage.enrichment.models import DebtItem, EnrichmentResult, Improvement, ModuleRole
from reposage.enrichment.synthesis_prompt import SYNTHESIS_SCHEMA, build_synthesis_prompt
from reposage.models import AuditReport

_TOOL_NAME = "audit_enrichment"

_TOOL_SCHEMA: dict[str, object] = {
    "type": "object",
    "required": ["module_roles", "debt_items", "top_improvements"],
    "properties": {
        "module_roles": CLASSIFICATION_SCHEMA,
        "debt_items": DEBT_SCHEMA,
        "top_improvements": SYNTHESIS_SCHEMA,
    },
}


class AnthropicEnricher:
    """Calls the Anthropic API once and returns a fully populated EnrichmentResult."""

    def __init__(self, config: EnrichConfig | None = None) -> None:
        self._config = config or EnrichConfig()

    def enrich(self, report: AuditReport) -> EnrichmentResult:
        try:
            import anthropic
        except ImportError as exc:
            raise ImportError(
                "The 'anthropic' package is required for AI enrichment. "
                "Install it with: pip install 'reposage[ai]'"
            ) from exc

        client: _anthropic.Anthropic = anthropic.Anthropic(timeout=self._config.timeout_seconds)
        classify_prompt = build_classification_prompt(report)
        debt_prompt = build_debt_prompt(report)
        synthesis_prompt = build_synthesis_prompt(report)

        combined_prompt = "\n\n---\n\n".join([classify_prompt, debt_prompt, synthesis_prompt])

        response = client.messages.create(
            model=self._config.model,
            max_tokens=4096,
            tools=[
                {
                    "name": _TOOL_NAME,
                    "description": (
                        "Structured enrichment of a repository audit: "
                        "module roles, debt items, and top improvements."
                    ),
                    "input_schema": _TOOL_SCHEMA,
                }
            ],
            tool_choice={"type": "tool", "name": _TOOL_NAME},
            messages=[{"role": "user", "content": combined_prompt}],
        )

        tool_input = _extract_tool_input(response)
        return _parse_result(tool_input, model_id=self._config.model)


def _extract_tool_input(response: _anthropic.types.Message) -> dict[str, object]:
    for block in response.content:
        if block.type == "tool_use" and block.name == _TOOL_NAME:
            return dict(block.input)
    raise ValueError(f"Model did not call tool '{_TOOL_NAME}'; got: {response.content}")


def _parse_result(data: dict[str, object], model_id: str) -> EnrichmentResult:
    raw_roles = data.get("module_roles", [])
    raw_debt = data.get("debt_items", [])
    raw_improvements = data.get("top_improvements", [])

    module_roles = [
        ModuleRole(
            module=str(r["module"]),
            responsibility=str(r["responsibility"]),
            layer=str(r["layer"]),
        )
        for r in (raw_roles if isinstance(raw_roles, list) else [])
    ]

    debt_items = [
        DebtItem(
            title=str(d["title"]),
            severity=str(d["severity"]),
            description=str(d["description"]),
            issue_title=str(d["issue_title"]),
            issue_body=str(d["issue_body"]),
        )
        for d in (raw_debt if isinstance(raw_debt, list) else [])
    ][:5]

    top_improvements = sorted(
        [
            Improvement(
                rank=int(str(i["rank"])),
                title=str(i["title"]),
                rationale=str(i["rationale"]),
                effort=str(i["effort"]),
            )
            for i in (raw_improvements if isinstance(raw_improvements, list) else [])
        ],
        key=lambda imp: imp.rank,
    )

    return EnrichmentResult(
        module_roles=module_roles,
        debt_items=debt_items,
        top_improvements=top_improvements,
        model_id=model_id,
    )
