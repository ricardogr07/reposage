"""Standard 5: Accountable. A running system's logs, metrics, and alerts."""

from __future__ import annotations

import re
from pathlib import Path

from reposage.standards.config import StandardsConfig
from reposage.standards.context import AuditContext
from reposage.standards.models import (
    CheckResult,
    CheckStatus,
    StandardResult,
    build_standard_result,
)

_NO_SURFACE = "no serving or training surface detected; Standard 5 presupposes a running system"

_EXPORTER_RE = re.compile(
    r"(opentelemetry|azure\.monitor|prometheus_client|datadog|statsd|structlog)"
)
_CORRELATION_RE = re.compile(r"\b(request_id|trace_id|correlation_id)\b")
_SERVING_METRIC_RE = re.compile(
    r"(\bCounter\(|\bHistogram\(|\bGauge\(|\bSummary\(|create_counter|create_histogram|\bstatsd\b)"
)
_TRAINING_METRIC_RE = re.compile(
    r"(mlflow\.log_metric|mlflow\.log_param|mlflow\.log_artifact|wandb\.log)"
)
_METRIC_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{4,}")


def evaluate(ctx: AuditContext, config: StandardsConfig) -> StandardResult:
    """Evaluate Standard 5: queryable logs, metric tracking, and alerting."""

    serving = [rel for rel, role in ctx.roles.items() if role == "serving"]
    training = [rel for rel, role in ctx.roles.items() if role == "training"]
    checks = [
        _check_logs(ctx, serving),
        _check_metrics(ctx, serving, training),
        _check_alerting(ctx, serving),
    ]
    return build_standard_result(5, "Accountable", checks)


def _check_logs(ctx: AuditContext, serving: list[str]) -> CheckResult:
    cid, name = "s5.logs", "Queryable logs"
    if not serving:
        return CheckResult(cid, name, CheckStatus.NOT_APPLICABLE, [_NO_SURFACE])
    source = _concat(ctx, serving)
    exporter = _EXPORTER_RE.search(source)
    correlation = _CORRELATION_RE.search(source)
    if exporter and correlation:
        return CheckResult(
            cid,
            name,
            CheckStatus.PASS,
            [f"log exporter ({exporter.group(1)}) and request correlation token in serving code"],
        )
    if exporter:
        return CheckResult(
            cid,
            name,
            CheckStatus.PASS,
            [
                f"log exporter ({exporter.group(1)}) configured",
                "no request correlation token found",
            ],
        )
    return CheckResult(
        cid,
        name,
        CheckStatus.FAIL,
        ["no log exporter in serving code: logs die with the process"],
        "Ship logs to a queryable backend (OpenTelemetry, Azure Monitor, or structlog handler).",
    )


def _check_metrics(ctx: AuditContext, serving: list[str], training: list[str]) -> CheckResult:
    cid, name = "s5.metrics", "Metric tracking"
    if not serving and not training:
        return CheckResult(cid, name, CheckStatus.NOT_APPLICABLE, [_NO_SURFACE])
    evidence: list[str] = []
    missing: list[str] = []
    if serving:
        if _SERVING_METRIC_RE.search(_concat(ctx, serving)):
            evidence.append("serving code emits production metrics")
        else:
            missing.append("serving surface emits no production metrics")
    if training:
        if _TRAINING_METRIC_RE.search(_concat(ctx, training)):
            evidence.append("training code logs experiment metrics")
        else:
            missing.append("training surface logs no experiment metrics")
    if missing:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            missing,
            "Instrument the missing surface: production metrics for serving, "
            "experiment tracking for training.",
        )
    return CheckResult(cid, name, CheckStatus.PASS, evidence)


def _check_alerting(ctx: AuditContext, serving: list[str]) -> CheckResult:
    cid, name = "s5.alerting", "Alerting"
    if not serving:
        return CheckResult(cid, name, CheckStatus.NOT_APPLICABLE, [_NO_SURFACE])
    artifacts = _alert_artifacts(ctx)
    if not artifacts:
        return CheckResult(
            cid,
            name,
            CheckStatus.FAIL,
            ["no alert rules found (Prometheus rules, Azure metric alerts, or a scheduled check)"],
            "Add an alert rule that fires when an emitted metric crosses a threshold.",
        )
    code = _concat_python(ctx)
    for rel, tokens in artifacts:
        matched = sorted(token for token in tokens if token in code)
        if matched:
            return CheckResult(
                cid,
                name,
                CheckStatus.PASS,
                [f"alert rule {rel} references emitted metric '{matched[0]}'"],
            )
    return CheckResult(
        cid,
        name,
        CheckStatus.UNCERTAIN,
        [f"alert rule {artifacts[0][0]} found but its metric does not match any emitted metric"],
        "Point the alert at a metric name the code actually emits.",
    )


def _alert_artifacts(ctx: AuditContext) -> list[tuple[str, set[str]]]:
    artifacts: list[tuple[str, set[str]]] = []
    for record in ctx.file_records:
        text = _read(ctx.root, record.path)
        if record.extension in (".yml", ".yaml"):
            if ("alert:" in text and "expr:" in text) or _is_scheduled_check(text):
                artifacts.append((record.path, _metric_tokens(text)))
        elif record.extension in (".bicep", ".tf", ".json") and "metricAlerts" in text:
            artifacts.append((record.path, _metric_tokens(text)))
    return artifacts


def _is_scheduled_check(text: str) -> bool:
    return "schedule:" in text and "cron" in text and bool(_metric_tokens(text))


def _metric_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for line in text.splitlines():
        low = line.strip().lower()
        if "expr:" in low or low.startswith(("alert:", "- alert:")):
            tokens.update(tok for tok in _METRIC_TOKEN_RE.findall(line) if "_" in tok)
    if not tokens:
        tokens.update(tok for tok in _METRIC_TOKEN_RE.findall(text) if "_" in tok)
    return tokens


def _concat(ctx: AuditContext, paths: list[str]) -> str:
    return "\n".join(_read(ctx.root, rel) for rel in paths)


def _concat_python(ctx: AuditContext) -> str:
    return "\n".join(
        _read(ctx.root, record.path) for record in ctx.file_records if record.extension == ".py"
    )


def _read(root: Path, rel: str) -> str:
    try:
        return (root / rel).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
