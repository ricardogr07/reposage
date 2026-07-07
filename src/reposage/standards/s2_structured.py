"""Standard 2: Structured. Stub evaluator (chunk 1)."""

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
    ("s2.package", "Package"),
    ("s2.boundaries", "Module boundaries"),
    ("s2.config_external", "Config externalization"),
)


def evaluate(ctx: AuditContext, config: StandardsConfig) -> StandardResult:
    """Evaluate Standard 2. Not yet implemented: all checks return UNCERTAIN."""

    checks = [
        CheckResult(
            check_id=cid,
            name=name,
            status=CheckStatus.UNCERTAIN,
            evidence=["not implemented"],
        )
        for cid, name in _CHECKS
    ]
    return build_standard_result(2, "Structured", checks)
