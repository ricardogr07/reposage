"""Shared audit context: one filesystem walk and AST parse for all checks."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path

from reposage.config import DEFAULT_SCAN_CONFIG
from reposage.models import FileRecord
from reposage.scan.filesystem import scan_repository
from reposage.standards.config import StandardsConfig

_TOKEN_SPLIT = re.compile(r"[^a-z0-9]+")

_TEST_WORDS = frozenset({"test", "tests", "conftest"})
_TRAIN_WORDS = frozenset({"train", "training", "trainer", "fit"})
_SERVE_WORDS = frozenset(
    {"serve", "serving", "server", "service", "app", "api", "predict", "prediction", "endpoint"}
)
_PIPE_WORDS = frozenset({"pipeline", "pipelines", "etl", "feature", "features"})
_DATA_WORDS = frozenset({"data", "loader", "loaders", "dataset", "datasets"})

_SERVING_IMPORTS = frozenset({"fastapi", "flask", "uvicorn", "mcp", "starlette", "django"})
_TRAINING_IMPORTS = frozenset({"sklearn", "torch", "xgboost", "lightgbm", "tensorflow", "keras"})
_DS_IMPORTS = _TRAINING_IMPORTS | frozenset({"pandas", "numpy", "scipy", "polars"})


@dataclass(slots=True)
class AuditContext:
    """Pre-computed repository facts shared by every standard evaluator."""

    root: Path
    file_records: list[FileRecord]
    python_asts: dict[str, ast.Module]
    roles: dict[str, str]
    is_ds_repo: bool
    has_git: bool
    workflow_files: list[str] = field(default_factory=list)


def build_context(root: Path, config: StandardsConfig) -> AuditContext:
    """Walk ``root`` once, parse its Python, and classify module roles."""

    resolved = root.resolve()
    file_records, _ = scan_repository(resolved, DEFAULT_SCAN_CONFIG)

    python_asts: dict[str, ast.Module] = {}
    roles: dict[str, str] = {}
    all_imports: set[str] = set()

    for record in file_records:
        if record.extension != ".py":
            continue
        rel = record.path
        try:
            source = (resolved / rel).read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=rel)
        except SyntaxError:
            roles[rel] = "other"
            continue
        except OSError:
            continue
        python_asts[rel] = tree
        imported = _imported_modules(tree)
        all_imports |= imported
        roles[rel] = _classify(rel, imported, config)

    is_ds_repo = any(role in ("training", "serving") for role in roles.values()) or bool(
        all_imports & _DS_IMPORTS
    )
    workflow_files = [
        record.path
        for record in file_records
        if record.path.startswith(".github/workflows/") and record.extension in (".yml", ".yaml")
    ]

    return AuditContext(
        root=resolved,
        file_records=file_records,
        python_asts=python_asts,
        roles=roles,
        is_ds_repo=is_ds_repo,
        has_git=(resolved / ".git").exists(),
        workflow_files=workflow_files,
    )


def _classify(rel: str, imported: set[str], config: StandardsConfig) -> str:
    """Classify one Python file's role from path, then imports, then globs."""

    role = _role_from_path(rel)
    if role != "test":
        if imported & _SERVING_IMPORTS:
            role = "serving"
        elif imported & _TRAINING_IMPORTS:
            role = "training"
    for pattern in config.serving_globs:
        if fnmatch(rel, pattern):
            role = "serving"
    for pattern in config.training_globs:
        if fnmatch(rel, pattern):
            role = "training"
    return role


def _role_from_path(rel: str) -> str:
    tokens = {token for token in _TOKEN_SPLIT.split(rel.lower()) if token}
    if tokens & _TEST_WORDS:
        return "test"
    if tokens & _TRAIN_WORDS:
        return "training"
    if tokens & _SERVE_WORDS:
        return "serving"
    if tokens & _PIPE_WORDS:
        return "pipeline"
    if tokens & _DATA_WORDS:
        return "data"
    return "other"


def _imported_modules(tree: ast.Module) -> set[str]:
    """Return the set of top-level imported module names."""

    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module.split(".")[0])
    return modules
