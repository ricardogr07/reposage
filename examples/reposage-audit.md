# RepoSage Audit: reposage

## Project Summary
- Root path: `C:\git\reposage`
- Scanned files: 175
- Ignored directories: .git, .mypy_cache, .ruff_cache, .tox, src/reposage/__pycache__, src/reposage/analysis/__pycache__, src/reposage/api/__pycache__, src/reposage/enrichment/__pycache__, src/reposage/reports/__pycache__, src/reposage/scan/__pycache__, src/reposage/security/__pycache__, src/reposage/server/__pycache__, tests/__pycache__, tests/fixtures/mixed_repo/.ruff_cache, tests/fixtures/mixed_repo/tests/__pycache__, tests/fixtures/python_repo/.ruff_cache, tests/fixtures/python_repo/tests/__pycache__
- Top-level layout: .claude, .coverage, .env, .github, .gitignore, .pre-commit-config.yaml, CHANGELOG.md, CONTRIBUTING.md, Dockerfile, LICENSE, README.md, action.yml, docs, examples, k8s, pyproject.toml, scripts, src/reposage, terraform, tests, tox.ini
- Languages: Python (81), Markdown (26), JSON (13), YAML (13), TOML (6), Docker (1), TypeScript (2), Java (3), Rust (3), C# (2), React TSX (2)
- Framework signals: ASP.NET Core, Angular, Axum, Dapper, Entity Framework Core, Express, FastAPI, Next.js, Quarkus, React, SQLx, Spring Boot
- Dependency ecosystems: cargo, maven, npm, nuget, python
- Dependency manifests: pyproject.toml, tests/fixtures/api_repo/pyproject.toml, tests/fixtures/csharp_repo/src/MyApp.Tests/MyApp.Tests.csproj, tests/fixtures/csharp_repo/src/MyApp/MyApp.csproj, tests/fixtures/java_gradle_repo/build.gradle, tests/fixtures/java_maven_repo/pom.xml, tests/fixtures/js_repo/package.json, tests/fixtures/mixed_repo/package.json, tests/fixtures/mixed_repo/pyproject.toml, tests/fixtures/monorepo_repo/packages/api/package.json, tests/fixtures/monorepo_repo/packages/lib/pyproject.toml, tests/fixtures/python_repo/pyproject.toml, tests/fixtures/rust_repo/Cargo.toml, tests/fixtures/ts_repo/package.json

## Architecture Guess
- Main modules: tests, src/reposage, .github, docs, terraform
- Probable layers: application source, automated tests, documentation, automation, examples
- Dependency directions: tests likely depend on source modules, not the reverse, documentation appears separate from runtime code, automation configuration is isolated from product code
- Possible god modules: examples/reposage-audit.json (660 lines), docs/plans/archive/m2-ai-enrichment.md (482 lines), docs/plans/archive/m8-m11-roadmap.md (398 lines), docs/plans/archive/m12-m13-roadmap.md (368 lines), src/reposage/scan/_dep_parsers.py (358 lines)
- Hotspots: examples/reposage-audit.json (19445 bytes, 660 lines), docs/plans/archive/m2-ai-enrichment.md (18776 bytes, 482 lines), docs/plans/archive/m8-m11-roadmap.md (17828 bytes, 398 lines), docs/plans/archive/m12-m13-roadmap.md (14874 bytes, 368 lines), src/reposage/scan/_dep_parsers.py (10852 bytes, 358 lines)
- Notes: Multiple manifest roots detected; monorepo behavior is likely., Source code appears separated from tests/docs via a src-style layout.

## Engineering Quality Checklist
- Quality score: 100/100
- Positive signals: Automated tests detected., CI configuration detected., Repository documentation detected., Packaging metadata detected., Lint configuration detected., Typing configuration detected.
- Missing signals: none
- Test files: tests/__init__.py, tests/conftest.py, tests/fixtures/api_repo/src/mylib/__init__.py, tests/fixtures/api_repo/src/mylib/core.py, tests/fixtures/api_repo/src/mylib/utils.py, tests/fixtures/csharp_repo/src/MyApp.Tests/ProgramTests.cs, tests/fixtures/csharp_repo/src/MyApp/Program.cs, tests/fixtures/java_gradle_repo/src/main/java/App.java, tests/fixtures/java_maven_repo/src/main/java/App.java, tests/fixtures/java_maven_repo/src/test/java/AppTest.java
- CI files: .github/workflows/ci.yml, .github/workflows/demo.yml, .github/workflows/deploy.yml, .github/workflows/release.yml
- Docs files: README.md, docs/agents.md, docs/architecture.md, docs/development.md, docs/plans/archive/m1-foundation.md, docs/plans/archive/m12-m13-roadmap.md, docs/plans/archive/m2-ai-enrichment.md, docs/plans/archive/m8-m11-roadmap.md, examples/README.md, tests/fixtures/api_repo/README.md, tests/fixtures/java_gradle_repo/README.md, tests/fixtures/java_maven_repo/README.md, tests/fixtures/js_repo/README.md, tests/fixtures/mixed_repo/README.md, tests/fixtures/monorepo_repo/README.md, tests/fixtures/python_repo/README.md, tests/fixtures/ts_repo/README.md
- Packaging files: pyproject.toml, tests/fixtures/api_repo/pyproject.toml, tests/fixtures/js_repo/package.json, tests/fixtures/mixed_repo/package.json, tests/fixtures/mixed_repo/pyproject.toml, tests/fixtures/monorepo_repo/packages/api/package.json, tests/fixtures/monorepo_repo/packages/lib/pyproject.toml, tests/fixtures/python_repo/pyproject.toml, tests/fixtures/ts_repo/package.json
- Lint files: pyproject.toml, tests/fixtures/java_maven_repo/checkstyle.xml
- Typing files: pyproject.toml, src/reposage/py.typed, tests/fixtures/ts_repo/tsconfig.json

## Risk Hotspots
- [medium] Large modules detected: The largest files are large enough to become coordination and review hotspots.
  Suggested action: Split oversized modules by responsibility and add focused tests around the seams.
- [low] Dependency surface area is growing: A larger dependency set increases upgrade and security maintenance cost.
  Suggested action: Review dependencies for overlap, abandoned packages, and version sprawl.

## Recommended Next Issues
1. Refactor the largest modules into smaller, responsibility-focused units.
1. Audit and rationalize the dependency set.

## Dependency Summary
- @angular/core ^17.0.0 [npm/dependencies] from tests/fixtures/ts_repo/package.json
- Dapper 2.1.28 [nuget/runtime] from tests/fixtures/csharp_repo/src/MyApp/MyApp.csproj
- Microsoft.AspNetCore.OpenApi 8.0.0 [nuget/runtime] from tests/fixtures/csharp_repo/src/MyApp/MyApp.csproj
- Microsoft.EntityFrameworkCore 8.0.0 [nuget/runtime] from tests/fixtures/csharp_repo/src/MyApp/MyApp.csproj
- Microsoft.NET.Test.Sdk 17.11.0 [nuget/runtime] from tests/fixtures/csharp_repo/src/MyApp.Tests/MyApp.Tests.csproj
- anthropic >=0.40 [python/ai] from pyproject.toml
- axum 0.7 [cargo/runtime] from tests/fixtures/rust_repo/Cargo.toml
- build >=1.2 [python/dev] from pyproject.toml
- cc 1.0 [cargo/build] from tests/fixtures/rust_repo/Cargo.toml
- express ^5.0.0 [npm/dependencies] from tests/fixtures/monorepo_repo/packages/api/package.json
- fastapi >=0.115 [python/runtime] from tests/fixtures/mixed_repo/pyproject.toml
- fastapi >=0.115 [python/runtime] from tests/fixtures/python_repo/pyproject.toml
- hatchling >=1.26 [python/dev] from pyproject.toml
- httpx >=0.27 [python/server] from pyproject.toml
- io.quarkus:quarkus-arc 3.6.0 [maven/runtime] from tests/fixtures/java_gradle_repo/build.gradle

## TypeScript

_No tsconfig.json found._

**Code signals:**
- `any` usage count: 5
- Untyped exports: 2
- Non-any type assertions: 1
