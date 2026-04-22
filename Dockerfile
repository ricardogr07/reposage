# Stage 1: install dependencies into /deps
FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir --target /deps ".[server,ai]"

# Stage 2: minimal runtime image
FROM python:3.12-slim

# git is required for cloning repositories at request time
# curl is required for the HEALTHCHECK
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /deps /usr/local/lib/python3.12/site-packages

RUN useradd -m -u 1000 reposage
USER reposage

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "reposage.server.app:create_mcp_app", \
     "--factory", "--host", "0.0.0.0", "--port", "8000"]
