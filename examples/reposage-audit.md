# RepoSage Audit: reposage

## Project Summary
- Root path: `C:\git\reposage`
- Scanned files: 166
- Ignored directories: .claude/worktrees/jolly-wozniak/tests/__pycache__, .git, .mypy_cache, .ruff_cache, .tmp/pytest-of-unknown/pytest-0/test_scan_repository_ignores_c0/node_modules, .tox, dist, src/reposage/__pycache__, src/reposage/analysis/__pycache__, src/reposage/enrichment/__pycache__, src/reposage/reports/__pycache__, src/reposage/scan/__pycache__, tests/__pycache__, tests/fixtures/mixed_repo/.ruff_cache, tests/fixtures/mixed_repo/tests/__pycache__, tests/fixtures/python_repo/.ruff_cache, tests/fixtures/python_repo/tests/__pycache__
- Top-level layout: .claude, .coverage, .env, .github, .gitignore, .tmp, AGENTS.md, CHANGELOG.md, CONTRIBUTING.md, LICENSE, M2_PLAN.md, PLAN.md, README.md, docs, examples, pyproject.toml, src/reposage, tests, tox.ini
- Languages: Python (75), Markdown (37), TOML (10), JSON (10), YAML (11), Text (4), React TSX (4), JavaScript (2)
- Framework signals: Express, FastAPI, Flask, Next.js, React
- Dependency ecosystems: npm, python
- Dependency manifests: .claude/worktrees/jolly-wozniak/pyproject.toml, .claude/worktrees/jolly-wozniak/tests/fixtures/js_repo/package.json, .claude/worktrees/jolly-wozniak/tests/fixtures/mixed_repo/package.json, .claude/worktrees/jolly-wozniak/tests/fixtures/mixed_repo/pyproject.toml, .claude/worktrees/jolly-wozniak/tests/fixtures/monorepo_repo/packages/api/package.json, .claude/worktrees/jolly-wozniak/tests/fixtures/monorepo_repo/packages/lib/pyproject.toml, .claude/worktrees/jolly-wozniak/tests/fixtures/python_repo/pyproject.toml, .tmp/pytest-of-unknown/pytest-0/test_dependency_surface_risk_u0/requirements.txt, .tmp/pytest-of-unknown/pytest-0/test_parse_package_json_return0/package.json, .tmp/pytest-of-unknown/pytest-0/test_parse_pyproject_collects_0/pyproject.toml, .tmp/pytest-of-unknown/pytest-0/test_parse_pyproject_returns_e0/pyproject.toml, .tmp/pytest-of-unknown/pytest-0/test_parse_requirements_skips_0/requirements.txt, .tmp/pytest-of-unknown/pytest-0/test_summarize_dependencies_di0/requirements-dev.txt, pyproject.toml, tests/fixtures/js_repo/package.json, tests/fixtures/mixed_repo/package.json, tests/fixtures/mixed_repo/pyproject.toml, tests/fixtures/monorepo_repo/packages/api/package.json, tests/fixtures/monorepo_repo/packages/lib/pyproject.toml, tests/fixtures/python_repo/pyproject.toml

## Architecture Guess
- Main modules: .claude, tests, src/reposage, .tmp, .github
- Probable layers: application source, automated tests, documentation, automation, examples
- Dependency directions: tests likely depend on source modules, not the reverse, documentation appears separate from runtime code, automation configuration is isolated from product code
- Possible god modules: .claude/worktrees/jolly-wozniak/PLAN_FIX.md (498 lines), M2_PLAN.md (482 lines), .claude/worktrees/jolly-wozniak/AGENTS.md (435 lines), AGENTS.md (435 lines), tests/test_enrichment.py (406 lines)
- Hotspots: .claude/worktrees/jolly-wozniak/PLAN_FIX.md (21778 bytes, 498 lines), M2_PLAN.md (18776 bytes, 482 lines), .claude/worktrees/jolly-wozniak/AGENTS.md (15391 bytes, 435 lines), AGENTS.md (15391 bytes, 435 lines), tests/test_enrichment.py (14069 bytes, 406 lines)
- Notes: Multiple manifest roots detected; monorepo behavior is likely., Source code appears separated from tests/docs via a src-style layout.

## Engineering Quality Checklist
- Quality score: 100/100
- Positive signals: Automated tests detected., CI configuration detected., Repository documentation detected., Packaging metadata detected., Lint configuration detected., Typing configuration detected.
- Missing signals: none
- Test files: .claude/worktrees/jolly-wozniak/tests/__init__.py, .claude/worktrees/jolly-wozniak/tests/conftest.py, .claude/worktrees/jolly-wozniak/tests/fixtures/js_repo/src/index.tsx, .claude/worktrees/jolly-wozniak/tests/fixtures/missing_signals_repo/src/legacy.py, .claude/worktrees/jolly-wozniak/tests/fixtures/mixed_repo/src/app/main.py, .claude/worktrees/jolly-wozniak/tests/fixtures/mixed_repo/tests/test_main.py, .claude/worktrees/jolly-wozniak/tests/fixtures/mixed_repo/web/src/index.tsx, .claude/worktrees/jolly-wozniak/tests/fixtures/monorepo_repo/packages/lib/src/lib_pkg/__init__.py, .claude/worktrees/jolly-wozniak/tests/fixtures/python_repo/src/example_pkg/__init__.py, .claude/worktrees/jolly-wozniak/tests/fixtures/python_repo/src/example_pkg/service.py
- CI files: .github/workflows/ci.yml, .github/workflows/release.yml
- Docs files: .claude/worktrees/jolly-wozniak/README.md, .claude/worktrees/jolly-wozniak/examples/README.md, .claude/worktrees/jolly-wozniak/tests/fixtures/js_repo/README.md, .claude/worktrees/jolly-wozniak/tests/fixtures/mixed_repo/README.md, .claude/worktrees/jolly-wozniak/tests/fixtures/monorepo_repo/README.md, .claude/worktrees/jolly-wozniak/tests/fixtures/python_repo/README.md, README.md, docs/architecture.md, docs/development.md, examples/README.md, tests/fixtures/js_repo/README.md, tests/fixtures/mixed_repo/README.md, tests/fixtures/monorepo_repo/README.md, tests/fixtures/python_repo/README.md
- Packaging files: .claude/worktrees/jolly-wozniak/pyproject.toml, .claude/worktrees/jolly-wozniak/tests/fixtures/js_repo/package.json, .claude/worktrees/jolly-wozniak/tests/fixtures/mixed_repo/package.json, .claude/worktrees/jolly-wozniak/tests/fixtures/mixed_repo/pyproject.toml, .claude/worktrees/jolly-wozniak/tests/fixtures/monorepo_repo/packages/api/package.json, .claude/worktrees/jolly-wozniak/tests/fixtures/monorepo_repo/packages/lib/pyproject.toml, .claude/worktrees/jolly-wozniak/tests/fixtures/python_repo/pyproject.toml, .tmp/pytest-of-unknown/pytest-0/test_parse_package_json_return0/package.json, .tmp/pytest-of-unknown/pytest-0/test_parse_pyproject_collects_0/pyproject.toml, .tmp/pytest-of-unknown/pytest-0/test_parse_pyproject_returns_e0/pyproject.toml, pyproject.toml, tests/fixtures/js_repo/package.json, tests/fixtures/mixed_repo/package.json, tests/fixtures/mixed_repo/pyproject.toml, tests/fixtures/monorepo_repo/packages/api/package.json, tests/fixtures/monorepo_repo/packages/lib/pyproject.toml, tests/fixtures/python_repo/pyproject.toml
- Lint files: .tmp/pytest-of-unknown/pytest-0/test_eslint_v9_flat_config_fil0/eslint.config.js, .tmp/pytest-of-unknown/pytest-0/test_eslint_v9_flat_config_fil1/eslint.config.mjs, .tmp/pytest-of-unknown/pytest-0/test_eslint_v9_flat_config_fil2/eslint.config.cjs, pyproject.toml
- Typing files: .claude/worktrees/jolly-wozniak/src/reposage/py.typed, pyproject.toml, src/reposage/py.typed

## Risk Hotspots
- [medium] Large modules detected: The largest files are large enough to become coordination and review hotspots.
  Suggested action: Split oversized modules by responsibility and add focused tests around the seams.
- [low] Dependency surface area is growing: A larger dependency set increases upgrade and security maintenance cost.
  Suggested action: Review dependencies for overlap, abandoned packages, and version sprawl.

## Recommended Next Issues
1. Refactor the largest modules into smaller, responsibility-focused units.
1. Audit and rationalize the dependency set.

## Dependency Summary
- anthropic >=0.40 [python/ai] from pyproject.toml
- build >=1.2 [python/dev] from .claude/worktrees/jolly-wozniak/pyproject.toml
- build >=1.2 [python/dev] from pyproject.toml
- express ^5.0.0 [npm/dependencies] from .claude/worktrees/jolly-wozniak/tests/fixtures/monorepo_repo/packages/api/package.json
- express ^5.0.0 [npm/dependencies] from tests/fixtures/monorepo_repo/packages/api/package.json
- fastapi >=0.115 [python/runtime] from .claude/worktrees/jolly-wozniak/tests/fixtures/mixed_repo/pyproject.toml
- fastapi >=0.115 [python/runtime] from .claude/worktrees/jolly-wozniak/tests/fixtures/python_repo/pyproject.toml
- fastapi >=0.115 [python/runtime] from tests/fixtures/mixed_repo/pyproject.toml
- fastapi >=0.115 [python/runtime] from tests/fixtures/python_repo/pyproject.toml
- flask >=3.0 [python/requirements] from .tmp/pytest-of-unknown/pytest-0/test_dependency_surface_risk_u0/requirements.txt
- flask >=3.0 [python/requirements] from .tmp/pytest-of-unknown/pytest-0/test_parse_requirements_skips_0/requirements.txt
- hatchling >=1.26 [python/dev] from .claude/worktrees/jolly-wozniak/pyproject.toml
- hatchling >=1.26 [python/dev] from pyproject.toml
- mkdocs * [python/docs] from .tmp/pytest-of-unknown/pytest-0/test_parse_pyproject_collects_0/pyproject.toml
- mypy >=1.11 [python/dev] from .claude/worktrees/jolly-wozniak/pyproject.toml
