"""Credential detection for s2.config_external: tree, git history, and .env."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from reposage.standards._subproc import run
from reposage.standards.config import StandardsConfig
from reposage.standards.context import AuditContext, _is_excluded
from reposage.standards.models import CheckResult, CheckStatus

# (label, tree regex, history regex). History patterns stay POSIX-ERE friendly
# so `git log -E -G` can use them without Perl.
_ASSIGN = re.compile(
    r"""(?i)(api_key|apikey|secret|token|password|passwd)\s*[:=]\s*["'][^"']{8,}["']"""
)
_URL_CRED = re.compile(r"://[^/\s:@]+:[^/\s:@]+@")
_AKIA = re.compile(r"AKIA[0-9A-Z]{16}")
_OPENAI = re.compile(r"sk-[A-Za-z0-9]{20,}")
_TREE_PATTERNS = (_ASSIGN, _URL_CRED, _AKIA, _OPENAI)

_HISTORY_PATTERNS = (
    # Mirror _ASSIGN's quoted-literal requirement; a bare `token:` matches every
    # function annotation and workflow yaml key ever committed.
    r"(api_key|apikey|secret|token|password|passwd)[[:space:]]*[:=][[:space:]]*[\"'][^\"']{8,}[\"']",
    r"AKIA[0-9A-Z]{16}",
    r"sk-[A-Za-z0-9]{20}",
)

_PLACEHOLDERS = (
    "xxx",
    "your-",
    "your_",
    "example",
    "<",
    "{{",
    "changeme",
    "dummy",
    "test",
    "placeholder",
    "insert",
    "redacted",
)
_BINARY_EXT = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".ico", ".woff", ".woff2"}
)
_MAX_BYTES = 1_000_000


def evaluate_config_external(ctx: AuditContext, config: StandardsConfig) -> CheckResult:
    """Combine tree, history, and .env.example checks into one CheckResult."""

    cid, name = "s2.config_external", "Config externalization"
    tree_hits = _scan_tree(ctx, config)
    env_fail = _env_example_gaps(ctx)
    history_hits, history_uncertain = _scan_history(ctx, config)

    # A scoped-out path is always announced, so a narrowed scan is visible
    # in the report rather than silently blessing whatever it skipped.
    scope_note = (
        [f"secret scan scoped: excluded {', '.join(config.secrets_exclude_globs)}"]
        if config.secrets_exclude_globs
        else []
    )

    evidence: list[str] = []
    evidence.extend(tree_hits)
    evidence.extend(env_fail)
    evidence.extend(history_hits)
    evidence.extend(scope_note)

    if tree_hits or env_fail or history_hits:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            evidence=evidence,
            remediation="Remove secrets from source/history and read config from the environment.",
        )
    if history_uncertain:
        return CheckResult(
            cid,
            name,
            CheckStatus.UNCERTAIN,
            evidence=["git history scan for secrets was inconclusive (timeout or git missing)"]
            + scope_note,
            remediation="Re-run with git available to scan history for leaked credentials.",
        )
    return CheckResult(
        cid,
        name,
        CheckStatus.PASS,
        evidence=["no credential-shaped literals found"] + scope_note,
    )


def _scan_tree(ctx: AuditContext, config: StandardsConfig) -> list[str]:
    hits: list[str] = []
    for record in ctx.file_records:
        ext = (record.extension or "").lower()
        if ext in _BINARY_EXT or record.size_bytes > _MAX_BYTES:
            continue
        if config.secrets_exclude_globs and _is_excluded(record.path, config.secrets_exclude_globs):
            continue
        path = ctx.root / record.path
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern in _TREE_PATTERNS:
                match = pattern.search(line)
                if match and not _is_placeholder(match.group(0)):
                    hits.append(f"{record.path}:{lineno} credential-shaped literal")
                    break
    return hits


def _is_placeholder(matched: str) -> bool:
    lowered = matched.lower()
    return any(token in lowered for token in _PLACEHOLDERS)


def _scan_history(ctx: AuditContext, config: StandardsConfig) -> tuple[list[str], bool]:
    if not ctx.has_git:
        return [], False
    depth = str(config.history_scan_depth)
    pathspec = _history_pathspec(config.secrets_exclude_globs)
    hits: list[str] = []
    for pattern in _HISTORY_PATTERNS:
        proc = run(
            ["git", "log", "-E", "-n", depth, f"-G{pattern}", "--format=%h", *pathspec],
            cwd=ctx.root,
            timeout=config.git_timeout,
        )
        if proc is None:
            return hits, True
        if proc.returncode != 0:
            continue
        shas = [s for s in proc.stdout.split() if s]
        if shas:
            hits.append(f"credential-shaped literal in history (e.g. commit {shas[0]})")
    return hits, False


def _history_pathspec(globs: tuple[str, ...]) -> list[str]:
    """Translate secrets_exclude_globs into git pathspec exclude arguments.

    A trailing ``/**`` becomes a directory pathspec (git's default matching
    already covers everything under a directory); other patterns use glob magic.
    """

    if not globs:
        return []
    spec = ["--", "."]
    for pattern in globs:
        if pattern.endswith("/**"):
            spec.append(f":(exclude){pattern[:-3]}/")
        else:
            spec.append(f":(exclude,glob){pattern}")
    return spec


def _env_example_gaps(ctx: AuditContext) -> list[str]:
    reads = _env_reads(ctx)
    if not reads:
        return []
    example = _find_env_example(ctx)
    if example is None:
        return [f"code reads env vars ({', '.join(sorted(reads))}) but no .env.example exists"]
    declared = _env_example_keys(ctx.root / example)
    missing = sorted(reads - declared)
    if missing:
        return [f".env.example is missing read variables: {', '.join(missing)}"]
    return []


def _env_reads(ctx: AuditContext) -> set[str]:
    names: set[str] = set()
    for tree in ctx.python_asts.values():
        for node in ast.walk(tree):
            names.update(_env_name(node))
    return names


def _env_name(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Subscript) and _is_os_environ(node.value):
        key = _const_str(node.slice)
        return {key} if key else set()
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        attr = node.func.attr
        if attr == "getenv" and _is_os(node.func.value):
            key = _const_str(node.args[0]) if node.args else None
            return {key} if key else set()
        if attr == "get" and _is_os_environ(node.func.value):
            key = _const_str(node.args[0]) if node.args else None
            return {key} if key else set()
    return set()


def _is_os(node: ast.AST) -> bool:
    return isinstance(node, ast.Name) and node.id == "os"


def _is_os_environ(node: ast.AST) -> bool:
    if isinstance(node, ast.Attribute) and node.attr == "environ":
        return _is_os(node.value)
    return isinstance(node, ast.Name) and node.id == "environ"


def _const_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _find_env_example(ctx: AuditContext) -> str | None:
    for record in ctx.file_records:
        if "/" not in record.path and record.path.lower() == ".env.example":
            return record.path
    return None


def _env_example_keys(path: Path) -> set[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    keys: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        keys.add(stripped.split("=", 1)[0].strip())
    return keys
