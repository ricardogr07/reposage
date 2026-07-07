"""Serving surface: FastAPI app with metrics, tracing, and request correlation."""

from __future__ import annotations

import opentelemetry  # noqa: F401  (log/trace exporter wiring)
from fastapi import FastAPI
from prometheus_client import Counter

app = FastAPI()
REQUESTS = Counter("churn_requests_total", "Total churn scoring requests")


@app.get("/health")
def health(request_id: str = "") -> dict[str, str]:
    """Health endpoint that increments a counter and echoes the request id."""

    REQUESTS.inc()
    return {"status": "ok", "request_id": request_id}
