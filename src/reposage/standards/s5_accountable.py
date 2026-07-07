"""Standard 5: Accountable. Stub evaluator (chunk 1)."""

from __future__ import annotations

from reposage.standards.config import StandardsConfig
from reposage.standards.context import AuditContext
from reposage.standards.models import (
    CheckResult,
    CheckStatus,
    StandardResult,
    build_standard_result,
)

_CHECKS = (
    ("s5.logs", "Queryable logs"),
    ("s5.metrics", "Metric tracking"),
    ("s5.alerting", "Alerting"),
)


def evaluate(ctx: AuditContext, config: StandardsConfig) -> StandardResult:
    """Evaluate Standard 5. Not yet implemented: all checks return UNCERTAIN."""

    checks = [
        CheckResult(
            check_id=cid,
            name=name,
            status=CheckStatus.UNCERTAIN,
            evidence=["not implemented"],
        )
        for cid, name in _CHECKS
    ]
    return build_standard_result(5, "Accountable", checks)
