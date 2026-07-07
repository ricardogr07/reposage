"""Standard 1: Legible. Git history, documentation, and logging."""

from __future__ import annotations

import ast
import re
import statistics
from pathlib import PurePosixPath

from reposage.api._symbol_extractor import extract_public_symbols
from reposage.standards._subproc import run
from reposage.standards.config import StandardsConfig
from reposage.standards.context import AuditContext
from reposage.standards.models import (
    CheckResult,
    CheckStatus,
    StandardResult,
    build_standard_result,
)

_LOW_QUALITY = frozenset(
    {"fix", "wip", "update", "updates", "changes", "change", "stuff", "temp", "tmp", "misc"}
)
_LOGGING_IMPORTS = frozenset({"logging", "structlog", "loguru"})
_CLI_ENTRY = frozenset({"cli.py", "__main__.py"})
_HEX40 = re.compile(r"^[0-9a-f]{40}$")


def evaluate(ctx: AuditContext, config: StandardsConfig) -> StandardResult:
    """Evaluate Standard 1: legible history, docs, and logging."""

    checks = [
        _git_history(ctx, config),
        _docs(ctx, config),
        _logging(ctx),
    ]
    return build_standard_result(1, "Legible", checks)


def _git(ctx: AuditContext, config: StandardsConfig, args: list[str]) -> str | None:
    proc = run(["git", *args], cwd=ctx.root, timeout=config.git_timeout)
    if proc is None or proc.returncode != 0:
        return None
    return proc.stdout


def _git_history(ctx: AuditContext, config: StandardsConfig) -> CheckResult:
    cid, name = "s1.git_history", "Version control"
    if not ctx.has_git:
        return CheckResult(
            cid,
            name,
            CheckStatus.UNCERTAIN,
            evidence=["no git repository detected"],
            remediation="Track the project in git and commit incrementally.",
        )

    count_out = _git(ctx, config, ["rev-list", "--count", "HEAD"])
    if count_out is None or not count_out.strip().isdigit():
        return CheckResult(
            cid,
            name,
            CheckStatus.UNCERTAIN,
            evidence=["git history unavailable (no commits or git missing)"],
            remediation="Commit the project to git.",
        )
    count = int(count_out.strip())
    if count < config.min_commits:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            evidence=[f"only {count} commit(s); threshold is {config.min_commits}"],
            remediation="Build history through small, incremental commits.",
        )

    subjects = (_git(ctx, config, ["log", "--format=%s", "-n", "200"]) or "").splitlines()
    quality = _subject_quality(subjects)
    if quality is not None:
        return CheckResult(cid, name, CheckStatus.FAIL, evidence=quality, remediation=_MSG_REMEDY)

    drop = _single_drop(ctx, config, count)
    if drop is not None:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            evidence=[drop],
            remediation="Grow history incrementally rather than one squashed import.",
        )
    return CheckResult(
        cid, name, CheckStatus.PASS, evidence=[f"{count} commits with legible subjects"]
    )


_MSG_REMEDY = "Write descriptive commit subjects (what changed and why)."


def _subject_quality(subjects: list[str]) -> list[str] | None:
    cleaned = [s.strip() for s in subjects if s.strip()]
    if not cleaned:
        return None
    lengths = [len(s) for s in cleaned]
    low = [s for s in cleaned if _is_low_quality(s)]
    ratio = len(low) / len(cleaned)
    median = statistics.median(lengths)
    if median < 10:
        return [f"median commit subject length is {median:.0f} chars (< 10)"]
    if ratio > 0.30:
        samples = ", ".join(repr(s) for s in low[:5])
        return [f"{ratio:.0%} of subjects are low-signal, e.g. {samples}"]
    return None


def _is_low_quality(subject: str) -> bool:
    lowered = subject.lower()
    if lowered in _LOW_QUALITY:
        return True
    tokens = lowered.split()
    return len(tokens) == 1 and len(tokens[0]) <= 4


def _single_drop(ctx: AuditContext, config: StandardsConfig, count: int) -> str | None:
    if count >= 20:
        return None
    added = _git(ctx, config, ["log", "--diff-filter=A", "--name-only", "--format=%H"])
    tracked = _git(ctx, config, ["ls-files"])
    if added is None or tracked is None:
        return None
    tracked_count = len([line for line in tracked.splitlines() if line.strip()])
    if tracked_count == 0:
        return None
    per_commit = _added_per_commit(added)
    if not per_commit:
        return None
    biggest = max(per_commit.values())
    if biggest / tracked_count > 0.80:
        return f"one commit added {biggest} of {tracked_count} tracked files (> 80%)"
    return None


def _added_per_commit(output: str) -> dict[str, int]:
    per_commit: dict[str, int] = {}
    current: str | None = None
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if _HEX40.match(stripped):
            current = stripped
            per_commit.setdefault(current, 0)
        elif current is not None:
            per_commit[current] += 1
    return per_commit


def _docs(ctx: AuditContext, config: StandardsConfig) -> CheckResult:
    cid, name = "s1.docs", "Documentation"
    has_readme = any(
        "/" not in r.path and r.path.lower().startswith("readme") for r in ctx.file_records
    )
    if not has_readme:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            evidence=["no README at repository root"],
            remediation="Add a README describing purpose, setup, and usage.",
        )

    records = [
        r for r in ctx.file_records if r.extension == ".py" and ctx.roles.get(r.path) != "test"
    ]
    symbols = extract_public_symbols(ctx.root, records, {})
    if not symbols:
        return CheckResult(
            cid, name, CheckStatus.PASS, evidence=["README present; no public symbols to document"]
        )

    documented = sum(1 for s in symbols if s.has_docstring)
    coverage = documented / len(symbols)
    if coverage >= config.min_docstring_coverage:
        return CheckResult(
            cid,
            name,
            CheckStatus.PASS,
            evidence=[f"docstring coverage {coverage:.0%} ({documented}/{len(symbols)})"],
        )
    offenders = sorted({s.module for s in symbols if not s.has_docstring and s.module})[:5]
    return CheckResult(
        cid,
        name,
        CheckStatus.FAIL,
        evidence=[
            f"docstring coverage {coverage:.0%} below {config.min_docstring_coverage:.0%}",
            f"undocumented in: {', '.join(offenders)}",
        ],
        remediation="Add docstrings to public functions and classes.",
    )


def _logging(ctx: AuditContext) -> CheckResult:
    cid, name = "s1.logging", "Logging"
    targets = _logging_targets(ctx)
    if not targets:
        targets = [
            rel
            for rel, tree in ctx.python_asts.items()
            if ctx.roles.get(rel) != "test" and PurePosixPath(rel).name not in _CLI_ENTRY
        ]

    print_files: dict[str, int] = {}
    has_logging = False
    for rel in targets:
        tree = ctx.python_asts.get(rel)
        if tree is None:
            continue
        prints = _count_prints(tree)
        if prints:
            print_files[rel] = prints
        if _imports_logging(tree):
            has_logging = True

    total_prints = sum(print_files.values())
    if not print_files:
        return CheckResult(
            cid, name, CheckStatus.PASS, evidence=["no stray print() calls in checked modules"]
        )
    if has_logging:
        return CheckResult(
            cid,
            name,
            CheckStatus.PASS,
            evidence=[f"logging configured; {total_prints} print call(s) remain"],
        )
    listing = ", ".join(f"{rel} ({n})" for rel, n in sorted(print_files.items()))
    return CheckResult(
        cid,
        name,
        CheckStatus.FAIL,
        evidence=[f"print() used without a logging framework: {listing}"],
        remediation="Replace print() with the logging/structlog module.",
    )


def _logging_targets(ctx: AuditContext) -> list[str]:
    return [
        rel
        for rel, role in ctx.roles.items()
        if role in ("training", "pipeline", "serving") and PurePosixPath(rel).name not in _CLI_ENTRY
    ]


def _count_prints(tree: ast.Module) -> int:
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
    )


def _imports_logging(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(a.name.split(".")[0] in _LOGGING_IMPORTS for a in node.names):
                return True
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.split(".")[0] in _LOGGING_IMPORTS
        ):
            return True
    return False
