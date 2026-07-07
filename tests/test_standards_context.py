"""Tests for role classification and DS/ML detection in the audit context."""

from __future__ import annotations

from pathlib import Path

from reposage.standards.config import StandardsConfig
from reposage.standards.context import build_context

_CONFIG = StandardsConfig()


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_role_from_path_tokens(tmp_path: Path) -> None:
    _write(tmp_path, "src/pkg/train.py", "x = 1\n")
    _write(tmp_path, "src/pkg/serve.py", "x = 1\n")
    _write(tmp_path, "src/pkg/pipeline.py", "x = 1\n")
    _write(tmp_path, "src/pkg/data.py", "x = 1\n")
    _write(tmp_path, "src/pkg/util.py", "x = 1\n")

    ctx = build_context(tmp_path, _CONFIG)

    assert ctx.roles["src/pkg/train.py"] == "training"
    assert ctx.roles["src/pkg/serve.py"] == "serving"
    assert ctx.roles["src/pkg/pipeline.py"] == "pipeline"
    assert ctx.roles["src/pkg/data.py"] == "data"
    assert ctx.roles["src/pkg/util.py"] == "other"


def test_imports_override_path_role(tmp_path: Path) -> None:
    _write(tmp_path, "src/pkg/core.py", "import torch\n")
    _write(tmp_path, "src/pkg/handlers.py", "import fastapi\n")

    ctx = build_context(tmp_path, _CONFIG)

    assert ctx.roles["src/pkg/core.py"] == "training"
    assert ctx.roles["src/pkg/handlers.py"] == "serving"


def test_test_files_never_import_overridden(tmp_path: Path) -> None:
    _write(tmp_path, "tests/test_model.py", "import torch\n")

    ctx = build_context(tmp_path, _CONFIG)

    assert ctx.roles["tests/test_model.py"] == "test"


def test_config_globs_win_last(tmp_path: Path) -> None:
    _write(tmp_path, "src/pkg/core.py", "import torch\n")
    config = StandardsConfig(serving_globs=("src/pkg/core.py",))

    ctx = build_context(tmp_path, config)

    assert ctx.roles["src/pkg/core.py"] == "serving"


def test_is_ds_repo_true_from_ds_imports(tmp_path: Path) -> None:
    _write(tmp_path, "src/pkg/util.py", "import pandas\n")

    assert build_context(tmp_path, _CONFIG).is_ds_repo is True


def test_is_ds_repo_false_for_general_repo(tmp_path: Path) -> None:
    _write(tmp_path, "src/pkg/util.py", "import json\n")

    assert build_context(tmp_path, _CONFIG).is_ds_repo is False
