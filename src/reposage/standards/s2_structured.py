"""Standard 2: Structured. Packaging, module boundaries, config externalization."""

from __future__ import annotations

import re
import sys
import tomllib
import venv
from pathlib import Path
from tempfile import TemporaryDirectory

from reposage.standards._secrets import evaluate_config_external
from reposage.standards._subproc import run
from reposage.standards.config import StandardsConfig
from reposage.standards.context import AuditContext
from reposage.standards.models import (
    CheckResult,
    CheckStatus,
    StandardResult,
    build_standard_result,
)

# Raw I/O tokens that do not belong inside model/serving code.
_IO_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("read_csv", re.compile(r"\bread_csv\(")),
    ("read_parquet", re.compile(r"\bread_parquet\(")),
    ("read_json", re.compile(r"\bread_json\(")),
    ("requests.get", re.compile(r"\brequests\.get\(")),
    ("httpx.get", re.compile(r"\bhttpx\.get\(")),
    ("open(write)", re.compile(r"""\bopen\([^)]*,\s*["'][rbx+]*[wa][rbx+]*["']""")),
    ("psycopg", re.compile(r"\bpsycopg2?\b")),
    ("create_engine", re.compile(r"\bcreate_engine\(")),
)


def evaluate(ctx: AuditContext, config: StandardsConfig) -> StandardResult:
    """Evaluate Standard 2: structured, installable, and boundary-respecting code."""

    checks = [
        _package(ctx, config),
        _boundaries(ctx),
        evaluate_config_external(ctx, config),
    ]
    return build_standard_result(2, "Structured", checks)


def _package(ctx: AuditContext, config: StandardsConfig) -> CheckResult:
    cid, name = "s2.package", "Package"
    pyproject = _load_pyproject(ctx.root)
    project_name = _project_name(pyproject)
    has_build = "build-system" in pyproject
    has_pkg_dir = _has_package_dir(ctx)

    if config.run_subprocess_checks:
        return _package_subprocess(ctx, config, project_name)

    if not pyproject or (project_name is None and not has_build):
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            evidence=["no packaging metadata; add [project] and [build-system] to pyproject.toml"],
            remediation="Make the project pip-installable with a pyproject.toml.",
        )
    missing = [
        label
        for label, present in (
            ("[project].name", project_name is not None),
            ("[build-system]", has_build),
            ("package directory", has_pkg_dir),
        )
        if not present
    ]
    if missing:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            evidence=[f"packaging metadata incomplete: missing {', '.join(missing)}"],
            remediation="Complete pyproject.toml packaging metadata and add a package directory.",
        )
    return CheckResult(
        cid,
        name,
        CheckStatus.UNCERTAIN,
        evidence=["looks installable; rerun with --run-subprocess-checks to verify"],
        remediation="Verify an editable install in a clean environment.",
    )


def _package_subprocess(
    ctx: AuditContext, config: StandardsConfig, project_name: str | None
) -> CheckResult:
    cid, name = "s2.package", "Package"
    pkg = _import_name(ctx, project_name)
    if pkg is None:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            evidence=["no importable package found to install"],
            remediation="Add a package directory with an __init__.py.",
        )
    with TemporaryDirectory() as tmp:
        venv_dir = Path(tmp) / "venv"
        venv.create(venv_dir, with_pip=True)
        python = (
            venv_dir
            / ("Scripts" if sys.platform == "win32" else "bin")
            / ("python.exe" if sys.platform == "win32" else "python")
        )
        install = run(
            [str(python), "-m", "pip", "install", "-e", str(ctx.root)],
            cwd=Path(tmp),
            timeout=config.install_timeout,
        )
        if install is None:
            return CheckResult(
                cid, name, CheckStatus.UNCERTAIN, evidence=["editable install timed out"]
            )
        if install.returncode != 0:
            return CheckResult(
                cid,
                name,
                CheckStatus.FAIL,
                evidence=[f"pip install -e failed: {_tail(install.stderr)}"],
                remediation="Fix the packaging so an editable install succeeds.",
            )
        imported = run(
            [str(python), "-c", f"import {pkg}"], cwd=Path(tmp), timeout=config.git_timeout
        )
    if imported is None:
        return CheckResult(cid, name, CheckStatus.UNCERTAIN, evidence=["import check timed out"])
    if imported.returncode == 0 and not imported.stdout.strip():
        return CheckResult(
            cid, name, CheckStatus.PASS, evidence=[f"installed and imported '{pkg}' cleanly"]
        )
    return CheckResult(
        cid,
        name,
        CheckStatus.FAIL,
        evidence=[f"import {pkg} failed: {_tail(imported.stderr)}"],
        remediation="Fix import errors surfaced by a clean install.",
    )


def _boundaries(ctx: AuditContext) -> CheckResult:
    cid, name = "s2.boundaries", "Module boundaries"
    targets = [rel for rel, role in ctx.roles.items() if role in ("training", "serving")]
    if not targets:
        return CheckResult(cid, name, CheckStatus.PASS, evidence=["no model/serving code detected"])

    hits: list[str] = []
    for rel in sorted(targets):
        text = _read(ctx.root / rel)
        if text is None:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for label, pattern in _IO_PATTERNS:
                if pattern.search(line):
                    hits.append(f"{rel}:{lineno} raw I/O ({label}) in model/serving code")
                    break
    if hits:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            evidence=hits,
            remediation="Move data and network I/O into a dedicated data or pipeline module.",
        )
    return CheckResult(cid, name, CheckStatus.PASS, evidence=["no raw I/O in model/serving code"])


def _load_pyproject(root: Path) -> dict[str, object]:
    path = root / "pyproject.toml"
    if not path.exists():
        return {}
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def _project_name(pyproject: dict[str, object]) -> str | None:
    project = pyproject.get("project")
    if isinstance(project, dict):
        name = project.get("name")
        if isinstance(name, str) and name:
            return name
    return None


def _has_package_dir(ctx: AuditContext) -> bool:
    return any(p.endswith("__init__.py") for p in ctx.python_asts)


def _import_name(ctx: AuditContext, project_name: str | None) -> str | None:
    inits = sorted(p for p in ctx.python_asts if p.endswith("__init__.py"))
    for rel in inits:
        parts = rel.split("/")
        if parts and parts[0] in ("src", "lib") and len(parts) >= 3:
            return parts[1]
        if len(parts) == 2:
            return parts[0]
    if project_name:
        return project_name.replace("-", "_")
    return None


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _tail(text: str, limit: int = 300) -> str:
    stripped = text.strip()
    return stripped[-limit:] if len(stripped) > limit else stripped
