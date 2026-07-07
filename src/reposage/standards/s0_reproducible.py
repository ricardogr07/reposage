"""Standard 0: Reproducible. Environment spec, lockfile, and determinism."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path, PurePosixPath

from reposage.scan.dependencies import summarize_dependencies
from reposage.standards._subproc import run
from reposage.standards.config import StandardsConfig
from reposage.standards.context import AuditContext
from reposage.standards.models import (
    CheckResult,
    CheckStatus,
    StandardResult,
    build_standard_result,
)

_SPEC_FILES = ("pyproject.toml", "requirements.txt", "environment.yml", "setup.py")
_LOCK_FILES = (
    "uv.lock",
    "poetry.lock",
    "requirements.lock",
    "Pipfile.lock",
    "conda-lock.yml",
)

# Import name -> PyPI distribution name. Identity entries keep import == dist so
# a single lookup handles both cases; only names present here are "confident".
_IMPORT_TO_DIST: dict[str, str] = {
    "sklearn": "scikit-learn",
    "skimage": "scikit-image",
    "cv2": "opencv-python",
    "PIL": "pillow",
    "yaml": "pyyaml",
    "dotenv": "python-dotenv",
    "bs4": "beautifulsoup4",
    "dateutil": "python-dateutil",
    "jwt": "pyjwt",
    "serial": "pyserial",
    "docx": "python-docx",
    "pptx": "python-pptx",
    "fitz": "pymupdf",
    "psycopg2": "psycopg2-binary",
    "MySQLdb": "mysqlclient",
    "attr": "attrs",
    "OpenSSL": "pyopenssl",
    "Crypto": "pycryptodome",
    "win32api": "pywin32",
    "opentelemetry": "opentelemetry-sdk",
    "google": "google-api-python-client",
    "numpy": "numpy",
    "pandas": "pandas",
    "scipy": "scipy",
    "polars": "polars",
    "pyarrow": "pyarrow",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "plotly": "plotly",
    "statsmodels": "statsmodels",
    "torch": "torch",
    "tensorflow": "tensorflow",
    "keras": "keras",
    "xgboost": "xgboost",
    "lightgbm": "lightgbm",
    "catboost": "catboost",
    "transformers": "transformers",
    "datasets": "datasets",
    "mlflow": "mlflow",
    "wandb": "wandb",
    "dvc": "dvc",
    "optuna": "optuna",
    "joblib": "joblib",
    "numba": "numba",
    "dask": "dask",
    "ray": "ray",
    "requests": "requests",
    "httpx": "httpx",
    "aiohttp": "aiohttp",
    "flask": "flask",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "starlette": "starlette",
    "pydantic": "pydantic",
    "sqlalchemy": "sqlalchemy",
    "pymongo": "pymongo",
    "redis": "redis",
    "celery": "celery",
    "click": "click",
    "typer": "typer",
    "rich": "rich",
    "structlog": "structlog",
    "loguru": "loguru",
    "tqdm": "tqdm",
    "jinja2": "jinja2",
    "networkx": "networkx",
    "sympy": "sympy",
    "boto3": "boto3",
    "openpyxl": "openpyxl",
    "gradio": "gradio",
    "streamlit": "streamlit",
    "pytest": "pytest",
}

_NORMALIZE = re.compile(r"[-_.]+")
_TOKEN = re.compile(r"[A-Za-z0-9_.-]+")

_SOURCE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("np.random", re.compile(r"\b(?:np|numpy)\.random\.")),
    ("random.", re.compile(r"(?<![\w.])random\.")),
    ("torch random", re.compile(r"\btorch\.(?:rand|randn|randint|randperm|normal)\b")),
    ("default_rng", re.compile(r"\bdefault_rng\(")),
    ("train_test_split", re.compile(r"\btrain_test_split\(")),
    (
        "estimator",
        re.compile(r"\b(?:RandomForest|GradientBoosting|DecisionTree|XGB|KMeans)\w*\("),
    ),
)
_SEED_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:np|numpy)\.random\.seed\("),
    re.compile(r"(?<![\w.])random\.seed\("),
    re.compile(r"\bmanual_seed\("),
    re.compile(r"\brandom_state\s*=\s*(?!None\b)\S"),
    re.compile(r"\bseed\s*=\s*(?!None\b)\S"),
    re.compile(r"\bdefault_rng\(\s*[^)\s]"),
)
_DATA_READ = re.compile(r"\bread_(?:csv|parquet)\(")
_HASH_TOKEN = re.compile(r"\b(?:hashlib|sha256|md5|dvc)\b")


def evaluate(ctx: AuditContext, config: StandardsConfig) -> StandardResult:
    """Evaluate Standard 0: reproducible environment and pipeline."""

    spec = _find_root_file(ctx, _SPEC_FILES)
    checks = [
        _env_spec(ctx, spec),
        _lockfile(ctx, config, spec),
        _determinism(ctx),
    ]
    return build_standard_result(0, "Reproducible", checks)


def _find_root_file(ctx: AuditContext, names: tuple[str, ...]) -> str | None:
    present = {r.path for r in ctx.file_records if "/" not in r.path}
    for name in names:
        if name in present:
            return name
    return None


def _normalize(name: str) -> str:
    return _NORMALIZE.sub("-", name.strip().lower())


def _env_spec(ctx: AuditContext, spec: str | None) -> CheckResult:
    cid, name = "s0.env_spec", "Environment spec"
    if spec is None:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            evidence=["no pyproject.toml/requirements.txt/environment.yml/setup.py at root"],
            remediation="Add a dependency spec (pyproject.toml or requirements.txt) at the root.",
        )

    declared = _declared_names(ctx)
    imports = _third_party_imports(ctx)

    misses: list[str] = []
    unknown: list[str] = []
    covered = 0
    for imp, location in sorted(imports.items()):
        dist = _IMPORT_TO_DIST.get(imp)
        if dist is None:
            unknown.append(imp)
            continue
        if _normalize(dist) in declared:
            covered += 1
        else:
            misses.append(f"{location} imports '{imp}' (distribution '{dist}') not in {spec}")

    if misses:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            evidence=misses,
            remediation=f"Declare the missing distributions in {spec}.",
        )

    evidence = [f"{spec} covers {covered} confident third-party import(s)"]
    if unknown:
        evidence.append(f"not in mapping table, unverified: {', '.join(sorted(unknown))}")
    if not imports:
        evidence = [f"{spec} present; no third-party imports to verify"]
    return CheckResult(cid, name, CheckStatus.PASS, evidence=evidence)


def _declared_names(ctx: AuditContext) -> set[str]:
    """Declared distribution names: parsed manifests plus raw spec-file tokens."""

    summary = summarize_dependencies(ctx.root, ctx.file_records)
    declared = {_normalize(dep.name) for dep in summary.dependencies if dep.ecosystem == "python"}
    for name in _SPEC_FILES:
        path = ctx.root / name
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        declared.update(_normalize(tok) for tok in _TOKEN.findall(text))
    return declared


def _third_party_imports(ctx: AuditContext) -> dict[str, str]:
    """Map each third-party top-level import to its first ``path:line``."""

    own = _own_top_names(ctx)
    stdlib = sys.stdlib_module_names
    found: dict[str, str] = {}
    for rel, tree in ctx.python_asts.items():
        for node in ast.walk(tree):
            top, lineno = _import_top_name(node)
            if top is None:
                continue
            if top in stdlib or top in own or top in found:
                continue
            found[top] = f"{rel}:{lineno}"
    return found


def _import_top_name(node: ast.AST) -> tuple[str | None, int]:
    if isinstance(node, ast.Import):
        alias = node.names[0]
        return alias.name.split(".")[0], node.lineno
    if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
        return node.module.split(".")[0], node.lineno
    return None, 0


def _own_top_names(ctx: AuditContext) -> set[str]:
    names: set[str] = set()
    for rel in ctx.python_asts:
        parts = list(PurePosixPath(rel).parts)
        if parts and parts[0] in ("src", "lib"):
            parts = parts[1:]
        if not parts:
            continue
        first = parts[0]
        if first.endswith(".py"):
            first = first[:-3]
        names.add(first)
    return names


def _lockfile(ctx: AuditContext, config: StandardsConfig, spec: str | None) -> CheckResult:
    cid, name = "s0.lockfile", "Dependency pinning"
    lock = _find_root_file(ctx, _LOCK_FILES)
    if lock is None:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            evidence=[f"no lockfile ({'/'.join(_LOCK_FILES)}) at root"],
            remediation="Generate a lockfile (uv lock / poetry lock) and commit it.",
        )

    if ctx.has_git and spec is not None:
        lock_ct = _last_commit_time(ctx, config, lock)
        spec_ct = _last_commit_time(ctx, config, spec)
        if lock_ct is not None and spec_ct is not None:
            if lock_ct < spec_ct:
                return CheckResult(
                    cid,
                    name,
                    CheckStatus.FAIL,
                    evidence=[f"{lock} predates the last change to {spec}"],
                    remediation="Regenerate the lockfile after changing the spec.",
                )
            return CheckResult(
                cid,
                name,
                CheckStatus.PASS,
                evidence=[f"{lock} present and newer than or equal to {spec}"],
            )
    return CheckResult(
        cid,
        name,
        CheckStatus.PASS,
        evidence=[f"{lock} present (staleness not checked: no git history)"],
    )


def _last_commit_time(ctx: AuditContext, config: StandardsConfig, rel: str) -> int | None:
    proc = run(
        ["git", "log", "-1", "--format=%ct", "--", rel],
        cwd=ctx.root,
        timeout=config.git_timeout,
    )
    if proc is None or proc.returncode != 0:
        return None
    out = proc.stdout.strip()
    return int(out) if out.isdigit() else None


def _determinism(ctx: AuditContext) -> CheckResult:
    cid, name = "s0.determinism", "Determinism"
    targets = [rel for rel, role in ctx.roles.items() if role in ("training", "pipeline")]

    unseeded: list[str] = []
    any_source = False
    reads_without_hash = False
    for rel in sorted(targets):
        text = _read(ctx.root / rel)
        if text is None:
            continue
        source_line = _first_source_line(text)
        if source_line is not None:
            any_source = True
            if not any(p.search(text) for p in _SEED_PATTERNS):
                unseeded.append(f"{rel}:{source_line[1]} {source_line[0]} without seed")
        if _DATA_READ.search(text) and not _HASH_TOKEN.search(text):
            reads_without_hash = True

    if not any_source:
        return CheckResult(
            cid, name, CheckStatus.PASS, evidence=["no random sources detected in model code"]
        )
    if unseeded:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            evidence=unseeded,
            remediation="Set an explicit seed (random_state=, np.random.seed, torch.manual_seed).",
        )
    evidence = ["all random sources are seeded"]
    if reads_without_hash:
        evidence.append("note: data reads present with no hash/version token nearby")
    return CheckResult(cid, name, CheckStatus.PASS, evidence=evidence)


def _first_source_line(text: str) -> tuple[str, int] | None:
    for lineno, line in enumerate(text.splitlines(), start=1):
        for label, pattern in _SOURCE_PATTERNS:
            if pattern.search(line):
                return label, lineno
    return None


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
