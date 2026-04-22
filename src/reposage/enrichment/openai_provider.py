"""OpenAI SDK implementation of EnrichmentProvider (optional dependency)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import openai as _openai

from reposage.enrichment.anthropic_provider import _parse_result
from reposage.enrichment.classify_prompt import CLASSIFICATION_SCHEMA, build_classification_prompt
from reposage.enrichment.debt_prompt import DEBT_SCHEMA, build_debt_prompt
from reposage.enrichment.models import EnrichmentResult
from reposage.enrichment.synthesis_prompt import SYNTHESIS_SCHEMA, build_synthesis_prompt
from reposage.models import AuditReport

_TOOL_NAME = "audit_enrichment"
_DEFAULT_MODEL = "gpt-4o-mini"

_TOOL_SCHEMA: dict[str, object] = {
    "type": "object",
    "required": ["module_roles", "debt_items", "top_improvements"],
    "properties": {
        "module_roles": CLASSIFICATION_SCHEMA,
        "debt_items": DEBT_SCHEMA,
        "top_improvements": SYNTHESIS_SCHEMA,
    },
}


class OpenAIEnricher:
    """Calls the OpenAI API once and returns a fully populated EnrichmentResult."""

    def __init__(self, model: str = _DEFAULT_MODEL, timeout_seconds: int = 30) -> None:
        self._model = model
        self._timeout = timeout_seconds

    def enrich(self, report: AuditReport) -> EnrichmentResult:
        try:
            import openai
        except ImportError as exc:
            raise ImportError(
                "The 'openai' package is required for OpenAI enrichment. "
                "Install it with: pip install 'reposage[ai]'"
            ) from exc

        client: _openai.OpenAI = openai.OpenAI(timeout=self._timeout)
        combined_prompt = "\n\n---\n\n".join(
            [
                build_classification_prompt(report),
                build_debt_prompt(report),
                build_synthesis_prompt(report),
            ]
        )

        response = client.chat.completions.create(
            model=self._model,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": _TOOL_NAME,
                        "description": (
                            "Structured enrichment of a repository audit: "
                            "module roles, debt items, and top improvements."
                        ),
                        "parameters": _TOOL_SCHEMA,
                    },
                }
            ],
            tool_choice={"type": "function", "function": {"name": _TOOL_NAME}},
            messages=[{"role": "user", "content": combined_prompt}],
        )

        tool_input = _extract_tool_input(response)
        return _parse_result(tool_input, model_id=self._model)


def _extract_tool_input(response: _openai.types.chat.ChatCompletion) -> dict[str, object]:
    choice = response.choices[0]
    tool_calls = choice.message.tool_calls
    if not tool_calls:
        raise ValueError(f"Model did not call tool '{_TOOL_NAME}'; got: {choice.message}")
    return json.loads(tool_calls[0].function.arguments)  # type: ignore[union-attr]
