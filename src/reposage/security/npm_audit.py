"""npm audit integration for JavaScript vulnerability scanning."""

from __future__ import annotations

import json
from pathlib import Path

from reposage.models import VulnerabilityFinding
from reposage.security._runner import run_or_load


def scan_npm_audit(root: Path) -> tuple[list[VulnerabilityFinding], str]:
    """Run npm audit or parse fallback report. Returns (findings, skip_reason)."""
    cmd = ["npm", "audit", "--json"]
    fallback = root / "npm-audit.json"
    raw = run_or_load(cmd, fallback, timeout=60)
    if raw is None:
        return [], "not installed and no npm-audit.json found"

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [], f"parse error: {exc}"

    vulns_dict = data.get("vulnerabilities", {})
    if not isinstance(vulns_dict, dict):
        return [], "unexpected format: vulnerabilities is not a dict"

    findings: list[VulnerabilityFinding] = []
    for name, vuln in vulns_dict.items():
        severity = vuln.get("severity", "unknown")
        version_range = vuln.get("range", "")

        cve = ""
        for via_entry in vuln.get("via", []):
            if isinstance(via_entry, dict):
                source = via_entry.get("source")
                if source:
                    cve = str(source)
                    break

        fix_info = vuln.get("fixAvailable")
        fix_version = fix_info.get("version", "") if isinstance(fix_info, dict) else ""

        findings.append(
            VulnerabilityFinding(
                package=name,
                ecosystem="npm",
                severity=severity,
                cve=cve,
                affected_version=version_range,
                fix_version=fix_version,
            )
        )
    return findings, ""
