"""Dependency parsing tests."""

from __future__ import annotations

from pathlib import Path

from reposage.models import FileRecord
from reposage.pipeline import build_audit_report
from reposage.scan.dependencies import (
    _dependencies_from_mapping,
    _dependencies_from_strings,
    _parse_dependency_string,
    _parse_package_json,
    _parse_pyproject,
    _parse_requirements,
    summarize_dependencies,
)
from tests.conftest import fixture_path


def test_dependency_summary_covers_python_and_npm_manifests() -> None:
    report = build_audit_report(fixture_path("mixed_repo"))
    dependency_names = {dependency.name for dependency in report.dependencies.dependencies}

    assert report.dependencies.ecosystems == ["npm", "python"]
    assert "fastapi" in dependency_names
    assert "react" in dependency_names
    assert "mypy" in dependency_names


def test_framework_detection_uses_dependency_signals() -> None:
    report = build_audit_report(fixture_path("js_repo"))

    assert "Next.js" in report.inventory.frameworks
    assert "React" in report.inventory.frameworks


def test_parse_requirements_skips_urls_vcs_and_options(tmp_path: Path) -> None:
    requirements_path = tmp_path / "requirements.txt"
    requirements_path.write_text(
        "\n".join(
            [
                "requests==2.31.0",
                "flask>=3.0",
                "https://github.com/some/repo/archive/main.zip",
                "git+https://github.com/org/pkg.git@main#egg=pkg",
                "-e .",
                "--hash=sha256:abc123def456",
                "# just a comment",
                "-r other-requirements.txt",
            ]
        ),
        encoding="utf-8",
    )

    dependencies = _parse_requirements(requirements_path, "requirements.txt")

    assert len(dependencies) == 2
    assert {dependency.name for dependency in dependencies} == {"requests", "flask"}


def test_summarize_dependencies_dispatches_requirements_manifests(tmp_path: Path) -> None:
    requirements_path = tmp_path / "requirements-dev.txt"
    requirements_path.write_text("urllib3>=2.0\n", encoding="utf-8")

    summary = summarize_dependencies(
        tmp_path,
        [
            FileRecord(
                path="requirements-dev.txt",
                extension=".txt",
                size_bytes=requirements_path.stat().st_size,
                line_count=1,
            )
        ],
    )

    assert summary.manifests == ["requirements-dev.txt"]
    assert summary.ecosystems == ["python"]
    assert [(dependency.name, dependency.version_spec) for dependency in summary.dependencies] == [
        ("urllib3", ">=2.0")
    ]


def test_parse_pyproject_returns_empty_on_invalid_toml(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text("[project\nname = 'broken'\n", encoding="utf-8")

    dependencies = _parse_pyproject(pyproject_path, "pyproject.toml")

    assert dependencies == []


def test_parse_pyproject_collects_optional_and_poetry_group_dependencies(
    tmp_path: Path,
) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        "\n".join(
            [
                "[project]",
                'dependencies = ["requests>=2.0"]',
                "",
                "[project.optional-dependencies]",
                'dev = ["pytest>=8.0"]',
                'docs = ["mkdocs"]',
                "",
                "[tool.poetry.group.lint.dependencies]",
                'ruff = "^0.5"',
                'mypy = { version = "^1.10" }',
            ]
        ),
        encoding="utf-8",
    )

    dependencies = _parse_pyproject(pyproject_path, "pyproject.toml")
    parsed = {
        (dependency.name, dependency.version_spec, dependency.group) for dependency in dependencies
    }

    assert ("requests", ">=2.0", "runtime") in parsed
    assert ("pytest", ">=8.0", "dev") in parsed
    assert ("mkdocs", "*", "docs") in parsed
    assert ("ruff", "^0.5", "lint") in parsed
    assert ("mypy", "^1.10", "lint") in parsed


def test_parse_requirements_returns_empty_for_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing-requirements.txt"
    dependencies = _parse_requirements(missing, "missing-requirements.txt")

    assert dependencies == []


def test_parse_package_json_returns_empty_on_invalid_json(tmp_path: Path) -> None:
    package_json_path = tmp_path / "package.json"
    package_json_path.write_text("{broken", encoding="utf-8")

    dependencies = _parse_package_json(package_json_path, "package.json")

    assert dependencies == []


def test_dependencies_from_strings_handles_non_list_and_non_string_values() -> None:
    assert (
        _dependencies_from_strings(
            "requests>=2.0",
            ecosystem="python",
            source_file="pyproject.toml",
            group="runtime",
        )
        == []
    )

    dependencies = _dependencies_from_strings(
        ["requests>=2.0", 123, None],
        ecosystem="python",
        source_file="pyproject.toml",
        group="runtime",
    )

    assert [(dependency.name, dependency.version_spec) for dependency in dependencies] == [
        ("requests", ">=2.0")
    ]


def test_dependencies_from_mapping_handles_ignore_and_version_shapes() -> None:
    assert (
        _dependencies_from_mapping(
            ["not", "a", "mapping"],
            ecosystem="python",
            source_file="pyproject.toml",
            group="runtime",
            ignore=set(),
        )
        == []
    )

    dependencies = _dependencies_from_mapping(
        {
            "python": ">=3.12",
            "requests": {"version": ">=2.31"},
            "local-package": object(),
        },
        ecosystem="python",
        source_file="pyproject.toml",
        group="runtime",
        ignore={"python"},
    )

    assert [(dependency.name, dependency.version_spec) for dependency in dependencies] == [
        ("requests", ">=2.31"),
        ("local-package", "*"),
    ]


def test_parse_dependency_string_handles_url_and_invalid_values() -> None:
    dependency = _parse_dependency_string(
        "demo-package @ https://example.com/demo-package.whl",
        ecosystem="python",
        source_file="requirements.txt",
        group="requirements",
    )

    assert dependency is not None
    assert dependency.name == "demo-package"
    assert dependency.version_spec == "@ https://example.com/demo-package.whl"
    assert (
        _parse_dependency_string(
            "!!!",
            ecosystem="python",
            source_file="requirements.txt",
            group="requirements",
        )
        is None
    )
