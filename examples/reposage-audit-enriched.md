# RepoSage Audit: reposage

## Project Summary
- Root path: `C:\git\reposage`
- Scanned files: 314
- Ignored directories: .claude/worktrees/jolly-wozniak/tests/__pycache__, .git, .mypy_cache, .ruff_cache, .tmp/pytest-of-unknown/pytest-0/test_scan_repository_ignores_c0/node_modules, .tmp/pytest-of-unknown/pytest-1/test_scan_repository_ignores_c0/node_modules, .tmp/pytest-of-unknown/pytest-2/test_scan_repository_ignores_c0/node_modules, .tox, dist, src/reposage/__pycache__, src/reposage/analysis/__pycache__, src/reposage/enrichment/__pycache__, src/reposage/reports/__pycache__, src/reposage/scan/__pycache__, src/reposage/server/__pycache__, tests/__pycache__, tests/fixtures/mixed_repo/.ruff_cache, tests/fixtures/mixed_repo/tests/__pycache__, tests/fixtures/python_repo/.ruff_cache, tests/fixtures/python_repo/tests/__pycache__
- Top-level layout: .claude, .coverage, .env, .github, .gitignore, .tmp, AGENTS.md, CHANGELOG.md, CONTRIBUTING.md, Dockerfile, LICENSE, M2_PLAN.md, PLAN.md, README.md, action.yml, docs, examples, k8s, pyproject.toml, src/reposage, terraform, tests, tox.ini
- Languages: Python (125), Markdown (61), JSON (19), YAML (29), TOML (18), Docker (2), Text (12), React TSX (6), JavaScript (6)
- Framework signals: Express, FastAPI, Flask, Next.js, React
- Dependency ecosystems: npm, python
- Dependency manifests: .claude/worktrees/jolly-wozniak/pyproject.toml, .claude/worktrees/jolly-wozniak/tests/fixtures/js_repo/package.json, .claude/worktrees/jolly-wozniak/tests/fixtures/mixed_repo/package.json, .claude/worktrees/jolly-wozniak/tests/fixtures/mixed_repo/pyproject.toml, .claude/worktrees/jolly-wozniak/tests/fixtures/monorepo_repo/packages/api/package.json, .claude/worktrees/jolly-wozniak/tests/fixtures/monorepo_repo/packages/lib/pyproject.toml, .claude/worktrees/jolly-wozniak/tests/fixtures/python_repo/pyproject.toml, .claude/worktrees/stupefied-rosalind-327d67/pyproject.toml, .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/js_repo/package.json, .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/mixed_repo/package.json, .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/mixed_repo/pyproject.toml, .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/monorepo_repo/packages/api/package.json, .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/monorepo_repo/packages/lib/pyproject.toml, .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/python_repo/pyproject.toml, .tmp/pytest-of-unknown/pytest-0/test_dependency_surface_risk_u0/requirements.txt, .tmp/pytest-of-unknown/pytest-0/test_parse_package_json_return0/package.json, .tmp/pytest-of-unknown/pytest-0/test_parse_pyproject_collects_0/pyproject.toml, .tmp/pytest-of-unknown/pytest-0/test_parse_pyproject_returns_e0/pyproject.toml, .tmp/pytest-of-unknown/pytest-0/test_parse_requirements_skips_0/requirements.txt, .tmp/pytest-of-unknown/pytest-0/test_summarize_dependencies_di0/requirements-dev.txt, .tmp/pytest-of-unknown/pytest-1/test_dependency_surface_risk_u0/requirements.txt, .tmp/pytest-of-unknown/pytest-1/test_parse_package_json_return0/package.json, .tmp/pytest-of-unknown/pytest-1/test_parse_pyproject_collects_0/pyproject.toml, .tmp/pytest-of-unknown/pytest-1/test_parse_pyproject_returns_e0/pyproject.toml, .tmp/pytest-of-unknown/pytest-1/test_parse_requirements_skips_0/requirements.txt, .tmp/pytest-of-unknown/pytest-1/test_summarize_dependencies_di0/requirements-dev.txt, .tmp/pytest-of-unknown/pytest-2/test_dependency_surface_risk_u0/requirements.txt, .tmp/pytest-of-unknown/pytest-2/test_parse_package_json_return0/package.json, .tmp/pytest-of-unknown/pytest-2/test_parse_pyproject_collects_0/pyproject.toml, .tmp/pytest-of-unknown/pytest-2/test_parse_pyproject_returns_e0/pyproject.toml, .tmp/pytest-of-unknown/pytest-2/test_parse_requirements_skips_0/requirements.txt, .tmp/pytest-of-unknown/pytest-2/test_summarize_dependencies_di0/requirements-dev.txt, pyproject.toml, tests/fixtures/js_repo/package.json, tests/fixtures/mixed_repo/package.json, tests/fixtures/mixed_repo/pyproject.toml, tests/fixtures/monorepo_repo/packages/api/package.json, tests/fixtures/monorepo_repo/packages/lib/pyproject.toml, tests/fixtures/python_repo/pyproject.toml

## Architecture Guess
- Main modules: .claude, .tmp, tests, src/reposage, .github
- Probable layers: application source, automated tests, documentation, automation, examples
- Dependency directions: tests likely depend on source modules, not the reverse, documentation appears separate from runtime code, automation configuration is isolated from product code
- Possible god modules: .claude/worktrees/stupefied-rosalind-327d67/examples/reposage-audit.json (668 lines), examples/reposage-audit.json (668 lines), tests/test_enrichment.py (517 lines), .claude/worktrees/jolly-wozniak/PLAN_FIX.md (498 lines), .claude/worktrees/stupefied-rosalind-327d67/M2_PLAN.md (482 lines)
- Hotspots: .claude/worktrees/stupefied-rosalind-327d67/examples/reposage-audit.json (22352 bytes, 668 lines), examples/reposage-audit.json (22352 bytes, 668 lines), tests/test_enrichment.py (17678 bytes, 517 lines), .claude/worktrees/jolly-wozniak/PLAN_FIX.md (21778 bytes, 498 lines), .claude/worktrees/stupefied-rosalind-327d67/M2_PLAN.md (18776 bytes, 482 lines)
- Notes: Multiple manifest roots detected; monorepo behavior is likely., Source code appears separated from tests/docs via a src-style layout.

## Engineering Quality Checklist
- Quality score: 100/100
- Positive signals: Automated tests detected., CI configuration detected., Repository documentation detected., Packaging metadata detected., Lint configuration detected., Typing configuration detected.
- Missing signals: none
- Test files: .claude/worktrees/jolly-wozniak/tests/__init__.py, .claude/worktrees/jolly-wozniak/tests/conftest.py, .claude/worktrees/jolly-wozniak/tests/fixtures/js_repo/src/index.tsx, .claude/worktrees/jolly-wozniak/tests/fixtures/missing_signals_repo/src/legacy.py, .claude/worktrees/jolly-wozniak/tests/fixtures/mixed_repo/src/app/main.py, .claude/worktrees/jolly-wozniak/tests/fixtures/mixed_repo/tests/test_main.py, .claude/worktrees/jolly-wozniak/tests/fixtures/mixed_repo/web/src/index.tsx, .claude/worktrees/jolly-wozniak/tests/fixtures/monorepo_repo/packages/lib/src/lib_pkg/__init__.py, .claude/worktrees/jolly-wozniak/tests/fixtures/python_repo/src/example_pkg/__init__.py, .claude/worktrees/jolly-wozniak/tests/fixtures/python_repo/src/example_pkg/service.py
- CI files: .github/workflows/ci.yml, .github/workflows/demo.yml, .github/workflows/deploy.yml, .github/workflows/release.yml
- Docs files: .claude/worktrees/jolly-wozniak/README.md, .claude/worktrees/jolly-wozniak/examples/README.md, .claude/worktrees/jolly-wozniak/tests/fixtures/js_repo/README.md, .claude/worktrees/jolly-wozniak/tests/fixtures/mixed_repo/README.md, .claude/worktrees/jolly-wozniak/tests/fixtures/monorepo_repo/README.md, .claude/worktrees/jolly-wozniak/tests/fixtures/python_repo/README.md, .claude/worktrees/stupefied-rosalind-327d67/README.md, .claude/worktrees/stupefied-rosalind-327d67/examples/README.md, .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/js_repo/README.md, .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/mixed_repo/README.md, .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/monorepo_repo/README.md, .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/python_repo/README.md, README.md, docs/architecture.md, docs/development.md, examples/README.md, tests/fixtures/js_repo/README.md, tests/fixtures/mixed_repo/README.md, tests/fixtures/monorepo_repo/README.md, tests/fixtures/python_repo/README.md
- Packaging files: .claude/worktrees/jolly-wozniak/pyproject.toml, .claude/worktrees/jolly-wozniak/tests/fixtures/js_repo/package.json, .claude/worktrees/jolly-wozniak/tests/fixtures/mixed_repo/package.json, .claude/worktrees/jolly-wozniak/tests/fixtures/mixed_repo/pyproject.toml, .claude/worktrees/jolly-wozniak/tests/fixtures/monorepo_repo/packages/api/package.json, .claude/worktrees/jolly-wozniak/tests/fixtures/monorepo_repo/packages/lib/pyproject.toml, .claude/worktrees/jolly-wozniak/tests/fixtures/python_repo/pyproject.toml, .claude/worktrees/stupefied-rosalind-327d67/pyproject.toml, .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/js_repo/package.json, .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/mixed_repo/package.json, .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/mixed_repo/pyproject.toml, .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/monorepo_repo/packages/api/package.json, .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/monorepo_repo/packages/lib/pyproject.toml, .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/python_repo/pyproject.toml, .tmp/pytest-of-unknown/pytest-0/test_parse_package_json_return0/package.json, .tmp/pytest-of-unknown/pytest-0/test_parse_pyproject_collects_0/pyproject.toml, .tmp/pytest-of-unknown/pytest-0/test_parse_pyproject_returns_e0/pyproject.toml, .tmp/pytest-of-unknown/pytest-1/test_parse_package_json_return0/package.json, .tmp/pytest-of-unknown/pytest-1/test_parse_pyproject_collects_0/pyproject.toml, .tmp/pytest-of-unknown/pytest-1/test_parse_pyproject_returns_e0/pyproject.toml, .tmp/pytest-of-unknown/pytest-2/test_parse_package_json_return0/package.json, .tmp/pytest-of-unknown/pytest-2/test_parse_pyproject_collects_0/pyproject.toml, .tmp/pytest-of-unknown/pytest-2/test_parse_pyproject_returns_e0/pyproject.toml, pyproject.toml, tests/fixtures/js_repo/package.json, tests/fixtures/mixed_repo/package.json, tests/fixtures/mixed_repo/pyproject.toml, tests/fixtures/monorepo_repo/packages/api/package.json, tests/fixtures/monorepo_repo/packages/lib/pyproject.toml, tests/fixtures/python_repo/pyproject.toml
- Lint files: .tmp/pytest-of-unknown/pytest-0/test_eslint_v9_flat_config_fil0/eslint.config.js, .tmp/pytest-of-unknown/pytest-0/test_eslint_v9_flat_config_fil1/eslint.config.mjs, .tmp/pytest-of-unknown/pytest-0/test_eslint_v9_flat_config_fil2/eslint.config.cjs, .tmp/pytest-of-unknown/pytest-1/test_eslint_v9_flat_config_fil0/eslint.config.js, .tmp/pytest-of-unknown/pytest-1/test_eslint_v9_flat_config_fil1/eslint.config.mjs, .tmp/pytest-of-unknown/pytest-1/test_eslint_v9_flat_config_fil2/eslint.config.cjs, .tmp/pytest-of-unknown/pytest-2/test_eslint_v9_flat_config_fil0/eslint.config.js, .tmp/pytest-of-unknown/pytest-2/test_eslint_v9_flat_config_fil1/eslint.config.mjs, .tmp/pytest-of-unknown/pytest-2/test_eslint_v9_flat_config_fil2/eslint.config.cjs, pyproject.toml
- Typing files: .claude/worktrees/jolly-wozniak/src/reposage/py.typed, .claude/worktrees/stupefied-rosalind-327d67/src/reposage/py.typed, pyproject.toml, src/reposage/py.typed

## Risk Hotspots
- [medium] Large modules detected: The largest files are large enough to become coordination and review hotspots.
  Suggested action: Split oversized modules by responsibility and add focused tests around the seams.
- [low] Dependency surface area is growing: A larger dependency set increases upgrade and security maintenance cost.
  Suggested action: Review dependencies for overlap, abandoned packages, and version sprawl.

## Recommended Next Issues
1. Refactor the largest modules into smaller, responsibility-focused units.
1. Audit and rationalize the dependency set.

## Dependency Summary
- anthropic >=0.40 [python/ai] from .claude/worktrees/stupefied-rosalind-327d67/pyproject.toml
- anthropic >=0.40 [python/ai] from pyproject.toml
- build >=1.2 [python/dev] from .claude/worktrees/jolly-wozniak/pyproject.toml
- build >=1.2 [python/dev] from .claude/worktrees/stupefied-rosalind-327d67/pyproject.toml
- build >=1.2 [python/dev] from pyproject.toml
- express ^5.0.0 [npm/dependencies] from .claude/worktrees/jolly-wozniak/tests/fixtures/monorepo_repo/packages/api/package.json
- express ^5.0.0 [npm/dependencies] from .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/monorepo_repo/packages/api/package.json
- express ^5.0.0 [npm/dependencies] from tests/fixtures/monorepo_repo/packages/api/package.json
- fastapi >=0.115 [python/runtime] from .claude/worktrees/jolly-wozniak/tests/fixtures/mixed_repo/pyproject.toml
- fastapi >=0.115 [python/runtime] from .claude/worktrees/jolly-wozniak/tests/fixtures/python_repo/pyproject.toml
- fastapi >=0.115 [python/runtime] from .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/mixed_repo/pyproject.toml
- fastapi >=0.115 [python/runtime] from .claude/worktrees/stupefied-rosalind-327d67/tests/fixtures/python_repo/pyproject.toml
- fastapi >=0.115 [python/runtime] from tests/fixtures/mixed_repo/pyproject.toml
- fastapi >=0.115 [python/runtime] from tests/fixtures/python_repo/pyproject.toml
- flask >=3.0 [python/requirements] from .tmp/pytest-of-unknown/pytest-0/test_dependency_surface_risk_u0/requirements.txt

## Module Responsibilities

| Module | Layer | Responsibility |
| --- | --- | --- |
| `.claude` | tooling | Manages Claude AI integration and temporary workspace configuration for development and analysis tasks. |
| `.tmp` | tooling | Stores temporary files and intermediate outputs generated during development and processing workflows. |
| `tests` | test | Contains automated test suites for validating core functionality, enrichment logic, and application behavior. |
| `src/reposage` | domain | Houses the core domain logic for repository analysis, audit generation, and enrichment functionality. |
| `.github` | infrastructure | Defines CI/CD workflows, action configurations, and repository automation rules for continuous integration. |

## Technical Debt

### [HIGH] Large JSON audit files create review and maintenance bottlenecks

The reposage-audit.json files (668 lines, 22KB each) are oversized, making them difficult to review, validate, and maintain. These should be split into smaller, focused segments organized by audit concern.

**GitHub issue title:** Refactor large audit JSON files into modular segments

<details><summary>Issue body</summary>

## Problem
The `examples/reposage-audit.json` and related audit files have grown to 668 lines, making them difficult to navigate and review. Large monolithic files become coordination hotspots.

## Solution
Split audit output into logical modules:
- `audit_modules.json` - module classifications
- `audit_debt.json` - technical debt items
- `audit_improvements.json` - prioritized improvements
- `audit_summary.json` - aggregate metadata

## Benefits
- Easier code review and diffs
- Cleaner data structure
- Simpler to version and track changes
- Better separation of concerns

</details>

### [MEDIUM] Test enrichment module exceeds optimal size with 517 lines

The test_enrichment.py file (517 lines) should be decomposed into separate test modules by concern: unit tests, integration tests, and fixture definitions to improve maintainability.

**GitHub issue title:** Split test_enrichment.py into focused test modules

<details><summary>Issue body</summary>

## Problem
`tests/test_enrichment.py` has grown to 517 lines, making it difficult to locate specific test cases and understand test organization.

## Proposed Structure
- `tests/unit/test_enrichment_core.py` - core enrichment logic tests
- `tests/integration/test_enrichment_api.py` - API contract tests
- `tests/fixtures/enrichment_fixtures.py` - shared test data

## Benefits
- Faster test execution (can run by concern)
- Clearer test intent and categorization
- Reduced file complexity and cognitive load

</details>

### [MEDIUM] Growing dependency surface area increases security maintenance burden

The project has an expanding dependency set that increases the cost of security patching, compatibility testing, and maintenance. A dependency audit and rationalization is needed.

**GitHub issue title:** Audit and rationalize project dependencies

<details><summary>Issue body</summary>

## Problem
The dependency surface area continues to grow, increasing security and maintenance overhead. Each new dependency adds transitive risk.

## Action Items
1. Generate dependency tree and identify unused packages
2. Consolidate overlapping functionality
3. Document justification for each major dependency
4. Establish dependency addition review criteria
5. Add dependency scanning to CI pipeline

## Success Criteria
- No unused dependencies
- Clear dependency rationale in documentation
- Automated security scanning in CI

</details>

### [MEDIUM] Architecture documentation lacks clarity on module responsibilities

The project would benefit from explicit architecture documentation that clearly defines layer boundaries, module responsibilities, and dependency flow to aid future contributors.

**GitHub issue title:** Create architecture decision records and module documentation

<details><summary>Issue body</summary>

## Problem
While the project has high quality signals, the explicit architecture documentation is minimal. New contributors cannot quickly understand module responsibilities and layer boundaries.

## Solution
1. Create `docs/architecture.md` with layer definitions
2. Add module README files in each major package
3. Document dependency flow between layers
4. Create ADRs for architectural decisions

## Deliverables
- Architecture overview diagram
- Module responsibility matrix
- Layer boundary constraints
- Example contribution patterns

</details>

### [LOW] Temporary workspace directories pollute repository root and version control

The .claude/worktrees/ directories contain duplicate audit files and planning documents that should be excluded from version control and managed separately.

**GitHub issue title:** Clean up and properly exclude development workspace directories

<details><summary>Issue body</summary>

## Problem
Temporary workspace directories (`.claude/worktrees/`) contain duplicated artifacts like `reposage-audit.json` and planning documents that clutter the repository.

## Solution
1. Add `.claude/worktrees/` to `.gitignore`
2. Move any retained artifacts to `docs/` or archive
3. Document workspace management in contributing guide

## Benefit
- Cleaner repository structure
- Reduced noise in version history
- Clearer distinction between source and ephemeral content

</details>


## Top 5 Improvements

1. **Refactor large audit output files into modular JSON segments** (effort: medium)
   The 668-line audit JSON files are identified hotspots causing review and maintenance friction. Splitting into focused modules (modules, debt, improvements, summary) directly addresses the medium-severity risk and improves code quality.

2. **Audit and rationalize the dependency set** (effort: medium)
   Growing dependency surface area is flagged as a low-risk concern with high maintenance cost. A systematic audit to remove unused dependencies, consolidate overlapping packages, and establish governance will reduce security and compatibility burden.

3. **Split test_enrichment.py into focused test modules by concern** (effort: medium)
   The 517-line test file is a coordination hotspot. Breaking it into unit, integration, and fixture modules improves test maintainability, speeds execution, and clarifies test intent.

4. **Create architecture documentation and module responsibility matrix** (effort: high)
   Despite a perfect quality score, explicit architecture documentation is minimal. Creating ADRs, layer definitions, and responsibility matrices will accelerate onboarding and guide future design decisions, aligning with the 'clarify architecture' roadmap bucket.

5. **Clean up version control by excluding temporary workspace directories** (effort: low)
   The `.claude/worktrees/` directories contain duplicate artifacts polluting the repository. Adding proper gitignore rules and archiving ephemeral content will improve repository cleanliness with minimal effort.
