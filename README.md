# RepoSage

RepoSage is an AI-assisted repository analysis tool that produces a structured
technical audit of a codebase.

The emphasis is deterministic repo intelligence first, not an ungrounded
"chat with your repo" experience. The MVP scans a local repository, extracts
static signals engineers already care about, and turns those signals into a
Markdown or JSON audit report.

## Current MVP scope

- Local repository scanning
- Static file, manifest, and layout analysis
- Language and dependency summaries
- Tests, docs, CI, packaging, lint, and typing heuristics
- Architecture and hotspot guesses
- Markdown and JSON output
- Optional AI enrichment only after deterministic extraction

## Quick start

```bash
pip install reposage

# Human-readable Markdown report (stdout)
reposage run /path/to/repo

# Explicit format and file output
reposage report /path/to/repo --format markdown --output audit.md
reposage report /path/to/repo --format json --output audit.json

# With AI enrichment (module roles, debt items, top-5 improvements)
pip install 'reposage[ai]'
ANTHROPIC_API_KEY=sk-ant-... reposage report /path/to/repo --enrich
```

## Commands

```bash
reposage report PATH --format markdown
reposage report PATH --format json
reposage run PATH
```

`report` supports explicit Markdown or JSON output. `run` is a convenience alias
for the human-readable Markdown report. Pass `--output FILE` to write to a file
instead of stdout. Pass `--enrich` to add AI-generated module roles, debt items,
and top-5 improvements (requires `reposage[ai]` and `ANTHROPIC_API_KEY`).

## GitHub Action

Add RepoSage to any workflow to audit your repository on every push:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"

- uses: ricardogr07/reposage@v0.2.0
  with:
    path: .
    format: markdown
    output: reposage-report.md

- uses: actions/upload-artifact@v4
  with:
    name: reposage-report
    path: reposage-report.md
```

See [`.github/workflows/demo.yml`](.github/workflows/demo.yml) for a complete
example, and [`examples/`](examples/) for sample audit outputs.

## Development

RepoSage targets Python 3.12+ and uses Hatchling for packaging. The preferred
local workflow is `uv` for environment setup and `tox` for repeatable checks.

```bash
uv sync --dev
tox -e py312
tox -e lint
tox -e type
tox -e pkg
```

If `uv` is unavailable, install the development tools with your normal Python
environment manager or with `python -m pip install -e .[dev]`, then run the
same `tox` commands.

## Project documents

- [PLAN.md](PLAN.md): roadmap, issue backlog, PR strategy, and acceptance criteria
- [CHANGELOG.md](CHANGELOG.md): version history
- [docs/architecture.md](docs/architecture.md): package and data-flow overview
- [docs/development.md](docs/development.md): contributor workflow and quality gates
- [CONTRIBUTING.md](CONTRIBUTING.md): contribution and review expectations
- [examples/](examples/): sample audit outputs

## Status

M0 (bootstrap), M1 (deterministic audit), and M2 (AI enrichment) are complete.
M3 (productization) adds release automation, a GitHub Action wrapper, and
examples. AI enrichment remains optional and is intentionally separated from the
extraction layer.
