"""Prompt and schema for debt labeling and GitHub issue draft generation (RS-022)."""

from __future__ import annotations

from reposage.enrichment.models import DebtItem as _DebtItem
from reposage.models import AuditReport

__all__ = ["build_debt_prompt", "DEBT_SCHEMA"]

# Keep a private reference to the target output model for documentation/tooling.
_DOC_DEBT_ITEM = _DebtItem

DEBT_SCHEMA: dict[str, object] = {
    "type": "array",
    "maxItems": 5,
    "items": {
        "type": "object",
        "required": ["title", "severity", "description", "issue_title", "issue_body"],
        "properties": {
            "title": {"type": "string"},
            "severity": {"type": "string", "enum": ["high", "medium", "low"]},
            "description": {"type": "string"},
            "issue_title": {"type": "string"},
            "issue_body": {"type": "string"},
        },
    },
}


def build_debt_prompt(report: AuditReport) -> str:
    """Return a tool-use prompt for up to five debt items matching :class:`DebtItem`."""

    missing = "\n".join(f"  - {s}" for s in report.quality.missing_signals) or "  (none)"
    risks = (
        "\n".join(
            f"  - [{item.severity.value}] {item.title}: {item.rationale}"
            for item in report.risk.items
        )
        or "  (none)"
    )
    weak = "\n".join(f"  - {w}" for w in report.risk.weak_points) or "  (none)"
    candidates = "\n".join(f"  - {c}" for c in report.risk.refactor_candidates) or "  (none)"

    return (
        f"You are reviewing the repository '{report.inventory.project_name}'.\n"
        f"Quality score: {report.quality.score}/100\n\n"
        f"Missing quality signals:\n{missing}\n\n"
        f"Risk items:\n{risks}\n\n"
        f"Weak points:\n{weak}\n\n"
        f"Refactor candidates:\n{candidates}\n\n"
        "Produce up to 5 technical debt items. For each item, provide:\n"
        "  - a title\n"
        "  - severity: high, medium, or low\n"
        "  - a concise description\n"
        "  - a GitHub issue title\n"
        "  - a GitHub issue body in Markdown\n\n"
        "Output will be captured via tool use. Do NOT output JSON directly."
    )
