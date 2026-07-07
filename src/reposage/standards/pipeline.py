"""Orchestrator for the Six Standards audit."""

from __future__ import annotations

from pathlib import Path

from reposage.standards import (
    s0_reproducible,
    s1_legible,
    s2_structured,
    s3_proven,
    s4_shipped,
    s5_accountable,
)
from reposage.standards.config import StandardsConfig, load_standards_config
from reposage.standards.context import build_context
from reposage.standards.models import (
    CheckResult,
    CheckStatus,
    FixItem,
    StandardResult,
    StandardsReport,
    build_standard_result,
)

_EVALUATORS = (
    s0_reproducible.evaluate,
    s1_legible.evaluate,
    s2_structured.evaluate,
    s3_proven.evaluate,
    s4_shipped.evaluate,
    s5_accountable.evaluate,
)

_S3_PRIORITY_NOTE = (
    "Standard 3, Proven, carries the highest weight; nothing above it can be "
    "trusted until it passes"
)


def build_standards_report(root: Path, config: StandardsConfig | None = None) -> StandardsReport:
    """Build a Six Standards audit report for ``root``.

    When ``config`` is None the config is loaded from the target root; the CLI
    passes an explicit config with its overrides already applied.
    """

    notes: list[str] = []
    if config is None:
        config, cfg_warnings = load_standards_config(root)
        notes.extend(cfg_warnings)

    ctx = build_context(root, config)
    raw = [evaluate(ctx, config) for evaluate in _EVALUATORS]

    skipped = _apply_skips(raw, config)
    if skipped:
        notes.append(f"{skipped} checks skipped by config")

    standards = [build_standard_result(s.number, s.name, s.checks) for s in raw]
    grade = sum(1 for standard in standards if standard.passed)
    uncertain_count = sum(
        1
        for standard in standards
        for check in standard.checks
        if check.status is CheckStatus.UNCERTAIN
    )
    fix_list = _build_fix_list(standards)

    return StandardsReport(
        root_path=str(ctx.root),
        standards=standards,
        grade=grade,
        fix_list=fix_list,
        uncertain_count=uncertain_count,
        # ponytail: no subprocess check runs in chunk 1; real ones land later.
        subprocess_checks_ran=False,
        notes=notes,
    )


def _apply_skips(standards: list[StandardResult], config: StandardsConfig) -> int:
    """Turn skipped checks into PASS in place and return how many were skipped."""

    if not config.skip:
        return 0
    skipped = 0
    for standard in standards:
        for check in standard.checks:
            prefix = check.check_id.split(".")[0]
            if check.check_id in config.skip or prefix in config.skip:
                check.status = CheckStatus.PASS
                check.evidence = ["skipped by config"]
                check.remediation = ""
                skipped += 1
    return skipped


def _build_fix_list(standards: list[StandardResult]) -> list[FixItem]:
    """Build an ascending fix list, flagging Standard 3's first item as priority."""

    fixes: list[FixItem] = []
    for standard in standards:
        for check in standard.checks:
            if _needs_fix(check):
                fixes.append(
                    FixItem(
                        standard=standard.number,
                        check_id=check.check_id,
                        title=check.remediation or check.name,
                    )
                )
    fixes.sort(key=lambda item: item.standard)

    if not _standard_passed(standards, 3):
        for item in fixes:
            if item.standard == 3:
                item.priority_note = _S3_PRIORITY_NOTE
                break
    return fixes


def _needs_fix(check: CheckResult) -> bool:
    return check.status not in (CheckStatus.PASS, CheckStatus.NOT_APPLICABLE)


def _standard_passed(standards: list[StandardResult], number: int) -> bool:
    return any(standard.number == number and standard.passed for standard in standards)
