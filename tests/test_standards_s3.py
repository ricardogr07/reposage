"""Tests for Standard 3: Proven (test suite, behavioral coverage, eval gate)."""

from __future__ import annotations

from pathlib import Path

import pytest

from reposage.standards import s3_proven
from reposage.standards.config import StandardsConfig
from reposage.standards.context import AuditContext, build_context
from reposage.standards.models import CheckResult, CheckStatus, StandardResult


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _ctx(root: Path, **cfg: object) -> tuple[AuditContext, StandardsConfig]:
    config = StandardsConfig(**cfg)  # type: ignore[arg-type]
    return build_context(root, config), config


def _check(result: StandardResult, check_id: str) -> CheckResult:
    return next(check for check in result.checks if check.check_id == check_id)


def _run(root: Path, **cfg: object) -> StandardResult:
    ctx, config = _ctx(root, **cfg)
    return s3_proven.evaluate(ctx, config)


def test_no_tests_suite_fails(tmp_path: Path) -> None:
    _write(tmp_path, "src/pkg/app.py", "def f() -> int:\n    return 1\n")

    suite = _check(_run(tmp_path), "s3.suite")

    assert suite.status is CheckStatus.FAIL


def test_static_mode_with_tests_is_uncertain(tmp_path: Path) -> None:
    _write(tmp_path, "tests/test_x.py", "def test_x():\n    assert 1 == 1\n")

    suite = _check(_run(tmp_path), "s3.suite")

    assert suite.status is CheckStatus.UNCERTAIN
    assert "run-subprocess-checks" in suite.evidence[0]


@pytest.mark.subprocess
def test_subprocess_passing_suite(tmp_path: Path) -> None:
    _write(tmp_path, "tests/test_ok.py", "def test_ok():\n    assert 1 + 1 == 2\n")

    suite = _check(_run(tmp_path, run_subprocess_checks=True), "s3.suite")

    assert suite.status is CheckStatus.PASS


@pytest.mark.subprocess
def test_subprocess_failing_suite(tmp_path: Path) -> None:
    _write(tmp_path, "tests/test_bad.py", "def test_bad():\n    assert 1 == 2\n")

    suite = _check(_run(tmp_path, run_subprocess_checks=True), "s3.suite")

    assert suite.status is CheckStatus.FAIL


def test_inner_audit_guard_short_circuits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REPOSAGE_INNER_AUDIT", "1")
    _write(tmp_path, "tests/test_ok.py", "def test_ok():\n    assert 1 == 1\n")

    suite = _check(_run(tmp_path, run_subprocess_checks=True), "s3.suite")

    assert suite.status is CheckStatus.UNCERTAIN
    assert "nested audit" in suite.evidence[0]


def test_bare_tests_fail_behavioral(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "tests/test_smoke.py",
        "def test_runs():\n    result = f()\n    assert result\n",
    )

    behavioral = _check(_run(tmp_path), "s3.behavioral")

    assert behavioral.status is CheckStatus.FAIL


def test_approx_tests_pass_behavioral(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "tests/test_calc.py",
        "import pytest\n\n\ndef test_calc():\n    assert value() == pytest.approx(1.0)\n",
    )

    behavioral = _check(_run(tmp_path), "s3.behavioral")

    assert behavioral.status is CheckStatus.PASS


def test_pandera_validate_passes_behavioral(tmp_path: Path) -> None:
    _write(tmp_path, "tests/test_schema.py", "def test_schema():\n    schema.validate(frame)\n")

    behavioral = _check(_run(tmp_path), "s3.behavioral")

    assert behavioral.status is CheckStatus.PASS


def test_no_training_gate_vacuous_pass(tmp_path: Path) -> None:
    _write(tmp_path, "src/pkg/util.py", "def f() -> int:\n    return 1\n")

    gate = _check(_run(tmp_path), "s3.eval_gate")

    assert gate.status is CheckStatus.PASS
    assert "not applicable" in gate.evidence[0]


def test_gate_unwired_is_uncertain(tmp_path: Path) -> None:
    _write(tmp_path, "src/pkg/train.py", "def train() -> int:\n    return 1\n")
    _write(
        tmp_path,
        "src/pkg/gate.py",
        "import sys\n\n\ndef gate(auc: float) -> int:\n"
        "    if auc >= 0.8:\n        return 0\n    sys.exit(1)\n",
    )

    gate = _check(_run(tmp_path), "s3.eval_gate")

    assert gate.status is CheckStatus.UNCERTAIN


def test_gate_wired_via_test_passes(tmp_path: Path) -> None:
    _write(tmp_path, "src/pkg/train.py", "def train() -> int:\n    return 1\n")
    _write(
        tmp_path,
        "tests/test_gate.py",
        "def test_auc_gate():\n    auc = 0.9\n    assert auc >= 0.8\n",
    )

    gate = _check(_run(tmp_path), "s3.eval_gate")

    assert gate.status is CheckStatus.PASS
