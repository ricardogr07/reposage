"""Repository inventory and metadata helpers."""

from __future__ import annotations

from collections import Counter
from pathlib import Path, PurePosixPath

from reposage.config import ScanConfig
from reposage.models import DependencySummary, FileRecord, LanguageStat, RepoInventory

FRAMEWORK_NAMES = {
    "@angular/core": "Angular",
    "@nestjs/core": "NestJS",
    "django": "Django",
    "express": "Express",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "next": "Next.js",
    "nestjs": "NestJS",
    "react": "React",
    "svelte": "Svelte",
    "vue": "Vue",
    # Rust web/application frameworks
    "actix-web": "Actix",
    "axum": "Axum",
    "rocket": "Rocket",
    "warp": "Warp",
    "tauri": "Tauri",
    "tonic": "Tonic",
    "diesel": "Diesel",
    "sqlx": "SQLx",
}

FRAMEWORK_PREFIXES = {
    "org.springframework.boot:": "Spring Boot",
    "io.quarkus:": "Quarkus",
    "io.micronaut:": "Micronaut",
    "jakarta.": "Jakarta EE",
    # .NET / NuGet prefix matching (more-specific before less-specific)
    "microsoft.aspnetcore.components": "Blazor",
    "microsoft.aspnetcore": "ASP.NET Core",
    "microsoft.entityframeworkcore": "Entity Framework Core",
    "microsoft.maui": ".NET MAUI",
    "grpc.aspnetcore": "gRPC",
    "masstransit": "MassTransit",
    "hangfire": "Hangfire",
    "dapper": "Dapper",
}


def build_inventory(
    root: Path,
    *,
    file_records: list[FileRecord],
    ignored_directories: list[str],
    languages: list[LanguageStat],
    dependencies: DependencySummary,
    config: ScanConfig,
) -> RepoInventory:
    """Build the top-level repository inventory model."""

    del config

    top_level_entries = sorted({_top_level_entry(record.path) for record in file_records})
    frameworks = _detect_frameworks(file_records, dependencies)
    largest_files = sorted(
        file_records,
        key=lambda record: (-record.size_bytes, -record.line_count, record.path),
    )[:5]

    return RepoInventory(
        project_name=root.name,
        root_path=str(root),
        scanned_files=len(file_records),
        ignored_directories=ignored_directories,
        top_level_entries=top_level_entries,
        languages=languages,
        frameworks=frameworks,
        largest_files=largest_files,
    )


def _top_level_entry(path: str) -> str:
    parts = PurePosixPath(path).parts
    if not parts:
        return path
    if len(parts) >= 2 and parts[0] in {"src", "app", "apps", "packages"}:
        return f"{parts[0]}/{parts[1]}"
    return parts[0]


def _detect_frameworks(
    file_records: list[FileRecord],
    dependencies: DependencySummary,
) -> list[str]:
    detected: set[str] = set()
    dependency_names = {dependency.name.lower() for dependency in dependencies.dependencies}
    for dependency_name, framework_name in FRAMEWORK_NAMES.items():
        if dependency_name in dependency_names:
            detected.add(framework_name)

    for dep in dependencies.dependencies:
        dep_name = dep.name.lower()
        for prefix, framework_name in FRAMEWORK_PREFIXES.items():
            if dep_name.startswith(prefix):
                detected.add(framework_name)

    file_names = Counter(PurePosixPath(record.path).name.lower() for record in file_records)
    if "manage.py" in file_names:
        detected.add("Django")
    if "next.config.js" in file_names or "next.config.mjs" in file_names:
        detected.add("Next.js")
    deno_names = {"deno.json", "deno.jsonc"}
    if any(PurePosixPath(record.path).name in deno_names for record in file_records):
        detected.add("Deno")
    if any(PurePosixPath(record.path).name == "bun.lockb" for record in file_records):
        detected.add("Bun")

    return sorted(detected)
