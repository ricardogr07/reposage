"""Subprocess helper and run-or-load utility for security tool integrations."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run_tool(cmd: list[str], timeout: int = 30) -> str | None:
    """Run cmd and return stdout. Returns None if tool missing or times out.

    Non-zero exit is NOT treated as failure — many security tools exit 1
    when they find issues, which is the normal case.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return None


def run_or_load(cmd: list[str], fallback: Path, timeout: int = 30) -> str | None:
    """Try subprocess first; fall back to reading fallback file if present."""
    raw = run_tool(cmd, timeout=timeout)
    if raw is not None:
        return raw
    if fallback.exists():
        return fallback.read_text(encoding="utf-8")
    return None
