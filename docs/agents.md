# AGENTS.md — RepoSage Worker Instructions

This file is read by all AI agents and Codex workers before touching any code. Follow it
exactly. No interpretation. No improvisation. No scope creep.

---

## 1. Project Overview

**RepoSage** is a deterministic, zero-dependency CLI tool that audits a Git repository and
produces a Markdown or JSON report covering file inventory, language breakdown, dependency
summary, engineering quality signals, architecture observations, and risk items.

**Package layout:**

```
src/reposage/
  __init__.py              — version string
  __main__.py              — python -m reposage entry point
  cli.py                   — Click-based CLI (report, run subcommands)
  config.py                — ScanConfig and EnrichConfig dataclasses
  models.py                — ALL shared dataclasses (FileRecord, RepoInventory,
                             DependencySummary, QualitySignals, ArchitectureSummary,
                             RiskReport, AuditReport, …)
  pipeline.py              — build_audit_report(): wires scan → analysis → report
  scan/
    filesystem.py          — walk repo tree, apply ignore policy
    languages.py           — map extensions to language names; framework signals
    repo_meta.py           — build_inventory(): aggregate FileRecords into RepoInventory
    dependencies.py        — manifest detection and dispatch
    _dep_parsers.py        — Python/JS/TS/Ruby/Go/Java/Rust manifest parsers
    _dep_parsers_dotnet.py — NuGet parsers (.csproj, packages.config, Directory.Packages.props)
    ts_analysis.py         — TypeScript code-quality signals
    ts_config.py           — tsconfig.json parsing
  analysis/
    tests.py               — detect_test_files(), _is_test_file()
    quality.py             — score_quality_signals()
    architecture.py        — summarise_architecture()
    risk.py                — analyze_risk()
  enrichment/
    provider.py            — EnrichmentProvider Protocol + enrich_report() dispatcher
    models.py              — EnrichmentResult, ModuleRole, DebtItem, Improvement dataclasses
    anthropic_provider.py  — Anthropic SDK implementation
    openai_provider.py     — OpenAI SDK implementation
    classify_prompt.py     — module-role classification prompt + JSON schema
    debt_prompt.py         — technical-debt prompt + JSON schema
    synthesis_prompt.py    — top-improvements prompt + JSON schema
  reports/
    markdown.py            — render_markdown_report()
    json_report.py         — render_json_report()
  api/
    surface.py             — API surface extraction
    _all_extractor.py      — collect all exported symbols
    _git_history.py        — git-history churn signals
    _symbol_extractor.py   — per-file symbol extraction
  security/
    scan.py                — security scan orchestration
    bandit_scan.py         — bandit integration
    eslint_scan.py         — eslint integration
    npm_audit.py           — npm audit integration
    pip_audit.py           — pip-audit integration
    ruff_scan.py           — ruff integration
    coverage_parser.py     — coverage report parsing
    _runner.py             — subprocess runner
  server/
    app.py                 — FastMCP HTTP server exposing audit_repository tool

tests/
  conftest.py              — fixture_path() helper
  fixtures/                — static repos used as scan inputs (NOT collected by pytest)
    api_repo/
    csharp_repo/
    java_gradle_repo/
    java_maven_repo/
    js_repo/
    missing_signals_repo/
    mixed_repo/
    monorepo_repo/
    python_repo/
    rust_repo/
    security/
    ts_repo/
```

**Key invariants:**
- Zero runtime dependencies. `dependencies = []` in `pyproject.toml`. Never add one.
- All shared data types live in `models.py`. Do not define dataclasses elsewhere.
- `tests/fixtures/` is excluded from pytest collection via `norecursedirs`.
- No source file in `src/reposage/` may exceed 400 lines. `tox -e linecount` enforces this.

---

## 2. How to Run Tests

**Preferred — full isolated tox run (always use this before committing):**
```bash
tox -e py312
```

**Quick iteration during development:**
```bash
python -m pytest tests/
```

**Single file:**
```bash
python -m pytest tests/test_dependencies.py -q
```

**With coverage detail:**
```bash
python -m pytest tests/ --cov=reposage --cov-report=term-missing
```

Coverage is collected automatically via `addopts` in `pyproject.toml`; you do not need to
pass `--cov` manually when using `python -m pytest`.

**Enrichment tests (requires `reposage[ai]`):**
```bash
tox -e ai
```

**MCP server tests (requires `reposage[server]`):**
```bash
tox -e server
```

**Coverage requirement:** No module may drop below its current coverage after your change.
Target ≥ 90% across all non-stub modules.

---

## 3. How to Run Linting, Type Checks, and Quality Gates

```bash
# Lint + format check
tox -e lint

# or directly:
python -m ruff check src tests
python -m ruff format --check src tests

# Type check
tox -e type

# or directly:
python -m mypy src

# Package build check
tox -e pkg

# File size check — 400-line ceiling per source file
tox -e linecount
```

**All five gates must be green before a commit:** `py312`, `lint`, `type`, `pkg`, `linecount`.

Fix every ruff and mypy violation your change introduces. Do not suppress them with
`# noqa` or `# type: ignore` unless the violation is a known false positive in an
unrelated line that pre-existed your change — and even then, do not add new suppressions.

---

## 4. Commit Conventions

- **One logical change, one commit.** Never batch multiple fixes or features.
- **Imperative mood, lowercase subject, no trailing period.**
  - Good: `fix(scan): skip url and vcs lines in _parse_requirements`
  - Bad: `Fixed parsing bug.`, `Fix two things`
- **No AI attribution lines.** No `Co-Authored-By:`, no `Generated by`, no `🤖`.
- **Prefix format:** `fix:` for bug fixes, `feat:` for features, `chore:` for housekeeping,
  `docs:` for documentation, `test:` for tests only.
- Body is optional. If included, wrap at 72 characters and explain *why*, not *what*.

---

## 5. Fix Protocol

1. Read every file you will modify before touching it.
2. Implement exactly what is described. Nothing more.
3. Add or update tests that cover the new behaviour (see section 6).
4. Run `python -m pytest tests/ -q` and confirm all tests pass.
5. Run `tox -e lint` and `tox -e linecount` — fix all new violations.
6. Commit with the correct message format.
7. Stop. Do not move on to the next task without being asked.

If the task description says "add a guard" — add the guard. If it says "delete the file" —
delete the file. Do not refactor adjacent code, rename variables, reorder imports, or add
docstrings to functions you did not change.

---

## 6. Test Requirements

- Every fix must ship with at least one test that covers the changed behaviour.
- Negative tests (asserting something is NOT in a result) are often the right choice for
  guard/filter fixes.
- Use `tmp_path: Path` (pytest built-in) for any test that needs a temp directory.
  Never create directories manually with `uuid` names and `shutil.rmtree`.
- If no test file exists for the module you are changing, create one at
  `tests/test_<module_name>.py`.
- Do not modify tests that are unrelated to your fix.
- `tests/fixtures/` is for static repo trees used as scan inputs. If a fixture repo needs
  a new file for your test, add it. Do not add binary files or cache artifacts.

---

## 7. What NOT to Do

- **No batch commits.** One logical change per commit, always.
- **No Co-Authored-By or AI attribution** of any kind in commit messages.
- **No touching files outside the stated scope.**
- **No skipping tests.** Do not use `pytest.mark.skip`, `pytest.mark.xfail`, or
  comment out assertions to make tests pass.
- **No `# type: ignore` shortcuts** to silence mypy on code you wrote.
- **No `# noqa` shortcuts** to silence ruff on code you wrote.
- **No adding runtime dependencies.** `dependencies = []` must remain empty.
- **No importing from `src/` with sys.path hacks.** The package is installed in the
  test env by tox; imports work without path manipulation.
- **No speculative improvements.** Scope is exactly what was asked.
- **No file over 400 lines.** Split by responsibility into a sibling module when a file
  approaches the limit (e.g., `_dep_parsers_dotnet.py` splits NuGet parsers from
  `_dep_parsers.py`). `tox -e linecount` will fail the build if this is violated.

---

## 8. Gate Before Merge

```bash
tox -e py312 && tox -e lint && tox -e type && tox -e pkg && tox -e linecount
```

All five must be green. Coverage must be ≥ 90% on every non-stub module.
