"""Tests for Standard 1 (Legible) checks."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from reposage.standards import s1_legible
from reposage.standards.config import StandardsConfig
from reposage.standards.context import build_context
from reposage.standards.models import CheckResult, CheckStatus
from tests.conftest import make_git_repo

_CONFIG = StandardsConfig()


def _check(root: Path, check_id: str, config: StandardsConfig = _CONFIG) -> CheckResult:
    result = s1_legible.evaluate(build_context(root, config), config)
    return next(c for c in result.checks if c.check_id == check_id)


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_repo(repo: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("git not available")
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "T")
    _git(repo, "config", "user.email", "t@e.com")


# ── s1.git_history ─────────────────────────────────────────────────────────


def test_git_history_single_squashed_drop_fails(tmp_path: Path) -> None:
    files = {f"mod{i}.py": f"x = {i}\n" for i in range(10)}
    repo = make_git_repo(tmp_path, files)
    check = _check(repo, "s1.git_history")
    assert check.status is CheckStatus.FAIL


def test_git_history_good_commits_pass(tmp_path: Path) -> None:
    files = {f"mod{i}.py": f"x = {i}\n" for i in range(12)}
    commits = [[f"mod{2 * i}.py", f"mod{2 * i + 1}.py"] for i in range(6)]
    repo = make_git_repo(tmp_path, files, commits=commits)
    check = _check(repo, "s1.git_history")
    assert check.status is CheckStatus.PASS


def test_git_history_low_quality_subjects_fail(tmp_path: Path) -> None:
    repo = tmp_path
    _init_repo(repo)
    for index, subject in enumerate(["fix", "wip", "update", "stuff", "temp", "misc"]):
        _write(repo, "mod.py", f"x = {index}\n")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-m", subject)
    check = _check(repo, "s1.git_history")
    assert check.status is CheckStatus.FAIL


def test_git_history_one_commit_dominates_fails(tmp_path: Path) -> None:
    repo = tmp_path
    _init_repo(repo)
    for i in range(10):
        _write(repo, f"mod{i}.py", f"x = {i}\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "Import the whole project at once")
    for i in range(5):
        _write(repo, "mod0.py", f"x = 0\n# tweak {i}\n")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-m", f"Adjust module zero revision {i}")
    check = _check(repo, "s1.git_history")
    assert check.status is CheckStatus.FAIL
    assert any("tracked files" in line for line in check.evidence)


def test_git_history_no_git_uncertain(tmp_path: Path) -> None:
    _write(tmp_path, "mod.py", "x = 1\n")
    check = _check(tmp_path, "s1.git_history")
    assert check.status is CheckStatus.UNCERTAIN


# ── s1.docs ────────────────────────────────────────────────────────────────


def test_docs_missing_readme_fails(tmp_path: Path) -> None:
    _write(tmp_path, "mod.py", "def f():\n    '''doc.'''\n    return 1\n")
    check = _check(tmp_path, "s1.docs")
    assert check.status is CheckStatus.FAIL


def test_docs_low_docstring_coverage_fails(tmp_path: Path) -> None:
    _write(tmp_path, "README.md", "# Project\n")
    _write(
        tmp_path,
        "mod.py",
        "def a():\n    '''doc.'''\n    return 1\n\n\n"
        "def b():\n    return 2\n\n\ndef c():\n    return 3\n",
    )
    check = _check(tmp_path, "s1.docs")
    assert check.status is CheckStatus.FAIL


def test_docs_high_docstring_coverage_passes(tmp_path: Path) -> None:
    _write(tmp_path, "README.md", "# Project\n")
    _write(
        tmp_path,
        "mod.py",
        "def a():\n    '''doc.'''\n    return 1\n\n\ndef b():\n    '''doc.'''\n    return 2\n",
    )
    check = _check(tmp_path, "s1.docs")
    assert check.status is CheckStatus.PASS


# ── s1.logging ─────────────────────────────────────────────────────────────


def test_logging_print_without_logging_fails(tmp_path: Path) -> None:
    _write(tmp_path, "train.py", "def train():\n    print('go')\n    return 1\n")
    check = _check(tmp_path, "s1.logging")
    assert check.status is CheckStatus.FAIL
    assert any("train.py" in line for line in check.evidence)


def test_logging_with_framework_passes(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "train.py",
        "import logging\n\n\ndef train():\n    print('go')\n    return 1\n",
    )
    check = _check(tmp_path, "s1.logging")
    assert check.status is CheckStatus.PASS
