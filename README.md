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

## Supported languages

| Language | Manifest / ecosystem | Framework signals |
|---|---|---|
| Python | `pyproject.toml`, `requirements*.txt` | FastAPI, Flask, Django, Celery, … |
| JavaScript / TypeScript | `package.json` | React, Next.js, Express, Angular, Vue, … |
| Java | `pom.xml` (Maven), `build.gradle` (Gradle) | Spring Boot, Quarkus, Micronaut, … |
| Rust | `Cargo.toml` | Tokio, Axum, Actix-web, Rocket, Diesel, SQLx, Serde, … |
| C# / .NET | `.csproj`, `packages.config`, `Directory.Packages.props` | ASP.NET Core, Blazor, EF Core, .NET MAUI, gRPC, … |
| Ruby, Go, and others | quality and test signals only | — |

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

## How it works

1. **Static extraction** — scans the filesystem, parses manifests, and applies heuristics.
   No API calls, no network, no runtime dependencies.
2. **Deterministic output** — the same repo always produces the same report.
3. **Optional AI enrichment** — pass `--enrich` to add module roles, technical debt items,
   and top-5 improvements via a single Anthropic or OpenAI API call.

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

## Six Standards audit

Alongside the descriptive `report`, RepoSage has a second, opinionated mode:
`reposage audit .` grades a repository from 0 to 6 against the Six Standards of
production-grade code. A repo earns one point per standard it fully passes:

0. **Reproducible** — pinned environment, lockfile, seeded determinism.
1. **Legible** — readable structure, naming, and docstring coverage.
2. **Structured** — clear layering and externalized configuration (no secrets in source).
3. **Proven** — a real test suite that asserts behavior and gates model quality.
4. **Shipped** — a deploy path, an isolated environment, and gated CI/CD.
5. **Accountable** — meaningful history, ownership, and observability.

```bash
# Markdown grade card (stdout)
reposage audit .

# Machine-readable JSON, or GitHub Actions annotations for CI
reposage audit . --format json
reposage audit . --format github --fail-under 4

# Allow checks that shell out (runs your test suite, etc.)
reposage audit . --run-subprocess-checks
```

Configure the audit under `[tool.reposage.audit]` in `pyproject.toml` (or an
`[audit]` table in `reposage.toml`). For example, keep fixture and example trees
out of the grade:

```toml
[tool.reposage.audit]
exclude_globs = ["tests/fixtures/**", "examples/**"]
```

`--format github` emits `::error` / `::warning` / `::notice` workflow commands so
failing checks surface as inline annotations, and writes the full Markdown grade
card to the job summary when `GITHUB_STEP_SUMMARY` is set. The module layout is
described in [docs/architecture.md](docs/architecture.md).

## Data science and ML repositories

RepoSage is a general-purpose auditor, but the Six Standards engine is
DS/ML-aware. During the audit's single repository walk, every Python file is
classified into a role: `training`, `serving`, `pipeline`, `data`, `test`, or
`other`. Classification uses path tokens first (`train.py`, `serve.py`,
`pipeline/`), then imports (`torch`/`sklearn`/`xgboost` mark training code;
`fastapi`/`flask`/`mcp` mark serving code), and finally explicit config globs,
which win over both. A repo with any training or serving code, or any DS import
(`pandas`, `numpy`, `scipy`, `polars`), is profiled as data science / ML; the
grade card's header says which profile was detected.

Several checks change behavior based on those roles:

- **s0.determinism** looks for seed calls only in training and pipeline code,
  and passes with a note when no random sources exist.
- **s2.boundaries** flags raw I/O (`read_csv`, `requests.get`) only inside
  training or serving files; I/O belongs in `data` modules.
- **s3.eval_gate** requires a model-quality gate only when training code
  exists; a repo with no trained model passes with "not applicable" noted.
- **s5** (logs, metrics, alerting) reports `NOT_APPLICABLE` instead of failing
  when there is no serving or training surface to observe.

When the heuristics misclassify a file, pin its role explicitly:

```toml
[tool.reposage.audit]
serving_globs = ["src/mypkg/handlers/*.py"]
training_globs = ["src/mypkg/fit_*.py"]
# Scope the secret scan away from paths that plant credential-shaped bait
# on purpose (scanner tests, honeypots). The grade card announces the scope.
secrets_exclude_globs = ["tests/**"]
```

## GitHub Action

Add RepoSage to any workflow to audit your repository on every push:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"

- uses: ricardogr07/reposage@v0.3.0
  with:
    path: .
    format: markdown
    output: reposage-report.md

- uses: actions/upload-artifact@v4
  with:
    name: reposage-report
    path: reposage-report.md
```

For DS/ML repositories there is a dedicated action wrapping the Six Standards
audit: annotations land inline on the PR, the grade card lands in the job
summary, and the job fails below a grade floor (default 4):

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"

- uses: ricardogr07/reposage/ds-audit@main
  with:
    path: .
    fail-under: "4"
    training-globs: "src/mypkg/fit_*.py"
```

Check out with `fetch-depth: 0`; the audit's history checks are meaningless on
a shallow clone. See [`.github/workflows/demo.yml`](.github/workflows/demo.yml)
for a complete example of both actions, and [`examples/`](examples/) for sample
audit outputs.

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

- [Roadmap history](docs/plans/): milestone roadmap and acceptance criteria archives
- [CHANGELOG.md](CHANGELOG.md): version history
- [docs/architecture.md](docs/architecture.md): package and data-flow overview
- [docs/development.md](docs/development.md): contributor workflow and quality gates
- [CONTRIBUTING.md](CONTRIBUTING.md): contribution and review expectations
- [examples/](examples/): sample audit outputs

## Status

M0 (bootstrap), M1 (deterministic audit), M2 (AI enrichment), M12 (Rust support),
and M13 (C# / .NET support) are complete. AI enrichment remains optional and is
intentionally separated from the extraction layer.
