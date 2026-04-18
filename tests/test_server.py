"""Tests for the RepoSage MCP server (requires reposage[server] installed)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("mcp", reason="reposage[server] not installed")

from starlette.testclient import TestClient  # noqa: E402

from reposage.server.app import (  # noqa: E402
    _audit,
    _clone,
    _validate_repo_url,
    create_mcp_app,
)

# The MCP SDK's transport_security middleware validates Host headers against
# DNS-rebinding attacks and rejects test hostnames for /mcp requests.
# Tool logic is therefore tested via direct calls to module-level helpers;
# HTTP tests are limited to the health endpoint and /mcp endpoint registration.


# ---------------------------------------------------------------------------
# HTTP: health endpoint
# ---------------------------------------------------------------------------


def test_health_returns_200() -> None:
    with TestClient(create_mcp_app(), base_url="http://localhost") as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# HTTP: /mcp endpoint exists (not 404)
# ---------------------------------------------------------------------------


def test_mcp_endpoint_registered() -> None:
    with TestClient(create_mcp_app(), base_url="http://localhost") as client:
        response = client.post("/mcp", content=b"")
    assert response.status_code != 404


# ---------------------------------------------------------------------------
# Unit: URL validation
# ---------------------------------------------------------------------------


def test_validate_url_accepts_https() -> None:
    _validate_repo_url("https://github.com/org/repo")  # must not raise


def test_validate_url_rejects_ssh() -> None:
    with pytest.raises(ValueError, match="https://"):
        _validate_repo_url("git@github.com:org/repo.git")


def test_validate_url_rejects_file() -> None:
    with pytest.raises(ValueError, match="https://"):
        _validate_repo_url("file:///etc/passwd")


def test_validate_url_rejects_http() -> None:
    with pytest.raises(ValueError, match="https://"):
        _validate_repo_url("http://github.com/org/repo")


# ---------------------------------------------------------------------------
# Unit: _audit helper
# ---------------------------------------------------------------------------


def test_audit_returns_markdown(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "fake"\n')
    result = _audit(tmp_path, enrich=False)
    assert "# RepoSage Audit" in result


def test_audit_enrich_without_key_raises(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "fake"\n')
    clean_env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    with (
        patch.dict("os.environ", clean_env, clear=True),
        pytest.raises(ValueError, match="ANTHROPIC_API_KEY"),
    ):
        _audit(tmp_path, enrich=True)


# ---------------------------------------------------------------------------
# Unit: _clone argument safety (mocked subprocess)
# ---------------------------------------------------------------------------


def test_clone_uses_list_args_not_shell(tmp_path: Path) -> None:
    dest = str(tmp_path / "repo")
    with patch("reposage.server.app.subprocess.run") as mock_run:
        mock_run.return_value = None
        _clone("https://github.com/example/repo", "main", dest)

    first_call_args = mock_run.call_args_list[0][0][0]
    # Must be a list, not a shell string — prevents argument injection
    assert isinstance(first_call_args, list)
    assert "https://github.com/example/repo" in first_call_args
    assert dest in first_call_args
