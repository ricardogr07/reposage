"""pip-audit integration for Python vulnerability scanning."""

from __future__ import annotations

import json
from pathlib import Path

from reposage.models import VulnerabilityFinding
from reposage.security._runner import run_or_load


def scan_pip_audit(root: Path) -> tuple[list[VulnerabilityFinding], str]:
    """Run pip-audit or parse fallback report. Returns (findings, skip_reason).

    skip_reason is "" on success, or a message if the tool was skipped.
    """
    manifest = root / "pyproject.toml"
    if not manifest.exists():
        manifest = root / "requirements.txt"

    cmd = ["pip-audit", "--format", "json"]
    if manifest.exists() and manifest.name != "pyproject.toml":
        cmd += ["-r", str(manifest)]

    fallback = root / "pip-audit-report.json"
    raw = run_or_load(cmd, fallback)
    if raw is None:
        return [], "not installed and no pip-audit-report.json found"

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [], f"parse error: {exc}"

    findings: list[VulnerabilityFinding] = []
    for dep in data.get("dependencies", []):
        name = dep.get("name", "")
        version = dep.get("version", "")
        for vuln in dep.get("vulns", []):
            fix_versions = vuln.get("fix_versions", [])
            findings.append(
                VulnerabilityFinding(
                    package=name,
                    ecosystem="python",
                    severity="unknown",
                    cve=vuln.get("id", ""),
                    affected_version=version,
                    fix_version=fix_versions[0] if fix_versions else "",
                )
            )
    return findings, ""
