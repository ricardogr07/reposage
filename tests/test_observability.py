"""Tests for server observability: structured logging + metric instrumentation.

The default test env does not install the optional [observability] extra, so
these exercise the no-op fallback path. A light real-path test runs only when
opentelemetry happens to be importable.
"""

from __future__ import annotations

import logging

import pytest

import reposage.server.observability as obs


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    """Clear the module singleton so each test rebuilds instrumentation."""
    obs._state = None


def test_observe_yields_request_id() -> None:
    with obs.observe("audit_repository") as request_id:
        assert isinstance(request_id, str)
        assert len(request_id) == 32  # uuid4().hex


def test_observe_logs_request_id(caplog: pytest.LogCaptureFixture) -> None:
    with (
        caplog.at_level(logging.INFO, logger="reposage.server"),
        obs.observe("audit_repository") as request_id,
    ):
        pass
    assert request_id in caplog.text
    assert "event=tool_start" in caplog.text
    assert "event=tool_end" in caplog.text


def test_observe_records_metrics_without_raising() -> None:
    # No-op fallback (or real) instruments must accept add()/record() calls.
    with obs.observe("audit_repository"):
        pass
    state = obs._get()
    state.counter.add(1, {"tool": "audit_repository", "status": "ok"})
    state.histogram.record(12.5, {"tool": "audit_repository"})


def test_observe_counts_errors_and_reraises(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="reposage.server"):  # noqa: SIM117
        with pytest.raises(ValueError, match="boom"):
            with obs.observe("audit_repository"):
                raise ValueError("boom")
    assert "status=error" in caplog.text


def test_noop_instrument_is_used_when_otel_absent() -> None:
    if obs._OTEL_AVAILABLE:
        pytest.skip("opentelemetry installed; no-op fallback not exercised")
    counter, histogram = obs._build_meter()
    assert isinstance(counter, obs._NoOpInstrument)
    assert isinstance(histogram, obs._NoOpInstrument)


def test_real_meter_builds_when_otel_present(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("opentelemetry.sdk.metrics")
    monkeypatch.setenv("REPOSAGE_OTEL_CONSOLE", "1")
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    counter, histogram = obs._build_meter()
    # Real instruments expose add()/record(); calling them must not raise.
    counter.add(1, {"tool": "audit_repository", "status": "ok"})
    histogram.record(1.0, {"tool": "audit_repository"})
