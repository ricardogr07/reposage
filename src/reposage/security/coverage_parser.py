"""Coverage report parsing from coverage.xml and lcov.info."""

from __future__ import annotations

import contextlib
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_coverage(root: Path) -> tuple[float | None, str]:
    """Parse coverage from coverage.xml or lcov.info. Returns (percent, source_name).

    Returns (None, "") if no supported coverage file is found.
    First match wins: coverage.xml is checked before lcov.info.
    """
    coverage_xml = root / "coverage.xml"
    if coverage_xml.exists():
        result = _parse_cobertura(coverage_xml)
        if result is not None:
            return result, "coverage.xml"

    lcov_info = root / "lcov.info"
    if lcov_info.exists():
        result = _parse_lcov(lcov_info)
        if result is not None:
            return result, "lcov.info"

    return None, ""


def _parse_cobertura(path: Path) -> float | None:
    """Parse Cobertura XML; return line coverage percent or None on error."""
    try:
        tree = ET.parse(path)
        root_elem = tree.getroot()
        line_rate = root_elem.get("line-rate")
        if line_rate is None:
            return None
        return float(line_rate) * 100
    except (ET.ParseError, ValueError, OSError):
        return None


def _parse_lcov(path: Path) -> float | None:
    """Parse LCOV text format; return line coverage percent or None on error."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    lines_hit = 0
    lines_found = 0
    for line in text.splitlines():
        if line.startswith("LH:"):
            with contextlib.suppress(ValueError):
                lines_hit += int(line[3:])
        elif line.startswith("LF:"):
            with contextlib.suppress(ValueError):
                lines_found += int(line[3:])

    if lines_found == 0:
        return None
    return (lines_hit / lines_found) * 100
