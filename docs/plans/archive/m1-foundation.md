# RepoSage Delivery Plan

## Product thesis

RepoSage should generate a structured technical audit of a repository. The core
output is a useful engineering artifact, not a conversational toy.

## Frozen MVP scope

### In scope

- Local repository scanning
- Static file and manifest analysis
- Easy dependency parsing for Python and JS/TS manifests
- Heuristics for tests, docs, CI, packaging, lint, and type coverage
- Markdown report generation
- Minimal machine-readable JSON output
- Optional AI enrichment layered on extracted signals

### Out of scope

- IDE plugin work
- PR review bots
- Code rewriting
- Semantic search UI
- Graph or distributed system infrastructure
- Deep monorepo guarantees

## Milestones

### M0 Bootstrap ✅ COMPLETE

- `RS-001`: package scaffold and shared models
- `RS-002`: tox, pytest, Ruff, mypy, and packaging baseline
- `RS-003`: CI workflow and branch protection contract
- `RS-004`: planning, README, contributor docs, and MIT license
- `RS-005`: GitHub templates, labels, milestones, and review guidance

### M1 Deterministic audit ✅ COMPLETE

- `RS-010`: filesystem scanner and ignore policy
- `RS-011`: language inventory and repo layout summary
- `RS-012`: Python and JS/TS dependency parsing
- `RS-013`: tests/docs/CI/packaging/lint/type heuristics
- `RS-014`: architecture and hotspot heuristics
- `RS-015`: Markdown report generation
- `RS-016`: JSON serialization
- `RS-017`: CLI orchestration and end-to-end fixtures

### M2 AI enrichment

- `RS-020`: provider-agnostic enrichment boundary
- `RS-021`: module responsibility classification
- `RS-022`: debt labeling and issue draft generation
- `RS-023`: top-five improvements synthesis

### M3 Productization

- `RS-030`: GitHub Action wrapper
- `RS-031`: sample audit on a real repository
- `RS-032`: screenshots and examples
- `RS-033`: release hardening

## Current status

| Milestone | Status | Notes |
| --- | --- | --- |
| M0 Bootstrap | ✅ Complete | Merged via PR #1 (`chore/bootstrap-public-foundation`) |
| M1 Deterministic Audit | ✅ Complete | Shipped with PR #1; all PLAN_FIX defects resolved |
| M2 AI Enrichment | 🔜 Ready to start | Branch: `feature/ai-enrichment-provider` |
| M3 Productization | ⏳ Pending | Depends on M2 |

## Working backlog

| Issue | Milestone | Status | Outcome |
| --- | --- | --- | --- |
| `RS-001` | M0 | Done | Create `src/` package, CLI entry point, models, and baseline package metadata |
| `RS-002` | M0 | Done | Add `tox`, `pytest`, `ruff`, `mypy`, coverage, and build validation |
| `RS-003` | M0 | Done | Add GitHub Actions CI and document required checks |
| `RS-004` | M0 | Done | Freeze scope and contributor guidance in core docs |
| `RS-005` | M0 | Done | Add issue templates, PR template, label spec, and milestone spec |
| `RS-010` | M1 | Done | Walk repositories with stable ignore rules and collect file metadata |
| `RS-011` | M1 | Done | Produce language, framework, and file layout summaries |
| `RS-012` | M1 | Done | Parse `pyproject.toml`, `requirements*.txt`, and `package.json` manifests |
| `RS-013` | M1 | Done | Evaluate tests, docs, CI, packaging, lint, and type coverage signals |
| `RS-014` | M1 | Done | Flag likely layers, hotspots, and god modules |
| `RS-015` | M1 | Done | Render deterministic Markdown reports |
| `RS-016` | M1 | Done | Emit JSON output from the same audit model |
| `RS-017` | M1 | Done | Cover core behavior with fixture-based tests and CLI checks |
| `RS-020` | M2 | Ready | Add enrichment provider interface without coupling extraction to one vendor |
| `RS-021` | M2 | Ready | Classify module responsibilities from extracted metadata |
| `RS-022` | M2 | Ready | Draft issue suggestions and debt labels |
| `RS-023` | M2 | Ready | Rank the top five next improvements |
| `RS-030` | M3 | Pending | Package RepoSage for GitHub Action use |
| `RS-031` | M3 | Pending | Publish an example audit against a reference repo |
| `RS-032` | M3 | Pending | Add screenshots and user-facing examples |
| `RS-033` | M3 | Pending | Harden release automation and packaging quality |

## PR strategy

### Bootstrap PR ✅ Merged

- Branch: `chore/bootstrap-public-foundation` → merged as PR #1
- Title: `Bootstrap RepoSage public package foundation`
- Contained: full M0 scaffold + M1 implementation + all PLAN_FIX fixes

### M2 PR

- Branch: `feature/ai-enrichment-provider`
- Goal: provider-agnostic enrichment boundary, module classification, debt labeling, top-5 synthesis (RS-020 through RS-023)

## GitHub working rules

- Branch from `main`
- Keep branches short-lived and scoped to one issue after bootstrap
- Open draft PRs early
- Use squash merge after approval
- Require `lint`, `type`, `py312`, and `pkg` checks before merge

## Labels and milestones

### Labels

- `type:feature`
- `type:bug`
- `type:chore`
- `type:docs`
- `type:test`
- `area:scan`
- `area:analysis`
- `area:reports`
- `area:cli`
- `area:ci`
- `priority:p0`
- `priority:p1`
- `priority:p2`
- `status:blocked`
- `status:ready`
- `good first issue`

### Milestones

- `M0 Bootstrap`
- `M1 Deterministic Audit`
- `M2 AI Enrichment`
- `M3 Productization`

## Validation matrix

- `uv sync --dev`
- `tox -e py312`
- `tox -e lint`
- `tox -e type`
- `tox -e pkg`

## Sprint 1 acceptance criteria

- RepoSage scans a local repository and builds a deterministic audit model
- RepoSage emits Markdown and JSON output from the same underlying data
- Report sections include project summary, architecture guess, quality checklist,
  risk hotspots, and recommended next issues
- Fixture-based tests cover positive and negative heuristics
- CI enforces the documented checks

