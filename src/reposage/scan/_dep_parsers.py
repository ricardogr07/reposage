"""Format-specific dependency parsers for pyproject.toml, requirements, package.json, pom.xml, and Gradle."""  # noqa: E501

from __future__ import annotations

import json
import re
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

from reposage.models import Dependency

PACKAGE_NAME_PATTERN = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*(.*)$")


def _parse_pyproject(path: Path, relative_path: str) -> list[Dependency]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return []

    dependencies: list[Dependency] = []
    project = data.get("project", {})
    dependencies.extend(
        _dependencies_from_strings(
            project.get("dependencies", []),
            ecosystem="python",
            source_file=relative_path,
            group="runtime",
        )
    )

    optional_dependencies = project.get("optional-dependencies", {})
    for group_name, values in optional_dependencies.items():
        dependencies.extend(
            _dependencies_from_strings(
                values,
                ecosystem="python",
                source_file=relative_path,
                group=group_name,
            )
        )

    dependency_groups = data.get("dependency-groups", {})
    for group_name, values in dependency_groups.items():
        dependencies.extend(
            _dependencies_from_strings(
                values,
                ecosystem="python",
                source_file=relative_path,
                group=group_name,
            )
        )

    poetry = data.get("tool", {}).get("poetry", {})
    poetry_dependencies = poetry.get("dependencies", {})
    dependencies.extend(
        _dependencies_from_mapping(
            poetry_dependencies,
            ecosystem="python",
            source_file=relative_path,
            group="runtime",
            ignore={"python"},
        )
    )

    poetry_groups = poetry.get("group", {})
    for group_name, group_body in poetry_groups.items():
        group_dependencies = group_body.get("dependencies", {})
        dependencies.extend(
            _dependencies_from_mapping(
                group_dependencies,
                ecosystem="python",
                source_file=relative_path,
                group=group_name,
                ignore=set(),
            )
        )

    return dependencies


def _parse_requirements(path: Path, relative_path: str) -> list[Dependency]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    dependencies: list[Dependency] = []
    for raw_line in lines:
        line = raw_line.strip()
        if (
            not line
            or line.startswith("#")
            or line.startswith(("-", "http://", "https://", "git+"))
        ):
            continue
        dependency = _parse_dependency_string(
            line,
            ecosystem="python",
            source_file=relative_path,
            group="requirements",
        )
        if dependency is not None:
            dependencies.append(dependency)
    return dependencies


def _parse_package_json(path: Path, relative_path: str) -> list[Dependency]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    dependencies: list[Dependency] = []
    for group_name in (
        "dependencies",
        "devDependencies",
        "peerDependencies",
        "optionalDependencies",
    ):
        dependencies.extend(
            _dependencies_from_mapping(
                data.get(group_name, {}),
                ecosystem="npm",
                source_file=relative_path,
                group=group_name,
                ignore=set(),
            )
        )
    return dependencies


def _dependencies_from_strings(
    values: object,
    *,
    ecosystem: str,
    source_file: str,
    group: str,
) -> list[Dependency]:
    if not isinstance(values, list):
        return []

    dependencies: list[Dependency] = []
    for value in values:
        if not isinstance(value, str):
            continue
        dependency = _parse_dependency_string(
            value,
            ecosystem=ecosystem,
            source_file=source_file,
            group=group,
        )
        if dependency is not None:
            dependencies.append(dependency)
    return dependencies


def _dependencies_from_mapping(
    values: object,
    *,
    ecosystem: str,
    source_file: str,
    group: str,
    ignore: set[str],
) -> list[Dependency]:
    if not isinstance(values, dict):
        return []

    dependencies: list[Dependency] = []
    for name, value in values.items():
        if not isinstance(name, str) or name in ignore:
            continue
        if isinstance(value, str):
            version_spec = value
        elif isinstance(value, dict):
            version_spec = str(value.get("version", ""))
        else:
            version_spec = ""
        dependencies.append(
            Dependency(
                name=name,
                version_spec=version_spec or "*",
                ecosystem=ecosystem,
                source_file=source_file,
                group=group,
            )
        )
    return dependencies


_MAVEN_NS = "{http://maven.apache.org/POM/4.0.0}"
_SCOPE_TO_GROUP: dict[str, str] = {"test": "test", "provided": "provided"}

_GRADLE_DEP_RE = re.compile(
    r"""^\s*(\w+)\s*(?:\(|'|")([A-Za-z][\w.\-]*):([A-Za-z][\w.\-]*):([^\s'")\n]+)""",
    re.MULTILINE,
)
_GRADLE_GROUPS: dict[str, str] = {
    "implementation": "runtime",
    "api": "runtime",
    "runtimeOnly": "runtime",
    "testImplementation": "test",
    "testRuntimeOnly": "test",
    "testCompileOnly": "test",
    "compileOnly": "provided",
    "provided": "provided",
}


def _parse_pom_xml(path: Path, relative_path: str) -> list[Dependency]:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        return []

    deps_el = root.find(f"{_MAVEN_NS}dependencies")
    if deps_el is None:
        return []

    dependencies: list[Dependency] = []
    for dep in deps_el.findall(f"{_MAVEN_NS}dependency"):
        gid_el = dep.find(f"{_MAVEN_NS}groupId")
        aid_el = dep.find(f"{_MAVEN_NS}artifactId")
        if gid_el is None or aid_el is None:
            continue
        group_id = (gid_el.text or "").strip()
        artifact_id = (aid_el.text or "").strip()
        if not group_id or not artifact_id:
            continue

        ver_el = dep.find(f"{_MAVEN_NS}version")
        version = (ver_el.text or "").strip() if ver_el is not None else ""

        scope_el = dep.find(f"{_MAVEN_NS}scope")
        scope = (scope_el.text or "").strip().lower() if scope_el is not None else ""

        dependencies.append(
            Dependency(
                name=f"{group_id}:{artifact_id}".lower(),
                version_spec=version or "*",
                ecosystem="maven",
                source_file=relative_path,
                group=_SCOPE_TO_GROUP.get(scope, "runtime"),
            )
        )
    return dependencies


def _parse_build_gradle(path: Path, relative_path: str) -> list[Dependency]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    dependencies: list[Dependency] = []
    for m in _GRADLE_DEP_RE.finditer(text):
        config, group_id, artifact_id, version = m.group(1), m.group(2), m.group(3), m.group(4)
        dependencies.append(
            Dependency(
                name=f"{group_id}:{artifact_id}".lower(),
                version_spec=version.strip() or "*",
                ecosystem="maven",
                source_file=relative_path,
                group=_GRADLE_GROUPS.get(config, "runtime"),
            )
        )
    return dependencies


def _parse_dependency_string(
    value: str,
    *,
    ecosystem: str,
    source_file: str,
    group: str,
) -> Dependency | None:
    if " @ " in value:
        name, version_spec = value.split(" @ ", maxsplit=1)
        return Dependency(
            name=name.strip(),
            version_spec=f"@ {version_spec.strip()}",
            ecosystem=ecosystem,
            source_file=source_file,
            group=group,
        )

    match = PACKAGE_NAME_PATTERN.match(value)
    if match is None:
        return None

    name = match.group(1)
    version_spec = match.group(2).strip() or "*"
    return Dependency(
        name=name,
        version_spec=version_spec,
        ecosystem=ecosystem,
        source_file=source_file,
        group=group,
    )
