FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen
COPY . .
CMD ["python", "-m", "churnpkg.serve"]
