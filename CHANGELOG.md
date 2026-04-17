# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
