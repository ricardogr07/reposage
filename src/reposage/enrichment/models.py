"""Data models for optional AI enrichment results."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ModuleRole:
    """AI-inferred responsibility classification for one module."""

    module: str
    responsibility: str
    layer: str  # infrastructure | domain | presentation | test | tooling


@dataclass(slots=True)
class DebtItem:
    """A technical debt observation with a ready-to-paste GitHub issue draft."""

    title: str
    severity: str  # high | medium | low
    description: str
    issue_title: str
    issue_body: str


@dataclass(slots=True)
class Improvement:
    """A ranked next-step improvement suggestion."""

    rank: int
    title: str
    rationale: str
    effort: str  # low | medium | high


@dataclass(slots=True)
class EnrichmentResult:
    """All AI-enrichment outputs bundled together."""

    module_roles: list[ModuleRole] = field(default_factory=list)
    debt_items: list[DebtItem] = field(default_factory=list)
    top_improvements: list[Improvement] = field(default_factory=list)
    model_id: str = ""
