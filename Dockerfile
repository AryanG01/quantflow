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

# ---- API target ----
FROM base AS api
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ---- Worker target ----
FROM base AS worker
CMD ["uv", "run", "python", "-m", "apps.worker.main"]
