"""Prompt and schema for module responsibility classification (RS-021)."""

from __future__ import annotations

from reposage.enrichment.models import ModuleRole
from reposage.models import AuditReport

CLASSIFICATION_SCHEMA: dict[str, object] = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["module", "responsibility", "layer"],
        "properties": {
            "module": {"type": "string"},
            "responsibility": {"type": "string"},
            "layer": {
                "type": "string",
                "enum": [
                    "infrastructure",
                    "domain",
                    "presentation",
                    "test",
                    "tooling",
                ],
            },
        },
    },
}


def build_classification_prompt(report: AuditReport) -> str:
    language_breakdown = (
        ", ".join(
            f"{language.language} ({language.file_count})"
            for language in report.inventory.languages
        )
        or "none"
    )
    main_modules = (
        "\n".join(f"- {module}" for module in report.architecture.main_modules) or "- none detected"
    )
    probable_layers = (
        "\n".join(f"- {layer}" for layer in report.architecture.probable_layers)
        or "- none detected"
    )

    return "\n".join(
        [
            "You are reviewing a RepoSage architecture summary.",
            f"Project name: {report.inventory.project_name}",
            f"Language breakdown: {language_breakdown}",
            "",
            "Main modules:",
            main_modules,
            "",
            "Probable layers:",
            probable_layers,
            "",
            "Classify each listed module into exactly one of these layers:",
            "- infrastructure",
            "- domain",
            "- presentation",
            "- test",
            "- tooling",
            "",
            "For each module, provide a single-sentence description of its primary responsibility.",
            "Use the provided tool input to submit the classifications.",
            "Do not output JSON directly.",
        ]
    )


build_classification_prompt.__doc__ = (
    f"Build the classification prompt for {ModuleRole.__name__}-style tool inputs."
)

__all__ = ["build_classification_prompt", "CLASSIFICATION_SCHEMA"]
