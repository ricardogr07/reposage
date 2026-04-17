"""Prompt and schema for top-five improvements synthesis (RS-023)."""

from __future__ import annotations

from reposage.enrichment.models import Improvement
from reposage.models import AuditReport

__all__ = ["build_synthesis_prompt", "SYNTHESIS_SCHEMA"]


SYNTHESIS_SCHEMA: dict[str, object] = {
    "type": "array",
    "minItems": 5,
    "maxItems": 5,
    "items": {
        "type": "object",
        "required": ["rank", "title", "rationale", "effort"],
        "properties": {
            "rank": {"type": "integer", "minimum": 1, "maximum": 5},
            "title": {"type": "string"},
            "rationale": {"type": "string"},
            "effort": {"type": "string", "enum": ["low", "medium", "high"]},
        },
    },
}


def build_synthesis_prompt(report: AuditReport) -> str:
    """Build the tool prompt for five ranked improvement suggestions."""

    def format_items(title: str, items: list[str]) -> str:
        rendered_items = items or ["None"]
        bullet_lines = [f"- {item}" for item in rendered_items]
        return "\n".join([title, *bullet_lines])

    language_parts = [
        f"{language.language}: {language.file_count} files"
        for language in report.inventory.languages
    ]
    language_breakdown = ", ".join(language_parts) if language_parts else "No languages detected"

    quality_summary = "\n".join(
        [
            "Quality signals:",
            f"- Test coverage signal present: {'yes' if report.quality.has_tests else 'no'}",
            f"- CI present: {'yes' if report.quality.ci_present else 'no'}",
            f"- Packaging present: {'yes' if report.quality.packaging_present else 'no'}",
            f"- Lint present: {'yes' if report.quality.lint_present else 'no'}",
            f"- Typing present: {'yes' if report.quality.typing_present else 'no'}",
        ]
    )

    sections = [
        "You are prioritizing the next engineering improvements for a repository audit.",
        "",
        f"Project name: {report.inventory.project_name}",
        f"Quality score: {report.quality.score}",
        f"Language breakdown: {language_breakdown}",
        "",
        quality_summary,
        "",
        format_items("Issue suggestions from risk analysis:", report.risk.issue_suggestions),
        "",
        format_items("Roadmap buckets from risk analysis:", report.risk.roadmap_buckets),
        "",
        format_items("God modules:", report.architecture.god_modules),
        "",
        format_items("Hotspots:", report.architecture.hotspots),
        "",
        "Rank exactly 5 concrete next improvements for this project.",
        "Each improvement must include:",
        "- rank: integer from 1 to 5",
        "- title: concise improvement title",
        "- rationale: 1-2 sentences tied to the audit evidence",
        "- effort: low, medium, or high",
        "Prioritize high-impact, actionable work that follows from the audit findings.",
        "Your output will be captured via tool use. Do not output JSON directly.",
    ]
    return "\n".join(sections)


build_synthesis_prompt.__doc__ = (
    "Build the tool prompt for five ranked "
    f":class:`{Improvement.__module__}.{Improvement.__name__}` suggestions."
)
