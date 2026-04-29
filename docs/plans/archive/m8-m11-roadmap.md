# RepoSage M8–M11 Roadmap

## Overview

| Milestone | Theme | Complexity |
|---|---|---|
| [M8](#m8--security--quality-aggregation) | Security & Quality Aggregation | L |
| [M9](#m9--typescript-support) | TypeScript Support | M |
| [M10](#m10--java-language-support) | Java Language Support | M |
| [M11](#m11--api-surface-analysis) | API Surface Analysis | XL |

Rust and C# language support are planned as M12 and M13 — see [m12-m13-roadmap.md](m12-m13-roadmap.md).

---

## M8 — Security & Quality Aggregation

**Complexity: L**

**Goal:** Elevate RepoSage from structure-inferring scanner to an actual security and quality gate. External tools (pip-audit, bandit, npm audit, ruff, eslint) are called as subprocesses when available, or their pre-existing output files are parsed when found on disk (e.g., from CI artifacts). All findings are advisory — they never block the audit or return non-zero.

### New Models

```python
@dataclass(slots=True)
class VulnerabilityFinding:
    package: str
    ecosystem: str          # "python" | "npm"
    severity: str           # "critical" | "high" | "medium" | "low"
    cve: str                # CVE ID or advisory ID
    affected_version: str
    fix_version: str        # "" if no fix available

@dataclass(slots=True)
class LintSummary:
    tool: str               # "ruff" | "eslint" | "bandit"
    error_count: int
    warning_count: int
    top_categories: list[str]

@dataclass(slots=True)
class SecuritySummary:
    vulnerabilities: list[VulnerabilityFinding] = field(default_factory=list)
    lint_summaries: list[LintSummary] = field(default_factory=list)
    coverage_percent: float | None = None
    coverage_source: str = ""   # "coverage.xml" | "lcov" | ""
    tools_run: list[str] = field(default_factory=list)
    tools_skipped: list[str] = field(default_factory=list)
```

`SecuritySummary` is added as an optional field to `AuditReport` (defaults to `None` unless `--security` is passed).

### Implementation Steps

#### Step 1 — Subprocess runner utility: `src/reposage/security/_runner.py`
- `run_tool(cmd: list[str], timeout: int = 30) -> str | None`
- Returns stdout on success, `None` if tool not found (`FileNotFoundError`) or times out
- Caller logs skipped tools; runner itself is silent

#### Step 2 — pip-audit integration: `src/reposage/security/pip_audit.py`
- Try subprocess: `pip-audit --format json -r <requirements or pyproject>`
- Fallback: look for `pip-audit-report.json` in repo root
- Parse JSON → `list[VulnerabilityFinding]` (ecosystem="python")

#### Step 3 — npm audit integration: `src/reposage/security/npm_audit.py`
- Try subprocess: `npm audit --json` in each directory containing `package.json`
- Fallback: look for `npm-audit.json` in repo root
- Parse JSON → `list[VulnerabilityFinding]` (ecosystem="npm")

#### Step 4 — bandit integration: `src/reposage/security/bandit_scan.py`
- Try subprocess: `bandit -r <src_dir> -f json`
- Fallback: look for `bandit-report.json` in repo root
- Parse JSON → `LintSummary(tool="bandit", ...)`

#### Step 5 — Coverage parsing: `src/reposage/security/coverage_parser.py`
- Check for `coverage.xml` → parse with `xml.etree.ElementTree` (stdlib) → line-rate %
- Check for `lcov.info` → parse text format → lines hit / lines found
- Check for `.coverage` (Python binary) → skip (not parseable without coverage.py)
- Returns `(float | None, str)` — percent and source name

#### Step 6 — Ruff output parsing: `src/reposage/security/ruff_scan.py`
- Try subprocess: `ruff check <root> --output-format json`
- Fallback: look for `ruff-report.json` in repo root
- Parse JSON → `LintSummary(tool="ruff", ...)`
- Top categories derived from rule prefixes (E=pycodestyle, F=pyflakes, S=security, etc.)

#### Step 7 — ESLint output parsing: `src/reposage/security/eslint_scan.py`
- Try subprocess: `eslint . --format json`
- Fallback: look for `eslint-report.json` in repo root
- Parse JSON → `LintSummary(tool="eslint", ...)`

#### Step 8 — Orchestrator: `src/reposage/security/scan.py`
- `scan_security(root: Path, file_records: list[FileRecord]) -> SecuritySummary`
- Decides which tools to run based on detected ecosystems
- Collects results into `SecuritySummary`
- Always completes — no tool failure can raise

#### Step 9 — CLI flag: `--security`
- Add `--security` to `report` and `run` subparsers
- When set: call `scan_security(root, file_records)` and attach result to `AuditReport`
- Pass `file_records` through from pipeline (currently discarded after `build_audit_report`)

#### Step 10 — Renderers
- **Markdown:** new `## Security & Quality` section with vulnerability table and coverage line
- **JSON:** `security` key in output (or `null` if not run)
- **Agent brief:** vulnerability tasks become `[vuln/critical]` in task list; coverage gap becomes `[signal]`

#### Step 11 — Tests
- Unit tests per parser with fixture JSON files in `tests/fixtures/security/`
- Integration test: scan a fixture repo with a pre-existing `pip-audit-report.json`
- CLI test: `--security` flag produces `SecuritySummary` in output

### New File Layout

```
src/reposage/security/
    __init__.py
    _runner.py          # subprocess helper (~30 lines)
    pip_audit.py        # (~50 lines)
    npm_audit.py        # (~50 lines)
    bandit_scan.py      # (~40 lines)
    coverage_parser.py  # (~60 lines)
    ruff_scan.py        # (~50 lines)
    eslint_scan.py      # (~50 lines)
    scan.py             # orchestrator (~80 lines)
```

---

## M9 — TypeScript Support

**Complexity: M**

**Goal:** Extend RepoSage to understand TypeScript projects deeply — not just detect `tsconfig.json` but parse strictness settings and perform lightweight code analysis to flag `any` usage, missing return types, and missing type exports.

### Scope

- `tsconfig.json` parsing → strictness quality signals
- TS code heuristic analysis → `any` usage count, untyped exports
- TS framework detection improvements (Angular, NestJS, Deno, Bun)
- Advisory rules with explanations (why each setting matters)
- Strictness flags feed into quality score

### Implementation Steps

#### Step 1 — `tsconfig.json` parser: `src/reposage/scan/ts_config.py`
- `parse_tsconfig(path: Path) -> TSConfig`
- New model:
  ```python
  @dataclass(slots=True)
  class TSConfig:
      strict: bool = False
      no_implicit_any: bool = False
      strict_null_checks: bool = False
      no_unchecked_indexed_access: bool = False
      target: str = ""        # "ES2020", "ESNext", etc.
      module: str = ""
      path_aliases: bool = False   # True if "paths" key present
  ```
- Handles `extends` chain (follow one level; skip network paths)
- Advisory rules with rationale:

  | Flag | Missing advisory |
  |---|---|
  | `strict` | Enables 8 sub-checks; missing allows silent type holes |
  | `strictNullChecks` | Without this, `null` and `undefined` are assignable to any type |
  | `noImplicitAny` | Allows untyped parameters — largest source of TS runtime errors |
  | `noUncheckedIndexedAccess` | Array index access can be `undefined`; this makes it explicit |

#### Step 2 — TS code heuristic analysis: `src/reposage/scan/ts_analysis.py`
- `analyze_typescript(root: Path, ts_files: list[FileRecord]) -> TSCodeSignals`
- New model:
  ```python
  @dataclass(slots=True)
  class TSCodeSignals:
      any_usage_count: int = 0        # occurrences of `: any` or `as any`
      untyped_exports: int = 0        # exported functions without return type annotation
      type_assertion_count: int = 0   # occurrences of `as SomeType` (excluding `as any`)
  ```
- Implementation: regex scan over `.ts` / `.tsx` files (no AST parser needed)
  - `any_usage_count`: count `:\s*any\b` and `as\s+any\b`
  - `untyped_exports`: count `export (async )?function \w+\(` without `):\s*\w`
  - `type_assertion_count`: count `\) as (?!any)\w`

#### Step 3 — Framework detection improvements: `src/reposage/scan/repo_meta.py`
- Add signals: `@angular/core` → Angular, `@nestjs/core` → NestJS, `deno` in `tsconfig.json` → Deno
- Bun: check for `bun.lockb` in top-level entries

#### Step 4 — Quality score integration: `src/reposage/analysis/quality.py`
- TS strictness flags contribute to `QualitySignals.score`
- Suggested weight: strict=+5, noImplicitAny=+3, strictNullChecks=+3 (capped at existing max)
- Missing flags append to `quality.missing_signals` with rationale strings

#### Step 5 — `TSConfig` and `TSCodeSignals` in `AuditReport`
- Both added as optional fields (populated only when TS files detected)
- Serialized in JSON renderer as `ts_config` and `ts_analysis` keys

#### Step 6 — Tests
- `tests/fixtures/ts_repo/` fixture with `tsconfig.json` and sample `.ts` files
- Unit tests for config parsing (strict=true propagation, extends chain)
- Unit tests for `any` detection (true positives and negatives)
- Integration test via `build_audit_report(fixture_path("ts_repo"))`

---

## M10 — Java Language Support

**Complexity: M**

**Goal:** Add full Java project understanding — Maven (`pom.xml`) and Gradle (`build.gradle`, `build.gradle.kts`) dependency parsing, Java framework detection, and Java-specific quality signals. Establishes the pattern for subsequent language milestones (Rust, C#).

### Implementation Steps

#### Step 1 — Maven parser: `src/reposage/scan/_dep_parsers.py` (extend existing)
- `_parse_pom_xml(path: Path, relative_path: str) -> list[Dependency]`
- Parse with `xml.etree.ElementTree` (stdlib)
- Extract `<dependency>` entries from `<dependencies>` and `<dependencyManagement>`
- Map `<scope>` → `group`: `compile`→`runtime`, `test`→`test`, `provided`→`provided`
- Ecosystem: `"maven"` (groupId:artifactId format for `name`)

#### Step 2 — Gradle parser: `src/reposage/scan/_dep_parsers.py` (extend existing)
- `_parse_build_gradle(path: Path, relative_path: str) -> list[Dependency]`
- Regex-based (no Groovy/Kotlin parser needed for dependency extraction)
- Patterns to match:
  ```
  implementation 'group:artifact:version'
  implementation("group:artifact:version")
  testImplementation 'group:artifact:version'
  ```
- Also handle `libs.versions.toml` (Gradle version catalog) if present in same dir
- Map configuration name → group: `implementation`→`runtime`, `testImplementation`→`test`, `api`→`api`

#### Step 3 — Manifest detection: `src/reposage/scan/dependencies.py`
- Extend `_is_supported_manifest` to include `pom.xml`, `build.gradle`, `build.gradle.kts`
- Add dispatch in `summarize_dependencies`

#### Step 4 — Java quality signals: `src/reposage/analysis/quality.py`
- Test detection: `src/test/` directory or files matching `*Test.java`, `*Spec.java`
- Lint detection: `checkstyle.xml`, `pmd.xml`, `.spotbugs.xml`
- Typing: Java is statically typed — always set `typing_present=True` when Java detected

#### Step 5 — Java framework detection: `src/reposage/scan/repo_meta.py`
- Spring Boot: `org.springframework.boot` in deps
- Quarkus: `io.quarkus` in deps
- Micronaut: `io.micronaut` in deps
- Jakarta EE: `jakarta.*` in deps

#### Step 6 — Language detection: `src/reposage/scan/languages.py`
- Ensure `.java` files are counted under language `"Java"`

#### Step 7 — Fixture and tests
- `tests/fixtures/java_maven_repo/` — minimal project with `pom.xml`
- `tests/fixtures/java_gradle_repo/` — minimal project with `build.gradle`
- Tests: dependency names, groups, framework detection, quality signals

---

## M11 — API Surface Analysis

**Complexity: XL**

**Goal:** Detect the public API surface of a Python repository, identify undocumented or untyped public symbols, and use git history to flag breaking changes (symbols removed between commits). Requires `libcst` as an optional dep and a git repository.

### New Models

```python
@dataclass(slots=True)
class PublicSymbol:
    name: str
    kind: str           # "function" | "class" | "constant"
    module: str         # dotted module path
    has_docstring: bool
    has_type_annotations: bool
    exported_via_all: bool      # appears in __all__

@dataclass(slots=True)
class RemovedSymbol:
    name: str
    module: str
    last_seen_commit: str   # short SHA

@dataclass(slots=True)
class APISurface:
    public_symbols: list[PublicSymbol] = field(default_factory=list)
    removed_symbols: list[RemovedSymbol] = field(default_factory=list)
    undocumented_count: int = 0
    untyped_count: int = 0
    breaking_changes: list[RemovedSymbol] = field(default_factory=list)
```

`APISurface` added as optional field to `AuditReport`.

### Public API Definition

A symbol is **public** if it satisfies **any** of:
1. Listed in `__all__` in its module
2. Has no leading underscore AND is defined at module top-level
3. Is imported and re-exported from a package `__init__.py`

All three signals are tracked per symbol for nuance.

### Implementation Steps

#### Step 1 — Optional dependency
- Add `[project.optional-dependencies].api = ["libcst>=1.0"]` to `pyproject.toml`
- Add `[testenv:api]` to `tox.ini` (mirrors `[testenv:ai]` pattern)
- Guard import: `try: import libcst except ImportError: raise ImportError("pip install reposage[api]")`

#### Step 2 — `__all__` extractor: `src/reposage/api/_all_extractor.py`
- Uses `libcst` to parse each `__init__.py` and extract `__all__` list values
- Returns `dict[str, set[str]]` — module path → set of exported names

#### Step 3 — Public symbol extractor: `src/reposage/api/_symbol_extractor.py`
- `extract_public_symbols(root: Path, python_files: list[FileRecord]) -> list[PublicSymbol]`
- Uses `libcst` CST visitor to collect:
  - Top-level `FunctionDef`, `ClassDef`, `Assign` / `AnnAssign`
  - Check name for underscore prefix
  - Check docstring presence (first statement is `SimpleStatementLine` with `Expr(ConcatenatedString | SimpleString)`)
  - Check return annotation presence (for functions)
  - Cross-reference with `__all__` map from Step 2

#### Step 4 — Git history integration: `src/reposage/api/_git_history.py`
- `get_removed_symbols(root: Path, depth: int = 50) -> list[RemovedSymbol]`
- Strategy:
  1. Run `git log --oneline -<depth>` to get recent SHAs
  2. For each SHA, run `git show <sha>:<module_path>` for each Python module
  3. Extract public symbols from each historical snapshot using stdlib `ast` (not libcst — speed)
  4. Diff current symbol set against historical: any symbol present in history but absent now is a `RemovedSymbol`
- `depth` configurable via `--api-depth N` CLI flag (default 50 commits)

#### Step 5 — Breaking change classification
- A `RemovedSymbol` becomes a `breaking_change` if:
  - It was in `__all__` or exported from `__init__.py` in any historical snapshot
  - It is absent from the current snapshot
- Symbols removed only from internal modules (no `__all__`, underscore prefix) are not breaking

#### Step 6 — Orchestrator: `src/reposage/api/surface.py`
- `analyze_api_surface(root: Path, file_records: list[FileRecord]) -> APISurface | None`
- Returns `None` if not a git repo or libcst not installed (graceful degradation)
- Requires `--api-surface` CLI flag to run (expensive operation)

#### Step 7 — CLI flag: `--api-surface`
- Add to `report` and `run` subparsers
- Validate git repo presence before running
- Pass result to renderers

#### Step 8 — Renderers
- **Markdown:** new `## API Surface` section — table of public symbols with docstring/type badges, breaking changes as `⚠️ BREAKING` list
- **JSON:** `api_surface` key (or `null`)
- **Agent brief:** breaking changes become `[breaking/high]` tasks; undocumented symbols become `[signal]` tasks

#### Step 9 — Tests (`tox -e api`)
- `tests/fixtures/api_repo/` — a Python package with `__all__`, mix of typed/untyped, with/without docstrings
- Unit tests for `__all__` extraction, symbol detection, docstring/annotation checks
- Git history test: create a temp git repo, commit a symbol, remove it, verify detection
- Integration test: `build_audit_report` + `analyze_api_surface` on `api_repo` fixture

### New File Layout

```
src/reposage/api/
    __init__.py
    _all_extractor.py       # __all__ parsing via libcst (~60 lines)
    _symbol_extractor.py    # public symbol extraction via libcst (~120 lines)
    _git_history.py         # git log + snapshot diff (~90 lines)
    surface.py              # orchestrator (~70 lines)
```

---

## Shared Patterns Across All Milestones

- **All findings are advisory.** No milestone causes a non-zero exit for content findings.
- **All new analysis modules are optional.** Guarded by CLI flags; absent tools are listed in `tools_skipped`.
- **400-line limit applies.** If a module approaches the limit, split it before merging.
- **Each milestone ships with:** new models, parsers, tests, renderer updates, and tox env if new optional dep.
- **Fixture-first testing.** Each milestone adds at least one new fixture repo under `tests/fixtures/`.

## Verification Per Milestone

```bash
# M8
pytest tests/test_security*.py -v
tox -e lint && tox -e linecount
python -m reposage report . --security --format json | jq .security

# M9
pytest tests/test_ts*.py -v
python -m reposage report tests/fixtures/ts_repo --format json | jq .ts_config

# M10
pytest tests/test_java*.py -v
python -m reposage report tests/fixtures/java_maven_repo --format json | jq .dependencies

# M11
tox -e api
python -m reposage report . --api-surface --format json | jq .api_surface
```
