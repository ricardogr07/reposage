"""Provider-agnostic enrichment boundary for optional AI features."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from reposage.models import AuditReport

from reposage.enrichment.models import EnrichmentResult


class EnrichmentProvider(Protocol):
    """Minimal interface any enrichment backend must satisfy."""

    def enrich(self, report: AuditReport) -> EnrichmentResult:
        """Return AI-derived enrichment for the given audit report."""
        ...


def enrich_report(report: AuditReport, provider: EnrichmentProvider) -> EnrichmentResult:
    """Delegate enrichment to a configured provider."""
    return provider.enrich(report)
