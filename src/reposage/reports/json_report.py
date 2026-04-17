"""JSON rendering for RepoSage audits."""

from __future__ import annotations

import json
from dataclasses import asdict

from reposage.enrichment.models import EnrichmentResult
from reposage.models import AuditReport


def render_json_report(report: AuditReport, enrichment: EnrichmentResult | None = None) -> str:
    """Render the report as formatted JSON, optionally including enrichment data."""

    data = report.to_dict()
    if enrichment is not None:
        data["enrichment"] = asdict(enrichment)
    return json.dumps(data, indent=2, sort_keys=True)
