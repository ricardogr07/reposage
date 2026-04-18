"""RepoSage MCP server (optional [server] extra)."""

from __future__ import annotations

__all__ = ["create_mcp_app"]


def create_mcp_app():  # type: ignore[return]
    """Return the Starlette app for the RepoSage MCP server.

    Import is deferred so the base package stays importable without mcp/uvicorn.
    """
    from reposage.server.app import create_mcp_app as _create

    return _create()
