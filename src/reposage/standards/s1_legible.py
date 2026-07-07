"""Standard 1: Legible. Stub evaluator (chunk 1)."""

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
    ("s1.git_history", "Version control"),
    ("s1.docs", "Documentation"),
    ("s1.logging", "Logging"),
)


def evaluate(ctx: AuditContext, config: StandardsConfig) -> StandardResult:
    """Evaluate Standard 1. Not yet implemented: all checks return UNCERTAIN."""

    checks = [
        CheckResult(
            check_id=cid,
            name=name,
            status=CheckStatus.UNCERTAIN,
            evidence=["not implemented"],
        )
        for cid, name in _CHECKS
    ]
    return build_standard_result(1, "Legible", checks)
