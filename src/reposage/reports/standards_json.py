"""JSON rendering for Six Standards audits."""

from __future__ import annotations

import json

from reposage.standards.models import StandardsReport


def render_standards_json(report: StandardsReport) -> str:
    """Render the standards report as formatted, deterministic JSON."""

    return json.dumps(report.to_dict(), indent=2, sort_keys=True)
