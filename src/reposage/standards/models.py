"""Dataclasses for the Six Standards audit engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class CheckStatus(StrEnum):
    """Outcome of a single standards check."""

    PASS = "pass"
    FAIL = "fail"
    UNCERTAIN = "uncertain"
    NOT_APPLICABLE = "not_applicable"


@dataclass(slots=True)
class CheckResult:
    """Result of one individual check within a standard."""

    check_id: str
    name: str
    status: CheckStatus
    evidence: list[str] = field(default_factory=list)
    remediation: str = ""


@dataclass(slots=True)
class StandardResult:
    """Aggregate result for one of the six standards."""

    number: int
    name: str
    checks: list[CheckResult]
    passed_count: int
    passed: bool


def build_standard_result(number: int, name: str, checks: list[CheckResult]) -> StandardResult:
    """Build a StandardResult, computing passed_count and passed from checks.

    A standard passes when every check is PASS or NOT_APPLICABLE. passed_count
    counts only PASS checks.
    """

    passed_count = sum(1 for check in checks if check.status is CheckStatus.PASS)
    passed = bool(checks) and all(
        check.status in (CheckStatus.PASS, CheckStatus.NOT_APPLICABLE) for check in checks
    )
    return StandardResult(
        number=number,
        name=name,
        checks=checks,
        passed_count=passed_count,
        passed=passed,
    )


@dataclass(slots=True)
class FixItem:
    """A single actionable item derived from a failing or uncertain check."""

    standard: int
    check_id: str
    title: str
    priority_note: str = ""


@dataclass(slots=True)
class StandardsReport:
    """Complete Six Standards audit for a repository."""

    root_path: str
    standards: list[StandardResult]
    grade: int
    fix_list: list[FixItem]
    uncertain_count: int
    subprocess_checks_ran: bool
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the report."""

        return asdict(self)
