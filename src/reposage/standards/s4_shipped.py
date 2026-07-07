"""Standard 4: Shipped. Stub evaluator (chunk 1)."""

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
    ("s4.deploy_path", "Deploy independence"),
    ("s4.env_isolation", "Environment isolation"),
    ("s4.cicd", "CI/CD"),
)


def evaluate(ctx: AuditContext, config: StandardsConfig) -> StandardResult:
    """Evaluate Standard 4. Not yet implemented: all checks return UNCERTAIN."""

    checks = [
        CheckResult(
            check_id=cid,
            name=name,
            status=CheckStatus.UNCERTAIN,
            evidence=["not implemented"],
        )
        for cid, name in _CHECKS
    ]
    return build_standard_result(4, "Shipped", checks)
