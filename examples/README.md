# Examples

This directory contains sample audit outputs produced by running RepoSage against
the `ricardogr07/reposage` repository itself.

## Files

| File | Description |
|---|---|
| `reposage-audit.json` | Full `AuditReport` as JSON — base pipeline, no AI enrichment |
| `reposage-audit.md` | Same report rendered as Markdown |
| `reposage-audit-enriched.md` | Markdown report with AI enrichment (module roles, debt items, top improvements) |

## Regenerating

```bash
# Base report (no extras required)
python -m reposage report . --format json   --output examples/reposage-audit.json
python -m reposage report . --format markdown --output examples/reposage-audit.md

# Enriched report (requires reposage[ai] and ANTHROPIC_API_KEY)
ANTHROPIC_API_KEY=<key> python -m reposage report . --enrich \
  --format markdown --output examples/reposage-audit-enriched.md
```
