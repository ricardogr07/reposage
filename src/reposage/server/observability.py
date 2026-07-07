"""Structured logging and OpenTelemetry metrics for the MCP server.

Core RepoSage stays zero-dependency; OpenTelemetry lives in the optional
``[observability]`` extra. When it is not installed, metrics degrade to no-ops
and only structured key=value logs remain, so the server runs either way.

Exporter wiring is env-driven:

* ``OTEL_EXPORTER_OTLP_ENDPOINT`` -- read by the OTLP exporter itself; when set,
  metrics are pushed to that collector.
* ``REPOSAGE_OTEL_CONSOLE`` -- when set (and no OTLP endpoint), metrics print to
  the console. Useful for local verification.
* neither set -- metrics are recorded but not exported (still exercises the
  instrumentation path without a collector).
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

_LOGGER_NAME = "reposage.server"
_METER_NAME = "reposage.server"

# Metric names live here as literals so they appear in the source tree. The
# alert rules in k8s/alerts.yaml reference these exact tokens.
_REQUESTS_TOTAL = "reposage_requests_total"
_REQUEST_LATENCY_MS = "reposage_request_latency_ms"

try:
    from opentelemetry import metrics as _otel_metrics
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter,
        PeriodicExportingMetricReader,
    )

    _OTEL_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only when the extra is absent
    _OTEL_AVAILABLE = False


class _NoOpInstrument:
    """Stand-in for an OpenTelemetry counter/histogram when the extra is absent."""

    def add(self, amount: int, attributes: dict[str, str] | None = None) -> None:
        pass

    def record(self, amount: float, attributes: dict[str, str] | None = None) -> None:
        pass


@dataclass(slots=True)
class _Observability:
    logger: logging.Logger
    counter: Any
    histogram: Any


_state: _Observability | None = None


def _configure_logger() -> logging.Logger:
    """Return the server logger, configuring root logging once if untouched."""
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    return logger


def _build_reader() -> Any | None:
    """Pick a metric reader from the environment, or None for record-only mode."""
    if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        try:
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
                OTLPMetricExporter,
            )
        except ImportError:  # pragma: no cover - otlp extra not installed
            return None
        return PeriodicExportingMetricReader(OTLPMetricExporter())
    if os.environ.get("REPOSAGE_OTEL_CONSOLE"):
        return PeriodicExportingMetricReader(ConsoleMetricExporter())
    return None


def _build_meter() -> tuple[Any, Any]:
    """Create the reposage.server counter and histogram, or no-op fallbacks."""
    if not _OTEL_AVAILABLE:
        return _NoOpInstrument(), _NoOpInstrument()
    reader = _build_reader()
    provider = MeterProvider(metric_readers=[reader] if reader else [])
    _otel_metrics.set_meter_provider(provider)
    meter = _otel_metrics.get_meter(_METER_NAME)
    counter = meter.create_counter(
        _REQUESTS_TOTAL,
        unit="1",
        description="Total MCP tool invocations.",
    )
    histogram = meter.create_histogram(
        _REQUEST_LATENCY_MS,
        unit="ms",
        description="MCP tool invocation latency in milliseconds.",
    )
    return counter, histogram


def _get() -> _Observability:
    global _state
    if _state is None:
        counter, histogram = _build_meter()
        _state = _Observability(_configure_logger(), counter, histogram)
    return _state


@contextmanager
def observe(tool: str) -> Iterator[str]:
    """Time one tool invocation: yield a request_id, then emit a metric and log.

    The counter and latency histogram are recorded in a ``finally`` block so a
    failing invocation is still counted (with ``status=error``).
    """
    state = _get()
    request_id = uuid.uuid4().hex
    start = time.perf_counter()
    status = "ok"
    state.logger.info("event=tool_start request_id=%s tool=%s", request_id, tool)
    try:
        yield request_id
    except Exception:
        status = "error"
        raise
    finally:
        latency_ms = (time.perf_counter() - start) * 1000.0
        state.counter.add(1, {"tool": tool, "status": status})
        state.histogram.record(latency_ms, {"tool": tool})
        state.logger.info(
            "event=tool_end request_id=%s tool=%s status=%s latency_ms=%.2f",
            request_id,
            tool,
            status,
            latency_ms,
        )
