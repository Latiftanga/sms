# ── Stage 1: dependency builder ───────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Install deps into an isolated venv
COPY pyproject.toml uv.lock* ./
RUN uv venv /venv \
    && UV_PROJECT_ENVIRONMENT=/venv uv sync --frozen --no-dev --no-install-project

# ── Stage 2: runtime ──────────────────────────────────────────────
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

# Non-root user
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
