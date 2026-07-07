"""Standard 4: Shipped. A deploy path, a locked environment, and gated CI/CD."""

from __future__ import annotations

import re
from pathlib import Path

from reposage.standards.config import StandardsConfig
from reposage.standards.context import AuditContext
from reposage.standards.models import (
    CheckResult,
    CheckStatus,
    StandardResult,
    build_standard_result,
)

_DEPLOY_RE = re.compile(r"\b(deploy|publish|release|push)\b", re.IGNORECASE)
_HEADING_RE = re.compile(r"^#+\s.*(deploy|publish|release)", re.IGNORECASE)
_TARGET_RE = re.compile(r"^(deploy|publish|release)[A-Za-z0-9_-]*:", re.IGNORECASE)
_LOCKFILE_RE = re.compile(r"(uv\.lock|poetry\.lock|requirements[\w.-]*\.lock|requirements\.txt)")
_INSTALL_RE = re.compile(
    r"(uv sync --frozen|uv sync --locked|pip install -r|poetry install)", re.IGNORECASE
)
_FROZEN_CI_RE = re.compile(
    r"(uv sync --frozen|uv sync --locked|pip install -r requirements\.lock)", re.IGNORECASE
)
_TEST_STEP_RE = re.compile(r"\b(pytest|tox)\b", re.IGNORECASE)


def evaluate(ctx: AuditContext, config: StandardsConfig) -> StandardResult:
    """Evaluate Standard 4: deploy path, environment isolation, and CI/CD gating."""

    checks = [
        _check_deploy_path(ctx),
        _check_env_isolation(ctx),
        _check_cicd(ctx),
    ]
    return build_standard_result(4, "Shipped", checks)


def _check_deploy_path(ctx: AuditContext) -> CheckResult:
    cid, name = "s4.deploy_path", "Deploy independence"
    for rel in ctx.workflow_files:
        # Search the filename and job/step bodies, not the ``on:`` trigger block,
        # so a routine ``on: [push]`` does not read as a deploy path.
        jobs_text = "\n".join(_parse_jobs(_read(ctx.root, rel)).values())
        if _DEPLOY_RE.search(rel) or _DEPLOY_RE.search(jobs_text):
            return CheckResult(cid, name, CheckStatus.PASS, [f"deploy/publish workflow: {rel}"])
    for base in ("Makefile", "makefile", "justfile", "Justfile"):
        text = _read_root(ctx, base)
        if text and any(_TARGET_RE.match(line) for line in text.splitlines()):
            return CheckResult(cid, name, CheckStatus.PASS, [f"deploy target in {base}"])
    readme = _find_readme(ctx)
    if readme and _readme_deploy_section(_read(ctx.root, readme)):
        return CheckResult(
            cid, name, CheckStatus.PASS, [f"deploy section with a command in {readme}"]
        )
    return CheckResult(
        cid,
        name,
        CheckStatus.FAIL,
        ["no deploy/publish/release workflow, make target, or documented command found"],
        "Add a one-command deploy path (a workflow, make target, or documented command).",
    )


def _readme_deploy_section(text: str) -> bool:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if _HEADING_RE.match(line):
            window = lines[index + 1 : index + 11]
            if any("```" in following for following in window):
                return True
    return False


def _check_env_isolation(ctx: AuditContext) -> CheckResult:
    cid, name = "s4.env_isolation", "Environment isolation"
    dockerfile = _find_dockerfile(ctx)
    if dockerfile:
        return _check_dockerfile(ctx, cid, name, dockerfile)
    lock = _root_lockfile(ctx)
    ci_frozen = any(_FROZEN_CI_RE.search(_read(ctx.root, rel)) for rel in ctx.workflow_files)
    if lock and ci_frozen:
        return CheckResult(
            cid,
            name,
            CheckStatus.PASS,
            [f"CI installs from {lock} frozen", "weaker form: locked environment, no container"],
        )
    return CheckResult(
        cid,
        name,
        CheckStatus.FAIL,
        ["no Dockerfile and no CI step installing from a lockfile frozen"],
        "Build a container that installs from a committed lockfile, or freeze the CI install.",
    )


def _check_dockerfile(ctx: AuditContext, cid: str, name: str, dockerfile: str) -> CheckResult:
    text = _read(ctx.root, dockerfile)
    copies_lock = any(
        line.strip().upper().startswith(("COPY", "ADD")) and _LOCKFILE_RE.search(line)
        for line in text.splitlines()
    )
    installs = bool(_INSTALL_RE.search(text))
    if copies_lock and installs:
        return CheckResult(
            cid,
            name,
            CheckStatus.PASS,
            [f"{dockerfile} copies a lockfile and installs from it"],
        )
    return CheckResult(
        cid,
        name,
        CheckStatus.FAIL,
        [f"{dockerfile} resolves dependencies fresh at build time (no locked install)"],
        "Copy the lockfile into the image and install from it frozen.",
    )


def _check_cicd(ctx: AuditContext) -> CheckResult:
    cid, name = "s4.cicd", "CI/CD"
    if not ctx.workflow_files:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            ["no CI workflow files found"],
            "Add a CI workflow that runs the test suite on every push.",
        )
    test_present = False
    deploy_jobs: list[tuple[str, str, set[str], set[str]]] = []
    for rel in ctx.workflow_files:
        jobs = _parse_jobs(_read(ctx.root, rel))
        test_ids = {job_id for job_id, body in jobs.items() if _TEST_STEP_RE.search(body)}
        test_present = test_present or bool(test_ids)
        for job_id, body in jobs.items():
            if _DEPLOY_RE.search(job_id) or _DEPLOY_RE.search(body):
                deploy_jobs.append((rel, job_id, _needs_ids(body), test_ids))
    if not test_present:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            ["CI does not run the test suite (no pytest/tox step found)"],
            "Add a job step that runs pytest or tox.",
        )
    if not deploy_jobs:
        return CheckResult(
            cid,
            name,
            CheckStatus.PASS,
            ["CI runs tests; no deploy job to gate"],
        )
    for rel, job_id, needs, test_ids in deploy_jobs:
        if needs & test_ids:
            return CheckResult(
                cid,
                name,
                CheckStatus.PASS,
                [f"deploy job '{job_id}' in {rel} needs the test job"],
            )
    return CheckResult(
        cid,
        name,
        CheckStatus.UNCERTAIN,
        ["a deploy job exists but no needs: reference to the test job was found"],
        "Add needs: <test-job> to the deploy job so it cannot ship past red tests.",
    )


def _parse_jobs(text: str) -> dict[str, str]:
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if re.match(r"^jobs:\s*(#.*)?$", line)), None)
    if start is None:
        return {}
    body = lines[start + 1 :]
    job_indent = _job_indent(body)
    if job_indent is None:
        return {}
    jobs: dict[str, str] = {}
    current: str | None = None
    buffer: list[str] = []
    for line in body:
        if not line.strip():
            buffer.append(line)
            continue
        indent = len(line) - len(line.lstrip())
        if indent == 0:
            break
        match = re.match(r"^(\s*)([A-Za-z0-9_-]+):\s*(#.*)?$", line)
        if match and len(match.group(1)) == job_indent:
            if current is not None:
                jobs[current] = "\n".join(buffer)
            current, buffer = match.group(2), []
        elif current is not None:
            buffer.append(line)
    if current is not None:
        jobs[current] = "\n".join(buffer)
    return jobs


def _job_indent(body: list[str]) -> int | None:
    for line in body:
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        return indent if indent > 0 else None
    return None


def _needs_ids(body: str) -> set[str]:
    ids: set[str] = set()
    lines = body.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^\s*needs:\s*(.*)$", line)
        if not match:
            continue
        inline = match.group(1).strip().strip("[]")
        if inline:
            ids.update(_split_ids(inline))
        else:
            for following in lines[index + 1 :]:
                item = re.match(r"^\s*-\s*(.+)$", following)
                if item:
                    ids.add(item.group(1).strip().strip("'\""))
                elif following.strip():
                    break
    return ids


def _split_ids(inline: str) -> set[str]:
    return {tok.strip().strip("'\"") for tok in re.split(r"[,\s]+", inline) if tok.strip()}


def _find_dockerfile(ctx: AuditContext) -> str | None:
    for record in ctx.file_records:
        base = _basename(record.path).lower()
        if base == "dockerfile" or base.endswith(".dockerfile"):
            return record.path
    return None


def _root_lockfile(ctx: AuditContext) -> str | None:
    for record in ctx.file_records:
        if "/" not in record.path and _LOCKFILE_RE.fullmatch(record.path):
            return record.path
    return None


def _find_readme(ctx: AuditContext) -> str | None:
    for record in ctx.file_records:
        if "/" not in record.path and _basename(record.path).lower().startswith("readme"):
            return record.path
    return None


def _basename(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def _read_root(ctx: AuditContext, base: str) -> str:
    return _read(ctx.root, base) if (ctx.root / base).exists() else ""


def _read(root: Path, rel: str) -> str:
    try:
        return (root / rel).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
