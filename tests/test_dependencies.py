"""Dependency parsing tests."""

from __future__ import annotations

from pathlib import Path

from reposage.pipeline import build_audit_report
from reposage.scan.dependencies import _parse_requirements
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
