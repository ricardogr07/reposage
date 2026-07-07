"""Standard 3: Proven. Tests exist, assert behavior, and gate model quality."""

from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

from reposage.analysis.tests import detect_test_files
from reposage.standards._subproc import run
from reposage.standards.config import StandardsConfig
from reposage.standards.context import AuditContext
from reposage.standards.models import (
    CheckResult,
    CheckStatus,
    StandardResult,
    build_standard_result,
)

_INNER_AUDIT_ENV = "REPOSAGE_INNER_AUDIT"
_COLLECTED_RE = re.compile(r"(\d+)\s+tests?\s+collected")
# pytest 9's `-q --collect-only` prints per-file summaries ("tests/test_x.py: 3")
# instead of node ids or a "collected" line.
_COLLECT_FILE_RE = re.compile(r"^\S+\.py: (\d+)\s*$", re.MULTILINE)
_METRIC_RE = re.compile(r"\b(auc|roc_auc|accuracy|precision|recall|f1|rmse|mae)\b", re.IGNORECASE)
_THRESHOLD_RE = re.compile(r"(>=|>|floor|threshold|baseline)", re.IGNORECASE)
_FAILURE_RE = re.compile(r"(sys\.exit|raise |assert )")


def evaluate(ctx: AuditContext, config: StandardsConfig) -> StandardResult:
    """Evaluate Standard 3: test suite, behavioral coverage, and evaluation gate."""

    all_tests = _all_test_files(ctx)
    py_tests = [rel for rel in all_tests if rel in ctx.python_asts]
    checks = [
        _check_suite(ctx, config, all_tests),
        _check_behavioral(ctx, config, py_tests),
        _check_eval_gate(ctx),
    ]
    return build_standard_result(3, "Proven", checks)


def _all_test_files(ctx: AuditContext) -> list[str]:
    detected = set(detect_test_files(ctx.file_records))
    role_tests = {rel for rel, role in ctx.roles.items() if role == "test"}
    return sorted(detected | role_tests)


def _check_suite(ctx: AuditContext, config: StandardsConfig, all_tests: list[str]) -> CheckResult:
    cid, name = "s3.suite", "Test suite"
    if os.environ.get(_INNER_AUDIT_ENV) == "1":
        return CheckResult(
            cid,
            name,
            CheckStatus.UNCERTAIN,
            ["nested audit: inner pytest run skipped to avoid recursion"],
        )
    if not all_tests:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            ["no test suite: no test files detected"],
            "Add a pytest suite under tests/.",
        )
    if not config.run_subprocess_checks:
        return CheckResult(
            cid,
            name,
            CheckStatus.UNCERTAIN,
            [
                f"{len(all_tests)} test file(s) present; rerun with "
                "--run-subprocess-checks to execute them"
            ],
            "Rerun with --run-subprocess-checks to execute the suite.",
        )
    return _run_suite(ctx, config)


def _run_suite(ctx: AuditContext, config: StandardsConfig) -> CheckResult:
    cid, name = "s3.suite", "Test suite"
    env = os.environ.copy()
    env[_INNER_AUDIT_ENV] = "1"
    collect = run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        ctx.root,
        config.pytest_timeout,
        env,
    )
    if collect is None:
        return CheckResult(
            cid,
            name,
            CheckStatus.UNCERTAIN,
            ["pytest collection timed out or pytest is unavailable"],
            "Ensure pytest is installed and the suite collects within the timeout.",
        )
    combined = f"{collect.stdout}\n{collect.stderr}"
    if "No module named pytest" in combined:
        return CheckResult(
            cid,
            name,
            CheckStatus.UNCERTAIN,
            ["pytest is not installed in the auditing environment"],
            "Install pytest where the audit runs so the suite can be executed.",
        )
    count = _parse_collected(combined)
    if count == 0:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            ["pytest collected 0 tests", _tail(collect.stdout + collect.stderr)],
            "Ensure test files are importable and named so pytest collects them.",
        )
    result = run([sys.executable, "-m", "pytest", "-q"], ctx.root, config.pytest_timeout, env)
    if result is None:
        return CheckResult(
            cid,
            name,
            CheckStatus.UNCERTAIN,
            [f"{count} tests collected but the run timed out"],
            "Speed up or shard the suite so it completes within the timeout.",
        )
    if result.returncode == 0:
        return CheckResult(cid, name, CheckStatus.PASS, [f"pytest passed; {count} tests collected"])
    return CheckResult(
        cid,
        name,
        CheckStatus.FAIL,
        [f"pytest failed (exit {result.returncode})", _tail(result.stdout + result.stderr)],
        "Fix the failing tests so the suite is green.",
    )


def _parse_collected(text: str) -> int:
    match = _COLLECTED_RE.search(text)
    if match:
        return int(match.group(1))
    per_file = _COLLECT_FILE_RE.findall(text)
    if per_file:
        return sum(int(count) for count in per_file)
    return sum(1 for line in text.splitlines() if "::" in line)


def _tail(text: str, lines: int = 12) -> str:
    kept = [line for line in text.splitlines() if line.strip()][-lines:]
    return "output tail: " + " | ".join(kept)


def _check_behavioral(
    ctx: AuditContext, config: StandardsConfig, py_tests: list[str]
) -> CheckResult:
    cid, name = "s3.behavioral", "Behavioral coverage"
    functions = _test_functions(ctx, py_tests)
    total = len(functions)
    if total == 0:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            ["no test functions found to assess behavioral coverage"],
            "Write tests whose assertions compare against expected values.",
        )
    bare = [fn.name for fn in functions if not _is_value_bearing(fn)]
    value_bearing = total - len(bare)
    ratio = value_bearing / total
    if ratio >= config.min_behavioral_assert_ratio:
        return CheckResult(
            cid,
            name,
            CheckStatus.PASS,
            [
                f"{value_bearing}/{total} test functions make value-bearing "
                f"assertions (ratio {ratio:.2f})"
            ],
        )
    return CheckResult(
        cid,
        name,
        CheckStatus.FAIL,
        [
            f"only {value_bearing}/{total} test functions assert on values "
            f"(ratio {ratio:.2f}, need {config.min_behavioral_assert_ratio})",
            f"bare examples: {', '.join(bare[:3])}",
        ],
        "Replace smoke tests with assertions that compare against expected values.",
    )


def _test_functions(
    ctx: AuditContext, py_tests: list[str]
) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    functions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for rel in py_tests:
        tree = ctx.python_asts.get(rel)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and (
                node.name == "test" or node.name.startswith("test_")
            ):
                functions.append(node)
    return functions


def _is_value_bearing(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, ast.Assert) and _is_value_assert(node.test):
            return True
        if _is_approx(node) or _is_validate(node) or _is_schema(node) or _is_raises_match(node):
            return True
    return False


def _is_value_assert(test: ast.expr) -> bool:
    if isinstance(test, ast.Compare):
        operands = [test.left, *test.comparators]
        return any(isinstance(op, ast.Constant) for op in operands)
    return False


def _is_approx(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and _attr_name(node.func) == "approx"


def _is_validate(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and _attr_name(node.func) == "validate"


def _is_schema(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id == "DataFrameSchema"
    if isinstance(node, ast.Attribute):
        return node.attr == "DataFrameSchema"
    return False


def _is_raises_match(node: ast.AST) -> bool:
    if isinstance(node, ast.Call) and _attr_name(node.func) == "raises":
        return any(kw.arg == "match" for kw in node.keywords)
    return False


def _attr_name(func: ast.expr) -> str:
    return func.attr if isinstance(func, ast.Attribute) else ""


def _check_eval_gate(ctx: AuditContext) -> CheckResult:
    cid, name = "s3.eval_gate", "Evaluation gate"
    if not any(role == "training" for role in ctx.roles.values()):
        return CheckResult(
            cid,
            name,
            CheckStatus.PASS,
            ["no trained model detected; evaluation gate not applicable"],
        )
    workflow_text = "\n".join(_read(ctx.root, rel) for rel in ctx.workflow_files)
    candidates = [
        record.path
        for record in ctx.file_records
        if record.extension == ".py" and _is_gate_source(_read(ctx.root, record.path))
    ]
    if not candidates:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            ["training code present but no script compares a metric against a threshold and fails"],
            "Add a gate that fails the build when a key metric drops below its baseline.",
        )
    for path in candidates:
        if _basename(path) in workflow_text or _is_pytest_path(path):
            return CheckResult(
                cid,
                name,
                CheckStatus.PASS,
                [f"evaluation gate {path} runs in CI or as a test"],
            )
    return CheckResult(
        cid,
        name,
        CheckStatus.UNCERTAIN,
        [f"gate logic present ({', '.join(candidates[:3])}) but nothing appears to run it"],
        "Wire the gate into CI or a test so a regression fails the build.",
    )


def _is_gate_source(source: str) -> bool:
    return bool(
        _METRIC_RE.search(source) and _THRESHOLD_RE.search(source) and _FAILURE_RE.search(source)
    )


def _is_pytest_path(path: str) -> bool:
    base = _basename(path)
    return base.startswith("test_") or base.endswith("_test.py")


def _basename(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def _read(root: Path, rel: str) -> str:
    try:
        return (root / rel).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
