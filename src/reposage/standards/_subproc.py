"""Subprocess helper with a hard timeout, generalized from api/_git_history.py."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run(
    cmd: list[str],
    cwd: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str] | None:
    """Run ``cmd`` in ``cwd`` and return the completed process.

    Returns ``None`` when the command times out, is missing, or the OS refuses
    to start it. ``check`` is not set, so a non-zero exit is returned to the
    caller for inspection rather than raising.
    """

    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None
