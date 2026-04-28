# RepoSage M12–M13 Roadmap

## Overview

| Milestone | Theme | Complexity |
|---|---|---|
| [M12](#m12--rust-language-support) | Rust Language Support | M |
| [M13](#m13--c-language-support) | C# Language Support | M |

Both milestones follow the exact pattern established by M10 (Java): manifest parsing,
dependency extraction, framework detection, quality signals, fixture, and tests. No new
optional dependencies — all parsing uses stdlib (`tomllib`, `xml.etree.ElementTree`, `re`).

---

## M12 — Rust Language Support

**Complexity: M**

**Goal:** Add full Rust project understanding — `Cargo.toml` dependency parsing, Cargo
workspace awareness, Rust framework detection, and Rust-specific quality signals. Language
detection already works (`.rs` → `"Rust"` in `languages.py`); this milestone adds
dependency and metadata understanding.

### Manifest Files

| File | Role |
|---|---|
| `Cargo.toml` | Package or workspace manifest (TOML) |
| `Cargo.lock` | Lock file (not parsed for deps — versions come from `Cargo.toml`) |

### Implementation Steps

#### Step 1 — Cargo.toml parser: `src/reposage/scan/_dep_parsers.py` (extend existing)

- `_parse_cargo_toml(path: Path, relative_path: str) -> list[Dependency]`
- Use `tomllib` (stdlib, already imported) to parse
- Extract from `[dependencies]`, `[dev-dependencies]`, `[build-dependencies]`
- Also handle `[workspace.dependencies]` for workspace manifests
- Package name format: crate name (no group prefix unlike Maven)
- Version: value if string, or `version` key if table value (`dep = { version = "1.0" }`)
- Ecosystem: `"cargo"`
- Group mapping:

  | Cargo section | `Dependency.group` |
  |---|---|
  | `[dependencies]` | `"runtime"` |
  | `[dev-dependencies]` | `"dev"` |
  | `[build-dependencies]` | `"build"` |
  | `[workspace.dependencies]` | `"runtime"` |

- Edge cases:
  - Path dependencies (`dep = { path = "../other" }`) → version `""`, include with name
  - Git dependencies (`dep = { git = "..." }`) → version `""`, include with name
  - Skip `dep = false` (disabled features)

#### Step 2 — Manifest detection: `src/reposage/scan/dependencies.py`

- Add `_RUST_MANIFESTS = {"Cargo.toml"}` constant (case-sensitive — Rust convention)
- Extend `_is_supported_manifest` to include `_RUST_MANIFESTS`
- Add dispatch in `summarize_dependencies`:
  ```python
  elif file_name == "Cargo.toml":
      parsed_dependencies = _parse_cargo_toml(absolute_path, manifest_path)
  ```

#### Step 3 — Rust quality signals: `src/reposage/analysis/quality.py`

- **Test detection:** `tests/` directory OR files matching `*_test.rs` OR inline `#[cfg(test)]`
  modules (detect via `grep`-style scan: `b"#[cfg(test)]"` in raw file bytes)
- **Lint detection:** `clippy.toml` or `.clippy.toml` in repo root
- **Typing:** Rust is statically typed — set `typing_present=True` when Rust detected
- **Formatting:** `rustfmt.toml` or `.rustfmt.toml` presence → `has_formatter=True`

#### Step 4 — Rust framework detection: `src/reposage/scan/repo_meta.py`

Detect from `[dependencies]` crate names:

| Crate | Framework signal |
|---|---|
| `tokio` | Async runtime (Tokio) |
| `actix-web` | Web framework (Actix) |
| `axum` | Web framework (Axum) |
| `rocket` | Web framework (Rocket) |
| `warp` | Web framework (Warp) |
| `serde` | Serialization (Serde) |
| `diesel` | ORM (Diesel) |
| `sqlx` | Async SQL (SQLx) |
| `tonic` | gRPC (Tonic) |
| `tauri` | Desktop (Tauri) |

Strategy: after parsing `Cargo.toml` dependencies, collect crate names into a set and match
against the table above. Append matching framework names to `InventorySignals.frameworks`.

#### Step 5 — Workspace support

- A `Cargo.toml` with `[workspace]` section is a workspace manifest
- Parse `members = [...]` to identify member crate paths
- Do NOT recursively parse member `Cargo.toml` files — they are already scanned by the
  filesystem walk and dispatched individually

#### Step 6 — Fixture and tests

**New fixture:** `tests/fixtures/rust_repo/`

```
tests/fixtures/rust_repo/
    Cargo.toml          (package with [dependencies] and [dev-dependencies])
    Cargo.lock          (minimal, not parsed)
    src/
        main.rs         (fn main + #[cfg(test)] block)
        lib.rs          (public fn + unit test)
    tests/
        integration_test.rs
```

**`Cargo.toml`** content:
```toml
[package]
name = "rust-sample"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio = { version = "1", features = ["full"] }
axum = "0.7"
serde = { version = "1", features = ["derive"] }
sqlx = { version = "0.7", git = "https://github.com/launchbadge/sqlx" }

[dev-dependencies]
tokio-test = "0.4"
```

**Tests to write** (`tests/test_rust.py`, ~80 lines):

1. `test_cargo_toml_runtime_deps` — parse fixture `Cargo.toml`; assert `tokio`, `axum`, `serde` found with `group="runtime"`
2. `test_cargo_toml_dev_deps` — assert `tokio-test` found with `group="dev"`
3. `test_cargo_toml_git_dep` — assert `sqlx` present with `version=""`
4. `test_cargo_toml_ecosystem` — all deps have `ecosystem="cargo"`
5. `test_rust_framework_detection` — `build_audit_report(fixture_path("rust_repo"))` → `"Axum"` in frameworks
6. `test_rust_language_detected` — `"Rust"` in detected languages
7. `test_rust_test_detection` — `has_tests=True` (via `tests/integration_test.rs`)
8. `test_cargo_toml_workspace` — tmp fixture with `[workspace]` section; assert no crash, returns `[]` or workspace-level deps
9. `test_cargo_toml_invalid` — malformed TOML; assert returns `[]`

### New / Modified Files

| File | Action |
|---|---|
| `src/reposage/scan/_dep_parsers.py` | **Modify** — add `_parse_cargo_toml` |
| `src/reposage/scan/dependencies.py` | **Modify** — add `_RUST_MANIFESTS`, dispatch |
| `src/reposage/analysis/quality.py` | **Modify** — Rust test/lint/typing signals |
| `src/reposage/scan/repo_meta.py` | **Modify** — Rust framework detection |
| `tests/fixtures/rust_repo/` | **New** — fixture |
| `tests/test_rust.py` | **New** — ~80 lines, 9 tests |

No changes to `models.py`, `cli.py`, or renderers — Rust data flows through existing
`Dependency`, `InventorySignals`, and `QualitySignals` fields.

---

## M13 — C# Language Support

**Complexity: M**

**Goal:** Add C# / .NET project understanding — `.csproj` dependency parsing (NuGet),
solution file awareness, C# framework detection, and C# quality signals. Language
detection needs `.cs` added to `languages.py`.

### Manifest Files

| File | Role |
|---|---|
| `*.csproj` | Project file — NuGet `<PackageReference>` entries (XML) |
| `*.sln` | Solution file — lists projects (not parsed for deps, used for workspace signal) |
| `packages.config` | Legacy NuGet format (pre-SDK-style projects) |
| `global.json` | SDK version pinning (not parsed for deps) |
| `Directory.Packages.props` | Central package management (NuGet CPM) |

Primary parse target: `*.csproj` (SDK-style, current standard). Legacy `packages.config`
supported as fallback.

### Implementation Steps

#### Step 1 — Language detection: `src/reposage/scan/languages.py`

Add to `EXTENSION_LANGUAGE_MAP`:
```python
".cs": "C#",
".csx": "C# Script",
".fs": "F#",
".vb": "Visual Basic",
```

#### Step 2 — `.csproj` parser: `src/reposage/scan/_dep_parsers.py` (extend existing)

- `_parse_csproj(path: Path, relative_path: str) -> list[Dependency]`
- Parse with `xml.etree.ElementTree` (stdlib, already imported)
- SDK-style `.csproj` — extract `<PackageReference Include="..." Version="..." />`
  - `Include` attribute → `name`
  - `Version` attribute → `version` (may be absent if using CPM)
- Map `Condition` attribute to group:
  - Contains `Test` or `test` → `"test"`
  - Otherwise → `"runtime"` (C# doesn't distinguish runtime/dev in `.csproj` by default)
- Ecosystem: `"nuget"`
- Strip XML namespace prefix if present (`{http://schemas.microsoft.com/developer/msbuild/2003}`)

- `_parse_packages_config(path: Path, relative_path: str) -> list[Dependency]`
  - Legacy format: `<package id="..." version="..." targetFramework="..." />`
  - `id` → `name`, `version` → `version`, ecosystem `"nuget"`, group `"runtime"`

#### Step 3 — Central Package Management: `src/reposage/scan/_dep_parsers.py`

- `_parse_directory_packages_props(path: Path, relative_path: str) -> list[Dependency]`
- Same XML structure as `.csproj` but `<PackageVersion Include="..." Version="..." />`
- Group: `"runtime"` for all (CPM doesn't segregate)

#### Step 4 — Manifest detection: `src/reposage/scan/dependencies.py`

- `.csproj` files are not detected by filename — they share a suffix pattern
- Add `_CSHARP_MANIFEST_SUFFIXES = {".csproj"}` alongside the name-based sets
- Extend `_is_supported_manifest`:
  ```python
  or PurePosixPath(file_name).suffix in _CSHARP_MANIFEST_SUFFIXES
  or file_name in {"packages.config", "Directory.Packages.props"}
  ```
- Dispatch:
  ```python
  elif Path(file_name).suffix == ".csproj":
      parsed_dependencies = _parse_csproj(absolute_path, manifest_path)
  elif file_name == "packages.config":
      parsed_dependencies = _parse_packages_config(absolute_path, manifest_path)
  elif file_name == "Directory.Packages.props":
      parsed_dependencies = _parse_directory_packages_props(absolute_path, manifest_path)
  ```

#### Step 5 — C# quality signals: `src/reposage/analysis/quality.py`

- **Test detection:** `*Test.cs`, `*Tests.cs`, `*Spec.cs` files OR project name contains
  `.Tests`, `.Test`, `.Specs`; OR NuGet packages `xunit`, `NUnit`, `MSTest.TestFramework`
  in deps
- **Lint detection:** `.editorconfig` in repo root (standard for C# formatting); `StyleCop`
  or `Roslynator` NuGet package in deps
- **Nullable reference types:** detect `<Nullable>enable</Nullable>` in `.csproj` → treat
  as typing signal (`typing_present=True`)
- **Typing:** C# is statically typed — always `typing_present=True` when C# detected

#### Step 6 — C# framework detection: `src/reposage/scan/repo_meta.py`

Detect from NuGet package names (case-insensitive prefix match):

| Package prefix / name | Framework signal |
|---|---|
| `Microsoft.AspNetCore` | ASP.NET Core |
| `Microsoft.AspNetCore.Components` | Blazor |
| `Microsoft.EntityFrameworkCore` | Entity Framework Core |
| `Microsoft.Maui` | .NET MAUI |
| `Grpc.AspNetCore` | gRPC |
| `MassTransit` | MassTransit (messaging) |
| `Hangfire` | Hangfire (background jobs) |
| `xunit` / `NUnit` / `MSTest` | test framework (not a prod framework signal) |
| `Dapper` | Dapper (micro-ORM) |

Also: presence of a `.sln` file in the root → append `".NET Solution"` to workspace signals
(indicates multi-project repo).

#### Step 7 — Fixture and tests

**New fixture:** `tests/fixtures/csharp_repo/`

```
tests/fixtures/csharp_repo/
    MyApp.sln
    src/
        MyApp/
            MyApp.csproj
            Program.cs
        MyApp.Tests/
            MyApp.Tests.csproj
            ProgramTests.cs
```

**`src/MyApp/MyApp.csproj`** content:
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.AspNetCore.OpenApi" Version="8.0.0" />
    <PackageReference Include="Microsoft.EntityFrameworkCore" Version="8.0.0" />
    <PackageReference Include="Dapper" Version="2.1.28" />
  </ItemGroup>
</Project>
```

**`src/MyApp.Tests/MyApp.Tests.csproj`** content:
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="xunit" Version="2.9.0" />
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.11.0" />
  </ItemGroup>
</Project>
```

**Tests to write** (`tests/test_csharp.py`, ~90 lines):

1. `test_csproj_runtime_deps` — parse `MyApp.csproj`; assert `Microsoft.AspNetCore.OpenApi`, `Microsoft.EntityFrameworkCore`, `Dapper` found with `group="runtime"`
2. `test_csproj_ecosystem` — all deps have `ecosystem="nuget"`
3. `test_csproj_version` — versions correctly extracted
4. `test_packages_config_parsing(tmp_path)` — write a `packages.config` fixture inline; assert deps extracted
5. `test_csharp_language_detected` — `build_audit_report(fixture_path("csharp_repo"))` → `"C#"` in languages
6. `test_csharp_framework_detection` — `"ASP.NET Core"` and `"Entity Framework Core"` in frameworks
7. `test_csharp_test_detection` — `has_tests=True` (via `MyApp.Tests.csproj`)
8. `test_csharp_nullable_typing` — detect `<Nullable>enable</Nullable>` in `.csproj`
9. `test_csproj_invalid_xml(tmp_path)` — malformed XML; assert returns `[]`
10. `test_directory_packages_props(tmp_path)` — write `Directory.Packages.props` inline; assert deps extracted

### New / Modified Files

| File | Action |
|---|---|
| `src/reposage/scan/languages.py` | **Modify** — add `.cs`, `.csx`, `.fs`, `.vb` |
| `src/reposage/scan/_dep_parsers.py` | **Modify** — add `_parse_csproj`, `_parse_packages_config`, `_parse_directory_packages_props` |
| `src/reposage/scan/dependencies.py` | **Modify** — suffix-based manifest detection, dispatch |
| `src/reposage/analysis/quality.py` | **Modify** — C# test/lint/nullable/typing signals |
| `src/reposage/scan/repo_meta.py` | **Modify** — C# framework detection |
| `tests/fixtures/csharp_repo/` | **New** — fixture |
| `tests/test_csharp.py` | **New** — ~90 lines, 10 tests |

No changes to `models.py`, `cli.py`, or renderers.

---

## Shared Patterns

Both milestones reuse the M10 Java pattern verbatim:

- **No new models** — `Dependency`, `InventorySignals`, `QualitySignals`, `AuditReport` already
  accommodate both languages
- **No new CLI flags** — dependency parsing runs unconditionally in `build_audit_report`
- **No new optional deps** — `tomllib` (Rust) and `xml.etree.ElementTree` (C#) are stdlib
- **No new tox envs** — tests run in default `pytest tests/ -q`
- **400-line limit** — `_dep_parsers.py` is currently 300 lines; adding both parsers may push
  it toward the limit; split into `_dep_parsers_jvm.py` / `_dep_parsers_dotnet.py` if needed
- **Fixture-first testing** — each milestone ships at least one fixture repo

## Verification

```bash
# M12 — Rust
pytest tests/test_rust.py -v
pytest tests/ -q                           # no regressions
tox -e lint && tox -e linecount
python -m reposage report tests/fixtures/rust_repo --format json | python -m json.tool | python -c "import sys,json; d=json.load(sys.stdin); print(d['dependencies'])"

# M13 — C#
pytest tests/test_csharp.py -v
pytest tests/ -q                           # no regressions
tox -e lint && tox -e linecount
python -m reposage report tests/fixtures/csharp_repo --format json | python -m json.tool | python -c "import sys,json; d=json.load(sys.stdin); print(d['dependencies'])"
```
