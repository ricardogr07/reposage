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
    _resolve_token,
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


# ---------------------------------------------------------------------------
# Unit: URL validation — embedded credentials
# ---------------------------------------------------------------------------


def test_validate_url_rejects_embedded_token() -> None:
    with pytest.raises(ValueError, match="Credentials must not be embedded"):
        _validate_repo_url("https://mytoken@github.com/org/repo")


def test_validate_url_rejects_user_and_password() -> None:
    with pytest.raises(ValueError, match="Credentials must not be embedded"):
        _validate_repo_url("https://user:example-password@github.com/org/repo")


# ---------------------------------------------------------------------------
# Unit: _resolve_token precedence
# ---------------------------------------------------------------------------


def test_resolve_token_returns_param_when_given() -> None:
    assert _resolve_token("p") == "p"


def test_resolve_token_falls_back_to_env_var() -> None:
    with patch.dict("os.environ", {"GITHUB_TOKEN": "e"}):
        assert _resolve_token(None) == "e"


def test_resolve_token_param_beats_env_var() -> None:
    with patch.dict("os.environ", {"GITHUB_TOKEN": "e"}):
        assert _resolve_token("p") == "p"


def test_resolve_token_none_when_both_absent() -> None:
    clean_env = {k: v for k, v in os.environ.items() if k != "GITHUB_TOKEN"}
    with patch.dict("os.environ", clean_env, clear=True):
        assert _resolve_token(None) is None


# ---------------------------------------------------------------------------
# Unit: _clone token handling (mocked subprocess)
# ---------------------------------------------------------------------------


def test_clone_token_passed_as_auth_header_not_in_url(tmp_path: Path) -> None:
    import base64

    dest = str(tmp_path / "repo")
    with patch("reposage.server.app.subprocess.run") as mock_run:
        mock_run.return_value = None
        _clone("https://github.com/example/private", "main", dest, token="ghp_test123")

    first_call_args = mock_run.call_args_list[0][0][0]
    assert isinstance(first_call_args, list)
    assert "-c" in first_call_args
    expected_b64 = base64.b64encode(b"x-access-token:ghp_test123").decode()
    assert any(expected_b64 in v for v in first_call_args if isinstance(v, str))
    # Token must not appear in the URL position
    url_idx = first_call_args.index("https://github.com/example/private")
    assert "ghp_test123" not in first_call_args[url_idx]


def test_clone_without_token_excludes_auth_header(tmp_path: Path) -> None:
    dest = str(tmp_path / "repo")
    with patch("reposage.server.app.subprocess.run") as mock_run:
        mock_run.return_value = None
        _clone("https://github.com/example/repo", "main", dest)

    first_call_args = mock_run.call_args_list[0][0][0]
    assert "-c" not in first_call_args
    assert not any("http.extraheader" in v for v in first_call_args if isinstance(v, str))


def test_clone_param_token_beats_env_var(tmp_path: Path) -> None:
    import base64

    dest = str(tmp_path / "repo")
    with (
        patch("reposage.server.app.subprocess.run") as mock_run,
        patch.dict("os.environ", {"GITHUB_TOKEN": "example-env-token"}),
    ):
        mock_run.return_value = None
        _clone("https://github.com/example/private", "main", dest, token="example-param-token")

    first_call_args = mock_run.call_args_list[0][0][0]
    param_b64 = base64.b64encode(b"x-access-token:example-param-token").decode()
    env_b64 = base64.b64encode(b"x-access-token:example-env-token").decode()
    assert any(param_b64 in v for v in first_call_args if isinstance(v, str))
    assert not any(env_b64 in v for v in first_call_args if isinstance(v, str))
