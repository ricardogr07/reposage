# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Nothing yet.

## [0.4.0] — 2026-07-07

### Added

- Six Standards audit mode (`reposage audit PATH`): grades a repository 0-6
  against the six standards (Reproducible, Legible, Structured, Proven, Shipped,
  Accountable), with 18 deterministic checks and an optional
  `--run-subprocess-checks` gate for checks that execute the test suite.
- `[tool.reposage.audit]` / `[audit]` config table, including an `exclude_globs`
  knob that drops fixture and example trees from the audit (they are inputs, not
  code to grade).
- `--format github` output: GitHub Actions `::error` / `::warning` / `::notice`
  workflow-command annotations, plus the Markdown grade card appended to
  `GITHUB_STEP_SUMMARY` when set.
- `action.yml` gains `mode` (report or audit), `fail-under`, and
  `run-subprocess-checks` inputs so the Action can run either mode.
- `tox -e selfaudit`: RepoSage grades its own repository against the Six
  Standards as a structural regression check. The pinned grade is 6/6.
- `secrets_exclude_globs` config knob: scopes the secret scan (tree and git
  history, via git pathspec excludes) away from paths that plant
  credential-shaped bait on purpose; the scope is announced in the grade card.
- `audit_standards` MCP tool: the server clones a remote repository at full
  depth and grades it against the Six Standards, with opt-in
  `run_subprocess_checks`. The server image installs the new `audit` extra
  (pytest, pytest-cov) so it can execute an audited repo's suite.
- DS/ML profile in the standards report: every Python file is classified as
  training / serving / pipeline / data / test, and the grade card header says
  whether the repo was profiled as data science / ML, with file counts.
- `--training-glob` / `--serving-glob` CLI flags to pin file roles when the
  classification heuristics miss.
- `ds-audit/action.yml`: a composite action tuned for DS/ML repositories
  (github-format annotations, `fail-under: 4` default, role-glob inputs).
- `.env.example` documenting every environment variable RepoSage reads.
- MCP server observability: OpenTelemetry request counter and latency
  histogram plus request-id structured logging behind the optional
  `observability` extra (no-op without it); Prometheus alert rules in
  `k8s/alerts.yaml` reference the emitted metric names.

### Changed

- The server Docker image installs frozen from the committed lockfile
  (`uv sync --frozen`) instead of resolving dependencies at build time.
- Anthropic enrichment default model is `claude-opus-4-8` (was
  `claude-haiku-4-5-20251001`); enrichment timeout raised to 60 s to match.
- `s3.suite` reports UNCERTAIN instead of a 0-collected FAIL when pytest is
  not installed in the auditing environment.
- History secret patterns now require a quoted 8+ character literal, matching
  the tree scan; a bare `token:` annotation no longer flags a commit.

## [0.3.0] — 2026-04-28

### Added

- Rust language support: Cargo.toml dependency parsing (normal / dev / build groups),
  framework detection (Tokio, Axum, Actix-web, Rocket, Diesel, SQLx, Serde, Tonic),
  quality signals, and 15 tests (M12).
- C# / .NET language support: SDK-style `.csproj`, legacy `packages.config`, and
  Central Package Management `Directory.Packages.props` parsing; NuGet ecosystem;
  framework detection (ASP.NET Core, Blazor, Entity Framework Core, .NET MAUI, gRPC,
  MassTransit, Hangfire, Dapper); static-typing signal; and 11 tests (M13).
- `.editorconfig` recognized as a lint-config file.
- `_dep_parsers_dotnet.py` module — splits NuGet parsers out of `_dep_parsers.py`
  to stay under the 400-line per-file ceiling enforced by `tox -e linecount`.
- `tox -e linecount` quality gate (`scripts/check_line_counts.py --max=400`).
- Language extensions: `.cs` (C#), `.csx` (C# Script), `.fs` (F#), `.vb` (Visual Basic).

## [0.2.0] — 2026-04-17

### Added

- Optional AI enrichment layer (`--enrich` flag, `reposage[ai]` extra) — module
  responsibility classification, technical debt labeling, and top-5 improvements
  synthesis via a single Anthropic tool-use call (RS-020 through RS-023).
- `EnrichmentProvider` Protocol and `AnthropicEnricher` implementation.
- `EnrichConfig` dataclass for tuning enrichment model, timeout, and debt item limits.
- Extended Markdown and JSON renderers to include enrichment sections when present.
- `tox -e ai` environment for enrichment-specific tests.
- GitHub Action wrapper (`action.yml`) for running RepoSage in CI workflows.
- Sample audit of this repository in `examples/`.
- Release automation workflow (tag → PyPI via trusted publisher).

### Changed

- Classifier updated from `3 - Alpha` to `4 - Beta`.

## [0.1.0] — 2026-03-01

### Added

- Initial release: deterministic repository audit pipeline (M0 + M1).
- Filesystem scanner with stable ignore policy.
- Language inventory, dependency parsing (Python + JS/TS), and layout summary.
- Quality, architecture, and risk heuristics.
- Markdown and JSON report rendering.
- CLI entry point (`reposage report`, `reposage run`).
- Full tox matrix: `lint`, `type`, `py312`, `pkg`.
