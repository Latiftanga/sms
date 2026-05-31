# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:latest AS uv

# ── Stage 1a: production deps ─────────────────────────────────────
FROM python:3.12-slim AS builder
WORKDIR /app
COPY --from=uv /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /venv \
    && UV_PROJECT_ENVIRONMENT=/venv uv sync --frozen --no-dev --no-install-project

# ── Stage 1b: production + dev deps ──────────────────────────────
FROM builder AS builder-dev
RUN --mount=type=cache,target=/root/.cache/uv \
    UV_PROJECT_ENVIRONMENT=/venv uv sync --frozen --no-install-project

# ── Stage 2: runtime (production) ────────────────────────────────
FROM python:3.12-slim AS runtime

# WeasyPrint system dependencies + fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libharfbuzz0b \
        libcairo2 \
        libgdk-pixbuf-xlib-2.0-0 \
        fonts-liberation \
        fontconfig \
    && fc-cache -f \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY . .
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

# ── Stage 3: development (runtime + dev deps) ─────────────────────
# Used by api/worker in docker-compose.override.yml and by the test service.
# COPY in a Dockerfile always runs as root, so the venv swap works even though
# USER appuser is inherited from the runtime stage.
FROM runtime AS development
COPY --from=builder-dev /venv /venv
