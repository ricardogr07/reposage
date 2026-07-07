"""Tests for Standard 0 (Reproducible) checks."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from reposage.standards import s0_reproducible
from reposage.standards.config import StandardsConfig
from reposage.standards.context import AuditContext, build_context
from reposage.standards.models import CheckResult, CheckStatus

_CONFIG = StandardsConfig()


def _eval(root: Path) -> AuditContext:
    return build_context(root, _CONFIG)


def _check(root: Path, check_id: str) -> CheckResult:
    result = s0_reproducible.evaluate(_eval(root), _CONFIG)
    return next(c for c in result.checks if c.check_id == check_id)


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ── s0.env_spec ────────────────────────────────────────────────────────────


def test_env_spec_declared_import_passes(tmp_path: Path) -> None:
    _write(tmp_path, "requirements.txt", "numpy\npandas\n")
    _write(tmp_path, "pkg.py", "import numpy as np\nimport pandas as pd\n")
    check = _check(tmp_path, "s0.env_spec")
    assert check.status is CheckStatus.PASS


def test_env_spec_undeclared_import_fails(tmp_path: Path) -> None:
    _write(tmp_path, "requirements.txt", "numpy\n")
    _write(tmp_path, "pkg.py", "import torch\n")
    check = _check(tmp_path, "s0.env_spec")
    assert check.status is CheckStatus.FAIL
    assert any("torch" in line for line in check.evidence)


def test_env_spec_unknown_import_passes_with_note(tmp_path: Path) -> None:
    _write(tmp_path, "requirements.txt", "requests\n")
    _write(tmp_path, "pkg.py", "import quux_unknown_lib\n")
    check = _check(tmp_path, "s0.env_spec")
    assert check.status is CheckStatus.PASS
    assert any("quux_unknown_lib" in line for line in check.evidence)


def test_env_spec_missing_spec_fails(tmp_path: Path) -> None:
    _write(tmp_path, "pkg.py", "import numpy\n")
    check = _check(tmp_path, "s0.env_spec")
    assert check.status is CheckStatus.FAIL


# ── s0.lockfile ────────────────────────────────────────────────────────────


def test_lockfile_absent_fails(tmp_path: Path) -> None:
    _write(tmp_path, "requirements.txt", "numpy\n")
    check = _check(tmp_path, "s0.lockfile")
    assert check.status is CheckStatus.FAIL


def test_lockfile_present_no_git_passes(tmp_path: Path) -> None:
    _write(tmp_path, "pyproject.toml", "[project]\nname='x'\n")
    _write(tmp_path, "uv.lock", "# lock\n")
    check = _check(tmp_path, "s0.lockfile")
    assert check.status is CheckStatus.PASS


def _git(repo: Path, *args: str, when: str | None = None) -> None:
    env = dict(os.environ)
    if when is not None:
        env["GIT_AUTHOR_DATE"] = when
        env["GIT_COMMITTER_DATE"] = when
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True, env=env)


def test_lockfile_stale_relative_to_spec_fails(tmp_path: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("git not available")
    _write(tmp_path, "uv.lock", "# lock\n")
    _write(tmp_path, "pyproject.toml", "[project]\nname='x'\n")
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.name", "T")
    _git(tmp_path, "config", "user.email", "t@e.com")
    _git(tmp_path, "add", "uv.lock")
    _git(tmp_path, "commit", "-m", "Add lockfile", when="2021-01-01T00:00:00")
    _git(tmp_path, "add", "pyproject.toml")
    _git(tmp_path, "commit", "-m", "Add spec later", when="2022-06-01T00:00:00")

    check = _check(tmp_path, "s0.lockfile")
    assert check.status is CheckStatus.FAIL
    assert any("predates" in line for line in check.evidence)


# ── s0.determinism ─────────────────────────────────────────────────────────


def test_determinism_unseeded_fails(tmp_path: Path) -> None:
    _write(tmp_path, "train.py", "import numpy as np\nx = np.random.rand(3)\n")
    check = _check(tmp_path, "s0.determinism")
    assert check.status is CheckStatus.FAIL
    assert any("train.py" in line for line in check.evidence)


def test_determinism_seeded_passes(tmp_path: Path) -> None:
    _write(tmp_path, "train.py", "import numpy as np\nnp.random.seed(0)\nx = np.random.rand(3)\n")
    check = _check(tmp_path, "s0.determinism")
    assert check.status is CheckStatus.PASS


def test_determinism_no_sources_passes(tmp_path: Path) -> None:
    _write(tmp_path, "train.py", "def train():\n    return 1\n")
    check = _check(tmp_path, "s0.determinism")
    assert check.status is CheckStatus.PASS
    assert any("no random sources" in line for line in check.evidence)
