# Stage 1: build a frozen virtualenv from the committed lockfile
FROM python:3.12-slim AS builder

# uv resolves nothing at build time: it installs the exact pins in uv.lock.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app
ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock README.md ./
COPY src/ src/

RUN uv sync --frozen --no-dev --extra server --extra observability --extra audit

# Stage 2: minimal runtime image
FROM python:3.12-slim

# git is required for cloning repositories at request time
# curl is required for the HEALTHCHECK
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:${PATH}"

RUN useradd -m -u 1000 reposage
USER reposage

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "reposage.server.app:create_mcp_app", \
     "--factory", "--host", "0.0.0.0", "--port", "8000"]
