FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY packages/ packages/
COPY apps/ apps/
COPY scripts/ scripts/
COPY config/ config/
RUN mkdir -p /app/models
COPY models/ models/
ENV PYTHONPATH=/app

# APP_MODE=api  → uvicorn (default)
# APP_MODE=worker → background worker
ENV APP_MODE=api
CMD ["sh", "-c", "if [ \"$APP_MODE\" = \"worker\" ]; then uv run python -m apps.worker.main; else uv run uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT:-8000}; fi"]
