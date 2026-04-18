"""FastMCP server exposing RepoSage as a remote MCP tool."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.applications import Starlette

try:
    from mcp.server.fastmcp import FastMCP
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "The 'mcp' and 'uvicorn' packages are required to run the RepoSage server. "
        "Install them with: pip install 'reposage[server]'"
    ) from exc


def _validate_repo_url(repo_url: str) -> None:
    """Raise ValueError for non-https:// URLs."""
    if not repo_url.startswith("https://"):
        raise ValueError(
            f"Only https:// URLs are accepted, got: {repo_url!r}. "
            "git@ and file:// URLs are not supported."
        )


def create_mcp_app() -> Starlette:
    """Return a fresh Starlette ASGI app for the RepoSage MCP server.

    A new FastMCP instance is created on each call so the app can be safely
    used in tests (FastMCP's session manager cannot be restarted after shutdown).
    """
    mcp = FastMCP("reposage", stateless_http=True)

    @mcp.tool()
    async def audit_repository(
        repo_url: str,
        ref: str = "HEAD",
        enrich: bool = False,
    ) -> str:
        """Clone a remote Git repository and return a RepoSage Markdown audit report.

        Args:
            repo_url: HTTPS URL of the repository (e.g. https://github.com/org/repo).
                      Only https:// URLs are accepted.
            ref: Branch name, tag, or commit SHA to audit. Defaults to HEAD.
            enrich: Add AI-generated module roles, debt items, and top-5 improvements.
                    Requires ANTHROPIC_API_KEY to be set in the server environment.
        """
        _validate_repo_url(repo_url)

        tmp = tempfile.mkdtemp(prefix="reposage-")
        try:
            _clone(repo_url, ref, tmp)
            return _audit(Path(tmp), enrich=enrich)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    app = mcp.streamable_http_app()
    app.routes.append(Route("/health", _health, methods=["GET"]))
    return app


def _clone(repo_url: str, ref: str, dest: str) -> None:
    """Clone repo_url at ref into dest. Falls back for non-branch refs."""
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", ref, repo_url, dest],
            check=True,
            capture_output=True,
            timeout=120,
        )
        return
    except subprocess.CalledProcessError:
        pass

    # ref may be a commit SHA not supported by --branch; clone default then fetch ref
    shutil.rmtree(dest, ignore_errors=True)
    subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, dest],
        check=True,
        capture_output=True,
        timeout=120,
    )
    if ref != "HEAD":
        subprocess.run(
            ["git", "-C", dest, "fetch", "--depth", "1", "origin", ref],
            check=True,
            capture_output=True,
            timeout=60,
        )
        subprocess.run(
            ["git", "-C", dest, "checkout", "FETCH_HEAD"],
            check=True,
            capture_output=True,
            timeout=30,
        )


def _audit(root: Path, *, enrich: bool) -> str:
    from reposage.pipeline import build_audit_report
    from reposage.reports.markdown import render_markdown_report

    report = build_audit_report(root)
    enrichment = None

    if enrich:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ValueError(
                "enrich=True requires ANTHROPIC_API_KEY to be set in the server environment."
            )
        from reposage.enrichment.anthropic_provider import AnthropicEnricher
        from reposage.enrichment.provider import enrich_report

        enrichment = enrich_report(report, AnthropicEnricher())

    return render_markdown_report(report, enrichment=enrichment)


async def _health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})
