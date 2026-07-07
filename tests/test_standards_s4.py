"""Tests for Standard 4: Shipped (deploy path, env isolation, CI/CD gating)."""

from __future__ import annotations

from pathlib import Path

from reposage.standards import s4_shipped
from reposage.standards.config import StandardsConfig
from reposage.standards.context import build_context
from reposage.standards.models import CheckResult, CheckStatus, StandardResult


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run(root: Path) -> StandardResult:
    config = StandardsConfig()
    return s4_shipped.evaluate(build_context(root, config), config)


def _check(result: StandardResult, check_id: str) -> CheckResult:
    return next(check for check in result.checks if check.check_id == check_id)


def test_publish_workflow_passes_deploy_path(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".github/workflows/release.yml",
        "name: Release\non:\n  push:\n    tags: ['v*']\n"
        "jobs:\n  publish:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo publish\n",
    )

    assert _check(_run(tmp_path), "s4.deploy_path").status is CheckStatus.PASS


def test_no_deploy_path_fails(tmp_path: Path) -> None:
    _write(tmp_path, "src/pkg/app.py", "def f() -> int:\n    return 1\n")

    assert _check(_run(tmp_path), "s4.deploy_path").status is CheckStatus.FAIL


def test_dockerfile_without_lockfile_fails_isolation(tmp_path: Path) -> None:
    _write(tmp_path, "Dockerfile", "FROM python:3.12\nRUN pip install fastapi\n")

    assert _check(_run(tmp_path), "s4.env_isolation").status is CheckStatus.FAIL


def test_dockerfile_with_lockfile_passes_isolation(tmp_path: Path) -> None:
    _write(tmp_path, "uv.lock", "version = 1\n")
    _write(tmp_path, "Dockerfile", "FROM python:3.12\nCOPY uv.lock ./\nRUN uv sync --frozen\n")

    assert _check(_run(tmp_path), "s4.env_isolation").status is CheckStatus.PASS


def test_weaker_lockfile_form_passes_with_note(tmp_path: Path) -> None:
    _write(tmp_path, "uv.lock", "version = 1\n")
    _write(
        tmp_path,
        ".github/workflows/ci.yml",
        "jobs:\n  test:\n    steps:\n      - run: uv sync --frozen\n      - run: pytest\n",
    )

    isolation = _check(_run(tmp_path), "s4.env_isolation")

    assert isolation.status is CheckStatus.PASS
    assert any("weaker form" in line for line in isolation.evidence)


def test_workflow_without_pytest_fails_cicd(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".github/workflows/ci.yml",
        "jobs:\n  build:\n    steps:\n      - run: echo build\n",
    )

    assert _check(_run(tmp_path), "s4.cicd").status is CheckStatus.FAIL


def test_deploy_job_without_needs_is_uncertain(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".github/workflows/ci.yml",
        "jobs:\n  test:\n    steps:\n      - run: pytest\n"
        "  deploy:\n    steps:\n      - run: echo deploy\n",
    )

    assert _check(_run(tmp_path), "s4.cicd").status is CheckStatus.UNCERTAIN


def test_gated_deploy_job_passes_cicd(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".github/workflows/ci.yml",
        "jobs:\n  test:\n    steps:\n      - run: pytest\n"
        "  deploy:\n    needs: test\n    steps:\n      - run: echo deploy\n",
    )

    assert _check(_run(tmp_path), "s4.cicd").status is CheckStatus.PASS


def test_pure_ci_without_deploy_passes_cicd(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".github/workflows/ci.yml",
        "jobs:\n  test:\n    steps:\n      - run: pytest\n",
    )

    cicd = _check(_run(tmp_path), "s4.cicd")

    assert cicd.status is CheckStatus.PASS
    assert any("no deploy job" in line for line in cicd.evidence)
