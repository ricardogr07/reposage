"""Tests for M10 Java language support."""

from __future__ import annotations

from pathlib import Path

from reposage.pipeline import build_audit_report
from reposage.scan._dep_parsers import _parse_build_gradle, _parse_pom_xml
from tests.conftest import fixture_path

# --- pom.xml parser ---


def test_parse_pom_xml_fixture() -> None:
    deps = _parse_pom_xml(fixture_path("java_maven_repo") / "pom.xml", "pom.xml")
    assert len(deps) >= 2
    names = {d.name for d in deps}
    assert "org.springframework.boot:spring-boot-starter-web" in names
    assert "junit:junit" in names
    spring_dep = next(
        d for d in deps if d.name == "org.springframework.boot:spring-boot-starter-web"
    )
    assert spring_dep.group == "runtime"
    assert spring_dep.ecosystem == "maven"
    junit_dep = next(d for d in deps if d.name == "junit:junit")
    assert junit_dep.group == "test"
    assert junit_dep.ecosystem == "maven"


def test_parse_pom_xml_missing_file(tmp_path: Path) -> None:
    result = _parse_pom_xml(tmp_path / "pom.xml", "pom.xml")
    assert result == []


def test_parse_pom_xml_invalid_xml(tmp_path: Path) -> None:
    (tmp_path / "pom.xml").write_text("not xml", encoding="utf-8")
    result = _parse_pom_xml(tmp_path / "pom.xml", "pom.xml")
    assert result == []


def test_parse_pom_xml_namespace_handling(tmp_path: Path) -> None:
    (tmp_path / "pom.xml").write_text(
        '<?xml version="1.0"?>'
        '<project xmlns="http://maven.apache.org/POM/4.0.0">'
        "<dependencies>"
        "<dependency>"
        "<groupId>com.example</groupId>"
        "<artifactId>mylib</artifactId>"
        "<version>1.0</version>"
        "</dependency>"
        "</dependencies>"
        "</project>",
        encoding="utf-8",
    )
    deps = _parse_pom_xml(tmp_path / "pom.xml", "pom.xml")
    assert len(deps) == 1
    assert deps[0].name == "com.example:mylib"
    assert deps[0].ecosystem == "maven"
    assert deps[0].version_spec == "1.0"


def test_parse_pom_xml_skips_dependency_management(tmp_path: Path) -> None:
    (tmp_path / "pom.xml").write_text(
        '<?xml version="1.0"?>'
        '<project xmlns="http://maven.apache.org/POM/4.0.0">'
        "<dependencyManagement>"
        "<dependencies>"
        "<dependency>"
        "<groupId>org.example</groupId>"
        "<artifactId>managed-only</artifactId>"
        "<version>2.0</version>"
        "</dependency>"
        "</dependencies>"
        "</dependencyManagement>"
        "<dependencies>"
        "<dependency>"
        "<groupId>org.example</groupId>"
        "<artifactId>direct</artifactId>"
        "<version>1.0</version>"
        "</dependency>"
        "</dependencies>"
        "</project>",
        encoding="utf-8",
    )
    deps = _parse_pom_xml(tmp_path / "pom.xml", "pom.xml")
    names = {d.name for d in deps}
    assert "org.example:direct" in names
    assert "org.example:managed-only" not in names


# --- build.gradle parser ---


def test_parse_build_gradle_fixture() -> None:
    deps = _parse_build_gradle(fixture_path("java_gradle_repo") / "build.gradle", "build.gradle")
    assert len(deps) >= 2
    names = {d.name for d in deps}
    assert "io.quarkus:quarkus-resteasy" in names
    assert "io.quarkus:quarkus-junit5" in names
    resteasy = next(d for d in deps if d.name == "io.quarkus:quarkus-resteasy")
    assert resteasy.group == "runtime"
    assert resteasy.ecosystem == "maven"
    junit5 = next(d for d in deps if d.name == "io.quarkus:quarkus-junit5")
    assert junit5.group == "test"
    assert junit5.ecosystem == "maven"


def test_parse_build_gradle_missing_file(tmp_path: Path) -> None:
    result = _parse_build_gradle(tmp_path / "build.gradle", "build.gradle")
    assert result == []


# --- pipeline integration ---


def test_pipeline_java_maven_ecosystems() -> None:
    report = build_audit_report(fixture_path("java_maven_repo"))
    assert "maven" in report.dependencies.ecosystems


def test_pipeline_java_gradle_ecosystems() -> None:
    report = build_audit_report(fixture_path("java_gradle_repo"))
    assert "maven" in report.dependencies.ecosystems


# --- framework detection ---


def test_framework_spring_boot() -> None:
    report = build_audit_report(fixture_path("java_maven_repo"))
    assert "Spring Boot" in report.inventory.frameworks


def test_framework_quarkus() -> None:
    report = build_audit_report(fixture_path("java_gradle_repo"))
    assert "Quarkus" in report.inventory.frameworks


# --- language detection ---


def test_java_language_detected() -> None:
    report = build_audit_report(fixture_path("java_maven_repo"))
    language_names = [ls.language for ls in report.inventory.languages]
    assert "Java" in language_names


# --- quality signals ---


def test_java_quality_lint_detected() -> None:
    report = build_audit_report(fixture_path("java_maven_repo"))
    assert report.quality.lint_present is True


def test_java_quality_tests_detected() -> None:
    report = build_audit_report(fixture_path("java_maven_repo"))
    assert report.quality.has_tests is True


def test_java_quality_typing_present() -> None:
    report = build_audit_report(fixture_path("java_maven_repo"))
    assert report.quality.typing_present is True
    # typing_files must contain only real paths — no synthetic Java marker
    for f in report.quality.typing_files:
        assert "[Java" not in f
