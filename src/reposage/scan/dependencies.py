"""Dependency manifest parsing for RepoSage."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path, PurePosixPath

from reposage.models import Dependency, DependencySummary, FileRecord

PACKAGE_NAME_PATTERN = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*(.*)$")

_PYPROJECT = "pyproject.toml"
_PACKAGE_JSON = "package.json"
_REQUIREMENTS_PREFIX = "requirements"


def summarize_dependencies(root: Path, file_records: list[FileRecord]) -> DependencySummary:
    """Parse supported manifests and summarize declared dependencies."""

    manifest_paths = sorted(
        {
            file_record.path
            for file_record in file_records
            if _is_supported_manifest(PurePosixPath(file_record.path).name)
        }
    )

    dependencies: list[Dependency] = []
    ecosystems: set[str] = set()

    for manifest_path in manifest_paths:
        absolute_path = root / manifest_path
        file_name = PurePosixPath(manifest_path).name
        if file_name == _PYPROJECT:
            parsed_dependencies = _parse_pyproject(absolute_path, manifest_path)
        elif file_name == _PACKAGE_JSON:
            parsed_dependencies = _parse_package_json(absolute_path, manifest_path)
        else:
            parsed_dependencies = _parse_requirements(absolute_path, manifest_path)

        dependencies.extend(parsed_dependencies)
        ecosystems.update(dependency.ecosystem for dependency in parsed_dependencies)

    unique_dependencies = sorted(
        {
            (
                dependency.name,
                dependency.version_spec,
                dependency.ecosystem,
                dependency.source_file,
                dependency.group,
            )
            for dependency in dependencies
        }
    )

    normalized_dependencies = [
        Dependency(
            name=name,
            version_spec=version_spec,
            ecosystem=ecosystem,
            source_file=source_file,
            group=group,
        )
        for name, version_spec, ecosystem, source_file, group in unique_dependencies
    ]

    counts_by_ecosystem: dict[str, int] = {}
    for ecosystem in ecosystems:
        counts_by_ecosystem[ecosystem] = sum(
            1 for dependency in normalized_dependencies if dependency.ecosystem == ecosystem
        )

    return DependencySummary(
        ecosystems=sorted(ecosystems),
        manifests=manifest_paths,
        dependencies=normalized_dependencies,
        counts_by_ecosystem=counts_by_ecosystem,
    )


def _is_supported_manifest(file_name: str) -> bool:
    return file_name in (_PYPROJECT, _PACKAGE_JSON) or file_name.startswith(_REQUIREMENTS_PREFIX)


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
