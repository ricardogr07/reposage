"""Tests for M13 C# language support."""

from __future__ import annotations

from pathlib import Path

from reposage.pipeline import build_audit_report
from reposage.scan._dep_parsers_dotnet import (
    _parse_csproj,
    _parse_directory_packages_props,
    _parse_packages_config,
)
from reposage.scan.dependencies import _is_supported_manifest
from tests.conftest import fixture_path

# --- .csproj parser ---


def test_csproj_runtime_deps() -> None:
    deps = _parse_csproj(
        fixture_path("csharp_repo") / "src" / "MyApp" / "MyApp.csproj",
        "src/MyApp/MyApp.csproj",
    )
    names = {d.name for d in deps}
    assert "Microsoft.AspNetCore.OpenApi" in names
    assert "Microsoft.EntityFrameworkCore" in names
    assert "Dapper" in names
    for d in deps:
        assert d.group == "runtime"


def test_csproj_ecosystem() -> None:
    deps = _parse_csproj(
        fixture_path("csharp_repo") / "src" / "MyApp" / "MyApp.csproj",
        "src/MyApp/MyApp.csproj",
    )
    assert deps
    assert all(d.ecosystem == "nuget" for d in deps)


def test_csproj_version() -> None:
    deps = _parse_csproj(
        fixture_path("csharp_repo") / "src" / "MyApp" / "MyApp.csproj",
        "src/MyApp/MyApp.csproj",
    )
    by_name = {d.name: d for d in deps}
    assert by_name["Microsoft.EntityFrameworkCore"].version_spec == "8.0.0"
    assert by_name["Dapper"].version_spec == "2.1.28"


def test_packages_config_parsing(tmp_path: Path) -> None:
    (tmp_path / "packages.config").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<packages>\n"
        '  <package id="Newtonsoft.Json" version="13.0.3" targetFramework="net48" />\n'
        '  <package id="log4net" version="2.0.15" targetFramework="net48" />\n'
        "</packages>\n",
        encoding="utf-8",
    )
    deps = _parse_packages_config(tmp_path / "packages.config", "packages.config")
    names = {d.name for d in deps}
    assert "Newtonsoft.Json" in names
    assert "log4net" in names
    assert all(d.ecosystem == "nuget" for d in deps)
    assert all(d.group == "runtime" for d in deps)


# --- manifest detection ---


def test_csproj_manifest_detected() -> None:
    assert _is_supported_manifest("MyApp.csproj") is True
    assert _is_supported_manifest("MyApp.Tests.csproj") is True
    assert _is_supported_manifest("packages.config") is True
    assert _is_supported_manifest("Directory.Packages.props") is True


# --- pipeline integration ---


def test_csharp_language_detected() -> None:
    report = build_audit_report(fixture_path("csharp_repo"))
    language_names = [ls.language for ls in report.inventory.languages]
    assert "C#" in language_names


def test_csharp_framework_detection() -> None:
    report = build_audit_report(fixture_path("csharp_repo"))
    frameworks = report.inventory.frameworks
    assert "ASP.NET Core" in frameworks
    assert "Entity Framework Core" in frameworks
    assert "Dapper" in frameworks


def test_csharp_test_detection() -> None:
    report = build_audit_report(fixture_path("csharp_repo"))
    assert report.quality.has_tests is True


def test_csharp_typing_present() -> None:
    report = build_audit_report(fixture_path("csharp_repo"))
    assert report.quality.typing_present is True


def test_csproj_invalid_xml(tmp_path: Path) -> None:
    (tmp_path / "bad.csproj").write_text("<Project><Broken", encoding="utf-8")
    result = _parse_csproj(tmp_path / "bad.csproj", "bad.csproj")
    assert result == []


def test_directory_packages_props(tmp_path: Path) -> None:
    (tmp_path / "Directory.Packages.props").write_text(
        "<Project>\n"
        "  <ItemGroup>\n"
        '    <PackageVersion Include="Serilog" Version="3.1.1" />\n'
        '    <PackageVersion Include="AutoMapper" Version="12.0.1" />\n'
        "  </ItemGroup>\n"
        "</Project>\n",
        encoding="utf-8",
    )
    deps = _parse_directory_packages_props(
        tmp_path / "Directory.Packages.props", "Directory.Packages.props"
    )
    names = {d.name for d in deps}
    assert "Serilog" in names
    assert "AutoMapper" in names
    assert all(d.ecosystem == "nuget" for d in deps)
    assert all(d.group == "runtime" for d in deps)
