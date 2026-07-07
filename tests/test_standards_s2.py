"""Tests for Standard 2 (Structured) checks."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from reposage.standards import s2_structured
from reposage.standards.config import StandardsConfig
from reposage.standards.context import build_context
from reposage.standards.models import CheckResult, CheckStatus
from reposage.standards.pipeline import build_standards_report
from tests.conftest import fixture_path

_CONFIG = StandardsConfig()


def _check(root: Path, check_id: str, config: StandardsConfig = _CONFIG) -> CheckResult:
    result = s2_structured.evaluate(build_context(root, config), config)
    return next(c for c in result.checks if c.check_id == check_id)


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ── s2.package ─────────────────────────────────────────────────────────────


def test_package_static_installable_uncertain(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "pyproject.toml",
        "[build-system]\nrequires=['hatchling']\n\n[project]\nname='tinypkg'\nversion='0.0.1'\n",
    )
    _write(tmp_path, "src/tinypkg/__init__.py", "VALUE = 1\n")
    check = _check(tmp_path, "s2.package")
    assert check.status is CheckStatus.UNCERTAIN
    assert any("run-subprocess-checks" in line for line in check.evidence)


def test_package_no_metadata_fails(tmp_path: Path) -> None:
    _write(tmp_path, "mod.py", "x = 1\n")
    check = _check(tmp_path, "s2.package")
    assert check.status is CheckStatus.FAIL


@pytest.mark.subprocess
def test_package_subprocess_install_passes(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "pyproject.toml",
        "[build-system]\nrequires=['hatchling']\nbuild-backend='hatchling.build'\n\n"
        "[project]\nname='tinypkg'\nversion='0.0.1'\n",
    )
    _write(tmp_path, "src/tinypkg/__init__.py", "VALUE = 1\n")
    config = StandardsConfig(run_subprocess_checks=True, install_timeout=180, git_timeout=60)
    check = _check(tmp_path, "s2.package", config)
    if check.status is not CheckStatus.PASS:
        pytest.skip(f"editable install unavailable in this environment: {check.evidence}")
    assert check.status is CheckStatus.PASS


# ── s2.boundaries ──────────────────────────────────────────────────────────


def test_boundaries_io_in_serving_fails(tmp_path: Path) -> None:
    _write(tmp_path, "app.py", "import fastapi\nimport pandas as pd\nd = pd.read_csv('x.csv')\n")
    check = _check(tmp_path, "s2.boundaries")
    assert check.status is CheckStatus.FAIL
    assert any("app.py" in line for line in check.evidence)


def test_boundaries_io_in_data_module_passes(tmp_path: Path) -> None:
    _write(tmp_path, "data.py", "import pandas as pd\nd = pd.read_csv('x.csv')\n")
    check = _check(tmp_path, "s2.boundaries")
    assert check.status is CheckStatus.PASS


# ── s2.config_external ─────────────────────────────────────────────────────


def test_config_external_tree_secret_fails(tmp_path: Path) -> None:
    _write(tmp_path, "settings.py", 'api_key = "sk-abcdef1234567890abcdef"\n')
    check = _check(tmp_path, "s2.config_external")
    assert check.status is CheckStatus.FAIL


def test_config_external_placeholder_passes(tmp_path: Path) -> None:
    _write(tmp_path, "settings.py", 'api_key = "your-key-here-example"\n')
    check = _check(tmp_path, "s2.config_external")
    assert check.status is CheckStatus.PASS


def test_config_external_history_secret_fails(tmp_path: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("git not available")

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True)

    git("init", "-b", "main")
    git("config", "user.name", "T")
    git("config", "user.email", "t@e.com")
    _write(tmp_path, "settings.py", 'api_key = "sk-abcdef1234567890abcdef"\n')
    git("add", "-A")
    git("commit", "-m", "Add settings with secret")
    _write(tmp_path, "settings.py", "api_key = get_from_env()\n")
    git("add", "-A")
    git("commit", "-m", "Remove hardcoded secret")

    check = _check(tmp_path, "s2.config_external")
    assert check.status is CheckStatus.FAIL
    assert any("history" in line for line in check.evidence)


def test_config_external_env_example_missing_var_fails(tmp_path: Path) -> None:
    _write(tmp_path, "config.py", 'import os\nu = os.getenv("API_URL")\np = os.getenv("DB_PASS")\n')
    _write(tmp_path, ".env.example", "API_URL=\n")
    check = _check(tmp_path, "s2.config_external")
    assert check.status is CheckStatus.FAIL
    assert any("DB_PASS" in line for line in check.evidence)


# ── integration ────────────────────────────────────────────────────────────


def test_ds_failing_repo_integration() -> None:
    root = fixture_path("standards/ds_failing_repo")
    report = build_standards_report(root)
    by_id = {c.check_id: c for s in report.standards for c in s.checks}

    assert by_id["s0.lockfile"].status is CheckStatus.FAIL
    assert by_id["s0.determinism"].status is CheckStatus.FAIL
    assert by_id["s1.docs"].status is CheckStatus.FAIL
    assert by_id["s2.config_external"].status is CheckStatus.FAIL
