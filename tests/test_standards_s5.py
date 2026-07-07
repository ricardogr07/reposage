"""Tests for Standard 5: Accountable (logs, metrics, alerting) plus integration."""

from __future__ import annotations

from pathlib import Path

from reposage.standards import s3_proven, s4_shipped, s5_accountable
from reposage.standards.config import StandardsConfig
from reposage.standards.context import build_context
from reposage.standards.models import CheckResult, CheckStatus, StandardResult

_SERVE_WITH_METRIC = (
    "from fastapi import FastAPI\n"
    "from prometheus_client import Counter\n\n"
    "app = FastAPI()\n"
    'HITS = Counter("api_hits_total", "hits")\n'
)


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run(root: Path) -> StandardResult:
    config = StandardsConfig()
    return s5_accountable.evaluate(build_context(root, config), config)


def _check(result: StandardResult, check_id: str) -> CheckResult:
    return next(check for check in result.checks if check.check_id == check_id)


def test_no_surfaces_all_not_applicable(tmp_path: Path) -> None:
    _write(tmp_path, "src/pkg/helpers.py", "def f() -> int:\n    return 1\n")

    result = _run(tmp_path)

    assert all(check.status is CheckStatus.NOT_APPLICABLE for check in result.checks)


def test_serving_with_exporter_and_request_id_passes_logs(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "src/pkg/serve.py",
        "import prometheus_client\n"
        "from fastapi import FastAPI\n\n"
        "app = FastAPI()\n\n"
        "def handler(request_id: str) -> str:\n    return request_id\n",
    )

    assert _check(_run(tmp_path), "s5.logs").status is CheckStatus.PASS


def test_serving_without_emission_fails_metrics(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "src/pkg/serve.py",
        "from fastapi import FastAPI\n\napp = FastAPI()\n",
    )

    metrics = _check(_run(tmp_path), "s5.metrics")

    assert metrics.status is CheckStatus.FAIL
    assert any("serving" in line for line in metrics.evidence)


def test_training_only_repo_metrics_pass_logs_not_applicable(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "src/pkg/train.py",
        "import mlflow\n\n\ndef train() -> None:\n    mlflow.log_metric('auc', 0.9)\n",
    )

    result = _run(tmp_path)

    assert _check(result, "s5.metrics").status is CheckStatus.PASS
    assert _check(result, "s5.logs").status is CheckStatus.NOT_APPLICABLE
    assert _check(result, "s5.alerting").status is CheckStatus.NOT_APPLICABLE


def test_alert_rule_cross_referencing_metric_passes(tmp_path: Path) -> None:
    _write(tmp_path, "src/pkg/serve.py", _SERVE_WITH_METRIC)
    _write(
        tmp_path,
        "alerts/rules.yml",
        "groups:\n  - name: x\n    rules:\n      - alert: NoHits\n"
        "        expr: rate(api_hits_total[5m]) == 0\n",
    )

    assert _check(_run(tmp_path), "s5.alerting").status is CheckStatus.PASS


def test_alert_rule_without_match_is_uncertain(tmp_path: Path) -> None:
    _write(tmp_path, "src/pkg/serve.py", _SERVE_WITH_METRIC)
    _write(
        tmp_path,
        "alerts/rules.yml",
        "groups:\n  - name: x\n    rules:\n      - alert: NoHits\n"
        "        expr: rate(other_metric_total[5m]) == 0\n",
    )

    assert _check(_run(tmp_path), "s5.alerting").status is CheckStatus.UNCERTAIN


def test_ds_passing_repo_per_check_statuses() -> None:
    repo = Path(__file__).resolve().parent / "fixtures" / "standards" / "ds_passing_repo"
    config = StandardsConfig()
    ctx = build_context(repo, config)

    s3 = s3_proven.evaluate(ctx, config)
    s4 = s4_shipped.evaluate(ctx, config)
    s5 = s5_accountable.evaluate(ctx, config)

    # s3.suite is UNCERTAIN in static mode (tests present, subprocess off).
    assert _check(s3, "s3.suite").status is CheckStatus.UNCERTAIN
    assert _check(s3, "s3.behavioral").status is CheckStatus.PASS
    assert _check(s3, "s3.eval_gate").status is CheckStatus.PASS
    assert _check(s4, "s4.deploy_path").status is CheckStatus.PASS
    assert _check(s4, "s4.env_isolation").status is CheckStatus.PASS
    assert _check(s4, "s4.cicd").status is CheckStatus.PASS
    assert _check(s5, "s5.logs").status is CheckStatus.PASS
    assert _check(s5, "s5.metrics").status is CheckStatus.PASS
    assert _check(s5, "s5.alerting").status is CheckStatus.PASS
