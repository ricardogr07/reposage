"""Dependency manifest parsing for RepoSage."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from reposage.models import Dependency, DependencySummary, FileRecord
from reposage.scan._dep_parsers import (
    _parse_build_gradle,
    _parse_package_json,
    _parse_pom_xml,
    _parse_pyproject,
    _parse_requirements,
)

_PYPROJECT = "pyproject.toml"
_PACKAGE_JSON = "package.json"
_REQUIREMENTS_PREFIX = "requirements"
_JAVA_MANIFESTS = {"pom.xml", "build.gradle", "build.gradle.kts"}


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
        elif file_name == "pom.xml":
            parsed_dependencies = _parse_pom_xml(absolute_path, manifest_path)
        elif file_name in {"build.gradle", "build.gradle.kts"}:
            parsed_dependencies = _parse_build_gradle(absolute_path, manifest_path)
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
    return (
        file_name in (_PYPROJECT, _PACKAGE_JSON)
        or file_name.startswith(_REQUIREMENTS_PREFIX)
        or file_name in _JAVA_MANIFESTS
    )
