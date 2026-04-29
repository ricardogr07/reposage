"""Dependency parsers for .NET / NuGet manifest formats."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from reposage.models import Dependency

_MSBUILD_NS = "{http://schemas.microsoft.com/developer/msbuild/2003}"


def _strip_ns(tag: str) -> str:
    return tag.replace(_MSBUILD_NS, "")


def _parse_csproj(path: Path, relative_path: str) -> list[Dependency]:
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError):
        return []

    dependencies: list[Dependency] = []
    for elem in tree.iter():
        if _strip_ns(elem.tag) != "PackageReference":
            continue
        name = elem.get("Include") or elem.get("include")
        if not name:
            continue
        version = elem.get("Version") or elem.get("version") or "*"
        condition = elem.get("Condition", "")
        group = "test" if "test" in condition.lower() else "runtime"
        dependencies.append(
            Dependency(
                name=name,
                version_spec=version,
                ecosystem="nuget",
                source_file=relative_path,
                group=group,
            )
        )
    return dependencies


def _parse_packages_config(path: Path, relative_path: str) -> list[Dependency]:
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError):
        return []

    dependencies: list[Dependency] = []
    for elem in tree.iter():
        if _strip_ns(elem.tag) != "package":
            continue
        name = elem.get("id")
        if not name:
            continue
        version = elem.get("version") or "*"
        dependencies.append(
            Dependency(
                name=name,
                version_spec=version,
                ecosystem="nuget",
                source_file=relative_path,
                group="runtime",
            )
        )
    return dependencies


def _parse_directory_packages_props(path: Path, relative_path: str) -> list[Dependency]:
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError):
        return []

    dependencies: list[Dependency] = []
    for elem in tree.iter():
        if _strip_ns(elem.tag) != "PackageVersion":
            continue
        name = elem.get("Include") or elem.get("include")
        if not name:
            continue
        version = elem.get("Version") or elem.get("version") or "*"
        dependencies.append(
            Dependency(
                name=name,
                version_spec=version,
                ecosystem="nuget",
                source_file=relative_path,
                group="runtime",
            )
        )
    return dependencies
