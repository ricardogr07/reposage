# Architecture

RepoSage is a deterministic repository-audit pipeline with an optional AI enrichment
layer. The deterministic core has zero runtime dependencies; AI providers are optional
extras loaded only when requested.

---

## Package Layout

```
src/reposage/
├── models.py          — shared dataclass tree (AuditReport and all sub-types)
├── config.py          — frozen config dataclasses (ScanConfig, EnrichConfig)
├── pipeline.py        — top-level orchestrator: build_audit_report()
├── cli.py             — command-line interface (report / run sub-commands)
├── scan/
│   ├── filesystem.py  — recursive file walk with stable ignore policy
│   ├── languages.py   — language and framework signal detection
│   ├── dependencies.py    — manifest detection and dispatch
│   ├── _dep_parsers.py    — Python/JS/TS/Ruby/Go/Java/Rust manifest parsers
│   ├── _dep_parsers_dotnet.py — NuGet parsers (.csproj, packages.config, Directory.Packages.props)
│   └── repo_meta.py       — project name, VCS metadata
├── analysis/
│   ├── architecture.py— main-module detection, layer guesses, god-module heuristics
│   ├── quality.py     — engineering-quality checklist and score
│   ├── risk.py        — risk hotspot synthesis
│   └── tests.py       — test-file detection helpers
├── enrichment/
│   ├── provider.py    — EnrichmentProvider Protocol + enrich_report() dispatcher
│   ├── models.py      — EnrichmentResult, ModuleRole, DebtItem, Improvement dataclasses
│   ├── anthropic_provider.py — Anthropic SDK implementation (claude-haiku default)
│   ├── openai_provider.py    — OpenAI SDK implementation (gpt-4o-mini default)
│   ├── classify_prompt.py    — module-role classification prompt + JSON schema
│   ├── debt_prompt.py        — technical-debt prompt + JSON schema
│   └── synthesis_prompt.py   — top-improvements prompt + JSON schema
├── standards/
│   ├── models.py      — CheckResult / StandardResult / StandardsReport dataclasses
│   ├── config.py      — StandardsConfig + [tool.reposage.audit] loader (exclude_globs, thresholds)
│   ├── context.py     — one filesystem walk + AST parse + role classification, shared by all checks
│   ├── pipeline.py    — build_standards_report(): runs the six evaluators, computes the 0-6 grade
│   ├── s0_reproducible.py … s5_accountable.py — the six standards' checks
│   ├── _secrets.py    — credential detection for s2 (tree, git history, .env)
│   ├── _subproc.py    — subprocess helper with a hard timeout
│   └── _cli.py        — the `audit` subcommand handler
├── reports/
│   ├── markdown.py    — Markdown renderer (with optional enrichment sections)
│   ├── json_report.py — JSON renderer (with optional enrichment key)
│   ├── standards_markdown.py — Markdown grade card for the Six Standards audit
│   ├── standards_json.py     — JSON rendering of the Six Standards audit
│   └── standards_github.py   — GitHub Actions workflow-command annotations for the audit
└── server/
    └── app.py         — FastMCP HTTP server exposing audit_repository tool
```

---

## Data Flow

```
Input: filesystem path (CLI / MCP tool)
          │
          ▼
   pipeline.build_audit_report(root)
          │
          ├── scan.filesystem   → FileRecord list
          ├── scan.languages    → LanguageBreakdown, FrameworkSignals
          ├── scan.dependencies → DependencySummary
          ├── scan.repo_meta    → project name, VCS info
          │
          ├── analysis.architecture → ArchitectureGuess
          ├── analysis.quality      → QualitySignals, quality score
          └── analysis.risk         → RiskReport
          │
          ▼
     AuditReport  (immutable dataclass tree)
          │
          ├── [optional] enrichment.provider.enrich_report(report, provider)
          │       └── AnthropicEnricher / OpenAIEnricher
          │               └── EnrichmentResult
          │
          ▼
   reports.markdown.render_markdown_report(report, enrichment?)
   reports.json_report.render_json_report(report, enrichment?)
          │
          ▼
   Output: string (Markdown or JSON)
```

---

## Key Data Models

All models live in `reposage/models.py` and use `@dataclass(slots=True)` for
immutability and low overhead. The top-level type is:

```
AuditReport
├── inventory: RepoInventory       (files, languages, manifests, project name)
├── architecture: ArchitectureGuess (modules, layers, hotspots, god-module candidates)
├── quality: QualitySignals        (checklist items, score 0–100)
├── risk: RiskReport               (risk hotspots with severity and suggested actions)
└── dependencies: DependencySummary (parsed deps, ecosystems, counts)
```

Enrichment results are a separate tree in `reposage/enrichment/models.py`:

```
EnrichmentResult
├── module_roles: list[ModuleRole]   (module → layer + responsibility)
├── debt_items:   list[DebtItem]     (title, severity, GitHub issue draft)
├── top_improvements: list[Improvement] (ranked, with effort estimate)
└── model_id: str                    (which model produced the result)
```

---

## Design Constraints

1. **Zero runtime dependencies** — `src/reposage/` imports only the standard library
   at the top level. `anthropic`, `openai`, `mcp`, and `uvicorn` are optional extras
   gated behind lazy imports inside their respective modules.

2. **Deterministic outputs** — given the same repository state, the same Markdown or
   JSON report must be produced on every run. No timestamps, random IDs, or
   non-deterministic ordering in the core pipeline.

3. **Strongly-typed model boundary** — scan and analysis results are communicated
   through the `AuditReport` dataclass tree, not loose dicts. This makes the boundary
   between extraction and rendering explicit and refactorable.

4. **Provider-agnostic enrichment** — `EnrichmentProvider` is a structural `Protocol`.
   Any class with an `enrich(report: AuditReport) -> EnrichmentResult` method satisfies
   it without inheriting from a base class.

5. **Isolation by extra** — the `ai` extra installs Anthropic and OpenAI SDKs; the
   `server` extra installs MCP and uvicorn. Neither extra is required for the CLI or
   the base audit pipeline.

6. **400-line per-file ceiling** — no source file in `src/reposage/` may exceed 400 lines.
   Enforced by `tox -e linecount` (`scripts/check_line_counts.py`). When a file approaches
   the limit, split it by responsibility into a sibling module.

---

## Layer Boundaries

| Layer | Modules | Allowed runtime dependencies |
|---|---|---|
| domain | `scan/`, `analysis/`, `models.py` | stdlib only |
| application | `pipeline.py`, `cli.py` | domain |
| presentation | `reports/` | domain, application |
| enrichment | `enrichment/` | domain; `anthropic` / `openai` via lazy import |
| infrastructure | `server/`, `api/`, `security/` | all layers; `mcp` / `uvicorn` via lazy import |

The domain layer must never import from enrichment or infrastructure. This keeps the
core audit pipeline runnable without any optional extras installed.

---

## Extension Points

### Adding a new dependency scanner (e.g., Go modules, Swift)

Cargo (M12) and NuGet (M13) are already implemented as examples of this pattern.

1. If the new parsers will push `_dep_parsers.py` past 400 lines, create a sibling file
   (e.g., `_dep_parsers_go.py`) and add parsers there.
2. Add a `_parse_<ecosystem>(path, relative_path)` function returning `list[Dependency]`.
3. Add the manifest filename constant in `dependencies.py` (e.g., `_GO_MOD = "go.mod"`).
4. Extend `_is_supported_manifest()` to recognise the new filename.
5. Add an `elif` branch in the dispatch block inside `summarize_dependencies()`.

### Adding a new enrichment provider (e.g., Google Gemini)

1. Create `src/reposage/enrichment/gemini_provider.py` with a `GeminiEnricher` class.
2. Implement `enrich(self, report: AuditReport) -> EnrichmentResult` using the same
   three prompts from `classify_prompt`, `debt_prompt`, and `synthesis_prompt`.
3. Reuse `_parse_result()` from `anthropic_provider.py` — it is provider-agnostic.
4. Add `"gemini"` to the `enrich_provider` dispatch block in `server/app.py` and
   extend the `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` pattern for `GEMINI_API_KEY`.
5. Add the SDK to the `ai` extra in `pyproject.toml`.

### Adding a new report format (e.g., HTML, SARIF)

1. Create `src/reposage/reports/html.py` (or `sarif.py`) with a
   `render_html_report(report, enrichment=None)` function.
2. Add a `--format html` branch in `src/reposage/cli.py`.
3. If exposing via MCP, add a `format` parameter to `audit_repository` in `server/app.py`.

---

## Testing Strategy

Tests are split by the extras they require:

| Command | What it tests | Extras needed |
|---|---|---|
| `pytest tests/` | Core pipeline, scan, analysis, models, CLI | none |
| `tox -e ai` | Enrichment providers (mocked SDK), prompts, renderers | `ai` |
| `tox -e server` | MCP server HTTP layer, `_clone`, URL validation | `server` |
| `tox -e lint` | Ruff lint + format check | none |
| `tox -e type` | mypy static analysis of `src/` | none |
| `tox -e linecount` | Enforces max 400 lines per source file | none |

Shared pytest fixtures live in `tests/conftest.py`. Fixture repositories for
integration-style tests are under `tests/fixtures/`.

The enrichment tests use mocked SDK modules (`patch.dict(sys.modules, ...)`) so they
never make real API calls and run without credentials.

---

## MCP Server

`reposage.server.app` exposes one MCP tool: `audit_repository`. It:

1. Validates the HTTPS URL (rejects embedded credentials, non-https schemes).
2. Resolves the auth token: `token` parameter → `GITHUB_TOKEN` env var → `None`.
3. Clones the repo with `git -c http.extraheader=Authorization: Basic <b64>` (token
   never embedded in the URL).
4. Calls `pipeline.build_audit_report()` then optionally `enrich_report()`.
5. Cleans up the temp clone on exit.

The server is a stateless FastMCP HTTP app (`stateless_http=True`), safe for
horizontal scaling. The Kubernetes deployment runs 2 replicas with HPA up to 10.
