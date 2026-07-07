"""FastMCP server exposing RepoSage as a remote MCP tool."""

from __future__ import annotations

import base64
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from reposage.server.observability import observe

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
    """Raise ValueError for non-https:// URLs or URLs with embedded credentials."""
    if not repo_url.startswith("https://"):
        raise ValueError(
            f"Only https:// URLs are accepted, got: {repo_url!r}. "
            "git@ and file:// URLs are not supported."
        )
    parsed = urlparse(repo_url)
    if parsed.username or parsed.password:
        raise ValueError(
            "Credentials must not be embedded in repo_url. "
            "Pass the token via the 'token' parameter or the GITHUB_TOKEN env var."
        )


def _resolve_token(token: str | None) -> str | None:
    return token or os.environ.get("GITHUB_TOKEN") or None


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
        enrich_provider: str = "anthropic",
        token: str | None = None,
    ) -> str:
        """Clone a remote Git repository and return a RepoSage Markdown audit report.

        Args:
            repo_url: HTTPS URL of the repository (e.g. https://github.com/org/repo).
                      Only https:// URLs are accepted. Do not embed credentials in the URL.
            ref: Branch name, tag, or commit SHA to audit. Defaults to HEAD.
            enrich: Add AI-generated module roles, debt items, and top-5 improvements.
            enrich_provider: AI provider for enrichment — "anthropic" (default) or "openai".
                             Requires ANTHROPIC_API_KEY or OPENAI_API_KEY respectively.
            token: Optional personal access token (PAT) or GitHub App token for private
                   repositories. Falls back to the GITHUB_TOKEN environment variable.
        """
        with observe("audit_repository"):
            _validate_repo_url(repo_url)
            effective_token = _resolve_token(token)

            tmp = tempfile.mkdtemp(prefix="reposage-")
            try:
                _clone(repo_url, ref, tmp, token=effective_token)
                return _audit(Path(tmp), enrich=enrich, enrich_provider=enrich_provider)
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

    app = mcp.streamable_http_app()
    app.routes.append(Route("/health", _health, methods=["GET"]))
    return app


def _clone(repo_url: str, ref: str, dest: str, *, token: str | None = None) -> None:
    """Clone repo_url at ref into dest. Falls back for non-branch refs."""
    if token:
        b64 = base64.b64encode(f"x-access-token:{token}".encode()).decode()
        git_auth = ["-c", f"http.extraheader=Authorization: Basic {b64}"]
    else:
        git_auth = []
    try:
        subprocess.run(
            ["git"] + git_auth + ["clone", "--depth", "1", "--branch", ref, repo_url, dest],
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
        ["git"] + git_auth + ["clone", "--depth", "1", repo_url, dest],
        check=True,
        capture_output=True,
        timeout=120,
    )
    if ref != "HEAD":
        subprocess.run(
            ["git"] + git_auth + ["-C", dest, "fetch", "--depth", "1", "origin", ref],
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


def _audit(root: Path, *, enrich: bool, enrich_provider: str = "anthropic") -> str:
    from reposage.pipeline import build_audit_report
    from reposage.reports.markdown import render_markdown_report

    report = build_audit_report(root)
    enrichment = None

    if enrich:
        from reposage.enrichment.provider import enrich_report

        if enrich_provider == "openai":
            if not os.environ.get("OPENAI_API_KEY"):
                raise ValueError(
                    "enrich_provider='openai' requires OPENAI_API_KEY "
                    "to be set in the server environment."
                )
            from reposage.enrichment.openai_provider import OpenAIEnricher

            enrichment = enrich_report(report, OpenAIEnricher())
        else:
            if not os.environ.get("ANTHROPIC_API_KEY"):
                raise ValueError(
                    "enrich_provider='anthropic' requires ANTHROPIC_API_KEY "
                    "to be set in the server environment."
                )
            from reposage.enrichment.anthropic_provider import AnthropicEnricher

            enrichment = enrich_report(report, AnthropicEnricher())

    return render_markdown_report(report, enrichment=enrichment)


async def _health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})
