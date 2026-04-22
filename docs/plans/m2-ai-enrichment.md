# M2 AI Enrichment — Delivery Plan

**Status:** Approved for implementation  
**Branch:** `feature/ai-enrichment-provider`  
**Base:** `main` (M0 + M1 complete, PR #1 merged)  
**Issues:** RS-020 → RS-023

---

## Context

M1 produced a fully deterministic `AuditReport` from static analysis. M2 layers optional
AI enrichment on top of that report — without modifying the core pipeline or breaking any
existing contract. The result is an `EnrichmentResult` that consumers can attach to an
`AuditReport` if enrichment was requested. Callers that do not pass `--enrich` are
completely unaffected.

---

## Critic findings (applied to this plan)

### Hard constraints

1. **Lazy imports are mandatory.** `anthropic_provider.py` must not import `anthropic` at
   module load time. Use a `try/except ImportError` guard or import inside the method body.
   `ImportError` on a missing optional dep would break every CLI user who did not install
   the `[ai]` extras.

2. **One `enrich()` method, not three.** RS-020 requires a provider-agnostic interface.
   The minimal form is one method: `enrich(report: AuditReport) -> EnrichmentResult`.
   A method per RS issue (classify, label_debt, synthesize) is a premature split for a
   single concrete implementation. Refactor into per-method Protocol only if a second
   provider with different partial capabilities is ever added.

3. **Single LLM call with structured output.** RS-021/022/023 map to three *fields* in
   `EnrichmentResult`, not three separate API calls. Use Anthropic tool-use JSON schema
   to capture all three in one round-trip. This cuts latency, cost, and failure surface.

4. **mypy with optional dep.** Wrap SDK types behind `TYPE_CHECKING` to avoid mypy
   failing when `anthropic` stubs are absent in the base tox environment. Add a separate
   `tox -e ai` environment that installs `[ai]` extras and runs the enrichment tests.

5. **--enrich must fail loudly.** If `--enrich` is passed but `ANTHROPIC_API_KEY` is
   absent, exit with a clear error. Silent skip is confusing.

### Flagged (non-blocking)

- **Protocol for one provider is YAGNI.** RS-020 requires it by spec, so it ships. But
  do not add a second concrete provider until there is a real second provider. Keep the
  Protocol minimal: one method, one return type.

- **Use claude-haiku-4-5-20251001** for all enrichment calls during M2. Cheapest,
  fastest, sufficient for structured JSON extraction. The model can be overridden by
  `EnrichConfig` later.

- **Do not modify `AuditReport`.** It is `slots=True` and the stable M1 contract. All
  M2 output lives in `EnrichmentResult`. Renderers accept both and combine at output time.

---

## Module layout

```
src/reposage/
├── enrichment/
│   ├── __init__.py          # exports: EnrichmentProvider, EnrichmentResult, enrich_report
│   ├── provider.py          # Protocol + enrich_report() dispatcher
│   ├── models.py            # EnrichmentResult, ModuleRole, DebtItem, Improvement
│   ├── prompts.py           # prompt + JSON schema builders (pure functions, no SDK dep)
│   └── anthropic_provider.py  # AnthropicEnricher (lazy import of anthropic SDK)
```

No changes to `scan/`, `analysis/`, `pipeline.py`, or existing `models.py`.  
Additive changes to `cli.py`, `reports/markdown.py`, `reports/json_report.py`.

---

## Data contracts

```python
# src/reposage/enrichment/models.py

@dataclass(slots=True)
class ModuleRole:
    module: str          # e.g. "src/reposage/scan"
    responsibility: str  # one sentence from AI
    layer: str           # "infrastructure" | "domain" | "presentation" | "test" | "tooling"

@dataclass(slots=True)
class DebtItem:
    title: str
    severity: str            # "high" | "medium" | "low"
    description: str
    issue_title: str         # ready-to-paste GitHub issue title
    issue_body: str          # ready-to-paste GitHub issue body (Markdown)

@dataclass(slots=True)
class Improvement:
    rank: int                # 1-5
    title: str
    rationale: str
    effort: str              # "low" | "medium" | "high"

@dataclass(slots=True)
class EnrichmentResult:
    module_roles: list[ModuleRole]
    debt_items: list[DebtItem]
    top_improvements: list[Improvement]
    model_id: str            # which model was used (audit trail)
```

```python
# src/reposage/enrichment/provider.py

class EnrichmentProvider(Protocol):
    def enrich(self, report: AuditReport) -> EnrichmentResult: ...

def enrich_report(report: AuditReport, provider: EnrichmentProvider) -> EnrichmentResult:
    return provider.enrich(report)
```

---

## Execution plan

### Dependency order

```
[T1] Branch + RS-020 interface  (blocks all below)
         ↓
    ┌────┴────────────────────────────┐
   [T2]          [T3]              [T4]
 RS-021         RS-022            RS-023
 prompts+      debt+issue        top-5
 classify      drafts            synthesis
    └────┬────────────────────────────┘
         ↓
    [T5] anthropic_provider.py  (integrates T2/T3/T4)
         ↓
    [T6] CLI + renderers
         ↓
    [T7] Tests + tox -e ai
         ↓
    [T8] Final CI verification + PR
```

T2, T3, T4 are **parallel** — they each own a separate file (`prompts.py` sections +
isolated logic). No merge conflict risk.

---

### Task table

| # | Task | Owner | Files touched | Commit message |
|---|------|-------|---------------|----------------|
| T1 | Branch + RS-020: interface + models | **worker** | `enrichment/__init__.py`, `enrichment/provider.py`, `enrichment/models.py`, `pyproject.toml` (optional dep), `tox.ini` (ai env) | `feat(RS-020): add provider-agnostic enrichment boundary and data models` |
| T2 | RS-021: module classification prompt + schema | **Codex** | `enrichment/prompts.py` (classify section) | `feat(RS-021): add module responsibility classification prompt and schema` |
| T3 | RS-022: debt labeling + issue draft prompt + schema | **Codex** | `enrichment/prompts.py` (debt section) | `feat(RS-022): add debt labeling and GitHub issue draft prompt and schema` |
| T4 | RS-023: top-5 synthesis prompt + schema | **Codex** | `enrichment/prompts.py` (synthesis section) | `feat(RS-023): add top-five improvements synthesis prompt and schema` |
| T5 | Anthropic provider: assembles T2/T3/T4 into one SDK call | **worker** | `enrichment/anthropic_provider.py` | `feat: implement AnthropicEnricher with single structured tool-use call` |
| T6 | CLI flag + report renderer extensions | **worker** | `cli.py`, `reports/markdown.py`, `reports/json_report.py` | `feat: wire --enrich flag into CLI and extend Markdown/JSON renderers` |
| T7 | Tests: mocked provider + AI env coverage | **worker** | `tests/test_enrichment.py`, `tox.ini` | `test: add enrichment test suite with FakeProvider and 100% coverage` |
| T8 | Final gate: tox all envs green, push, open PR | **Claude Code** | — | *(PR creation, not a commit)* |

---

### Parallel execution window (T2 / T3 / T4)

T2, T3, and T4 each write isolated sections of `prompts.py` (or, if there is any risk of
conflict, three separate files: `classify_prompt.py`, `debt_prompt.py`,
`synthesis_prompt.py` merged into `prompts.py` by T5's worker). They have no shared
write scope.

**Codex invocation pattern for T2/T3/T4:**

Each Codex task receives:
- The data contracts from `enrichment/models.py` (committed in T1)
- The Anthropic tool-use JSON schema format (specified below)
- A single file to write
- Clear acceptance criteria (mypy clean, 100% coverage from T7)

Codex runs these three tasks in **background** while the human reviews T1's interface.
When all three complete, the worker merges them into the Anthropic provider in T5.

---

## Anthropic tool-use schema (T5 contract)

The single LLM call uses one tool named `audit_enrichment`. The JSON schema:

```json
{
  "name": "audit_enrichment",
  "description": "Structured enrichment of a repository audit report.",
  "input_schema": {
    "type": "object",
    "required": ["module_roles", "debt_items", "top_improvements"],
    "properties": {
      "module_roles": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["module", "responsibility", "layer"],
          "properties": {
            "module":          { "type": "string" },
            "responsibility":  { "type": "string" },
            "layer": {
              "type": "string",
              "enum": ["infrastructure", "domain", "presentation", "test", "tooling"]
            }
          }
        }
      },
      "debt_items": {
        "type": "array",
        "maxItems": 5,
        "items": {
          "type": "object",
          "required": ["title", "severity", "description", "issue_title", "issue_body"],
          "properties": {
            "title":        { "type": "string" },
            "severity":     { "type": "string", "enum": ["high", "medium", "low"] },
            "description":  { "type": "string" },
            "issue_title":  { "type": "string" },
            "issue_body":   { "type": "string" }
          }
        }
      },
      "top_improvements": {
        "type": "array",
        "minItems": 5,
        "maxItems": 5,
        "items": {
          "type": "object",
          "required": ["rank", "title", "rationale", "effort"],
          "properties": {
            "rank":      { "type": "integer", "minimum": 1, "maximum": 5 },
            "title":     { "type": "string" },
            "rationale": { "type": "string" },
            "effort":    { "type": "string", "enum": ["low", "medium", "high"] }
          }
        }
      }
    }
  }
}
```

This schema is defined in `prompts.py` as a Python dict and passed to the Anthropic SDK's
`tools` parameter. Structured output guarantees parseable results without fragile regex.

---

## Multi-agent strategy

### When to use Codex CLI

Codex runs headlessly in background on well-scoped, single-file tasks with a clear
deliverable. Good for:
- T2 / T3 / T4: each writes one section of `prompts.py` (pure functions, no imports
  beyond `models.py` types, no SDK). The spec is fully defined by the tool-use schema
  above. Codex can run all three in parallel while T1 is reviewed.

**Codex task format:**
```
Write src/reposage/enrichment/prompts.py — <RS-XXX section only>.
The file already has <other sections>. Add only the function(s) for <this section>.
Input contract: AuditReport from src/reposage/models.py.
Output: a prompt string and the JSON schema dict for the tool call.
No SDK imports. No anthropic imports. Pure Python.
mypy strict: all args and returns typed.
```

### When to use Claude Code CLI (interactive)

Claude Code has full repo context and is better for:
- T1 (RS-020): interface design touches models.py patterns + pyproject.toml dependency
  management + tox.ini environment setup. Cross-file awareness matters.
- T5 (Anthropic provider): assembles T2/T3/T4 outputs + Anthropic SDK lazy import
  pattern + error handling.
- T6 (CLI + renderers): touches 3 existing files simultaneously, needs to understand
  current CLI argument structure and renderer output format.
- T8 (CI gate + PR): requires running `tox` and interpreting failure output.

### When to use /worker skill (in-session)

/worker is the right choice when:
- The implementation is complex enough to need interactive refinement (ask questions,
  see intermediate output, iterate on types)
- You want to stay in the current Claude Code session with accumulated context
- T1, T5, T6, T7 are all good /worker candidates

**How /worker is enabled:**
Invoke the worker skill in the Claude Code session:
```
/worker
```
Then paste the task spec from this plan. The worker receives:
- The task slice (one item from the task table above)
- The relevant interface file(s) (already committed)
- The acceptance criteria (CI green, 100% coverage, mypy clean)

The worker stays within the file scope listed in the task table and stops at the commit
message. It does NOT proceed to the next task without explicit instruction.

### Execution timeline

```
Day 0
  [Claude Code / worker]  T1: branch + RS-020 interface → commit → push for review

Day 0 (parallel, after T1 committed)
  [Codex background]      T2: classify prompt
  [Codex background]      T3: debt prompt
  [Codex background]      T4: synthesis prompt
  (human reviews T1 interface while Codex runs T2/T3/T4 in background)

Day 1
  [worker]                T5: Anthropic provider (after T2/T3/T4 merged)
  [worker]                T6: CLI + renderers
  [worker]                T7: tests
  [Claude Code]           T8: tox all green → push → open PR
```

---

## QA checkpoints

| After | /qa fires on |
|-------|-------------|
| T1 | `enrichment/models.py` dataclass contracts match the tool-use JSON schema; no slots violation; `pyproject.toml` optional dep parses cleanly |
| T5 | Anthropic provider lazy-imports correctly; `AnthropicEnricher` satisfies `EnrichmentProvider` Protocol; mypy passes on `ai` env |
| T6 | `--enrich` with missing key exits non-zero with clear message; `--enrich` with key and no SDK installed gives clear `ImportError` message; renderers produce valid Markdown and JSON |
| T7 | Coverage ≥ 100% on `enrichment/` (excluding `anthropic_provider.py` lines guarded by `try/except`); `tox -e ai` green |
| T8 | All CI checks green: `tox -e lint`, `tox -e type`, `tox -e py312`, `tox -e pkg` |

---

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| mypy fails on `anthropic` SDK types in base env | High | Medium | Wrap all SDK types in `TYPE_CHECKING`; add `# type: ignore[import-untyped]` if SDK has no stubs |
| Anthropic tool-use schema changes between SDK versions | Low | Medium | Pin `anthropic>=0.40,<1.0` and test against pinned version |
| 100% coverage impossible on `try/except ImportError` guard | Medium | Low | Use `# pragma: no cover` on the `except` branch only; document why |
| Codex writes prompts that don't match the tool-use schema | Medium | Low | T5 worker validates schema round-trip in `test_enrichment.py` with FakeProvider |
| Single LLM call times out on large repos | Low | Medium | Add `timeout_seconds: int = 30` to `EnrichConfig` (added in `config.py` alongside `ScanConfig`) |
| `--enrich` flag added to CLI breaks existing CLI tests | Low | High | Add `--enrich` as a store_true flag; default is False; existing tests pass no flag → no change |

---

## Config extension

Add `EnrichConfig` to `src/reposage/config.py`:

```python
@dataclass(frozen=True, slots=True)
class EnrichConfig:
    model: str = "claude-haiku-4-5-20251001"
    timeout_seconds: int = 30
    max_debt_items: int = 5
```

This keeps enrichment tunable without touching `ScanConfig`.

---

## CLI additions (T6 spec)

```
reposage report PATH [--format {markdown|json}] [--output FILE] [--enrich]
reposage run PATH [--output FILE] [--enrich]
```

When `--enrich` is passed:
1. Check `ANTHROPIC_API_KEY` env var. If absent → `sys.stderr.write(...)` + `sys.exit(2)`.
2. Check `anthropic` importable. If not → clear message + `sys.exit(2)`.
3. Build `AnthropicEnricher(config=EnrichConfig())`.
4. Call `enrich_report(audit_report, enricher)` → `EnrichmentResult`.
5. Pass both to renderer.

---

## Report renderer extensions (T6 spec)

### Markdown additions (appended as new sections)

```markdown
## Module Responsibilities

| Module | Layer | Responsibility |
| --- | --- | --- |
| src/reposage/scan | infrastructure | Walks the filesystem and collects file metadata |
...

## Technical Debt

### 🔴 [High] Missing integration test coverage
> Tests cover only unit paths. Real pipeline runs are never exercised.
**GitHub issue:** *Add integration test for full pipeline run against fixture repos*

...

## Top 5 Improvements

1. **Add integration tests** (effort: low) — …
2. **Enable strict mypy on all modules** (effort: medium) — …
...
```

### JSON additions

`render_json_report` accepts an optional `enrichment: EnrichmentResult | None = None`
parameter. When present, adds `"enrichment"` key to the top-level JSON object.

---

## `tox -e ai` environment

Add to `tox.ini`:

```ini
[testenv:ai]
extras = ai
commands = python -m pytest tests/test_enrichment.py {posargs}
```

This environment installs `anthropic` and runs only enrichment tests. It is **not**
required to pass in the base CI matrix (it is not in the required checks). It is an
optional check run manually or in a separate CI job gated on `ANTHROPIC_API_KEY` presence.

The base `tox -e py312` must still reach 100% coverage on `enrichment/` modules using
the `FakeProvider` mock — no real API calls in base CI.

---

## Commits summary

```
feat(RS-020): add provider-agnostic enrichment boundary and data models
feat(RS-021): add module responsibility classification prompt and JSON schema
feat(RS-022): add debt labeling and GitHub issue draft prompt and JSON schema
feat(RS-023): add top-five improvements synthesis prompt and JSON schema
feat: implement AnthropicEnricher with single structured tool-use call
feat: wire --enrich flag into CLI and extend Markdown/JSON renderers
test: add enrichment test suite with FakeProvider and 100% coverage
```

7 commits. Linear history. Each commit is independently reviewable and tox-clean.

---

## Verification steps

```bash
# From feature/ai-enrichment-provider branch

# Base checks (no API key needed)
tox -e lint
tox -e type
tox -e py312       # must include enrichment/ at 100% coverage via FakeProvider
tox -e pkg

# Enrichment smoke test (requires ANTHROPIC_API_KEY)
tox -e ai

# Manual end-to-end
uv sync --extra ai
python -m reposage report . --enrich --output /tmp/enriched.md
# Verify: /tmp/enriched.md contains Module Responsibilities, Technical Debt, Top 5 sections
```

---

## PR spec

- **Branch:** `feature/ai-enrichment-provider`
- **Title:** `feat(M2): add optional AI enrichment layer (RS-020 through RS-023)`
- **Base:** `main`
- **Required checks before merge:** `lint`, `type`, `py312`, `pkg`
- **Optional check (advisory):** `ai` (documents that it passes in PR description)
- **Reviewers:** assign after all 7 commits are pushed
