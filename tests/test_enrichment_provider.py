"""Tests for the provider-agnostic EnrichmentProvider Protocol and dispatcher."""

from __future__ import annotations

from reposage.enrichment.models import EnrichmentResult
from reposage.enrichment.provider import EnrichmentProvider, enrich_report
from reposage.models import AuditReport
from tests.conftest import make_enrichment, make_report


class FakeProvider:
    """Minimal in-memory implementation that satisfies EnrichmentProvider."""

    def __init__(self, result: EnrichmentResult) -> None:
        self._result = result

    def enrich(self, report: AuditReport) -> EnrichmentResult:
        return self._result


def test_enrich_report_delegates_to_provider() -> None:
    expected = make_enrichment()
    provider: EnrichmentProvider = FakeProvider(expected)
    report = make_report()
    result = enrich_report(report, provider)
    assert result is expected
