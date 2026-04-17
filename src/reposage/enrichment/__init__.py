"""Optional AI enrichment layer for RepoSage audit reports."""

from reposage.enrichment.models import (
    DebtItem,
    EnrichmentResult,
    Improvement,
    ModuleRole,
)
from reposage.enrichment.provider import EnrichmentProvider, enrich_report

__all__ = [
    "DebtItem",
    "EnrichmentProvider",
    "EnrichmentResult",
    "Improvement",
    "ModuleRole",
    "enrich_report",
]
