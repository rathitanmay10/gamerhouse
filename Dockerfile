# ─────────────────────────────────────────────────────────────────────────────
# GamerHouse — Production Dockerfile
# Python 3.13 · uv · Gunicorn
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.13-slim

# ── System dependencies ───────────────────────────────────────────────────────
# libpq-dev / gcc needed to compile psycopg2-binary native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# ── Install uv ────────────────────────────────────────────────────────────────
# Pinned to a specific version for reproducibility
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Install dependencies FIRST (layer-cache friendly) ────────────────────────
# Copy only the dependency manifests so this layer is rebuilt only when they change
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# ── Copy application source ───────────────────────────────────────────────────
COPY . .

# ── Static files directory (populated at runtime by collectstatic) ────────────
RUN mkdir -p /app/staticfiles

# ── Entrypoint ────────────────────────────────────────────────────────────────
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]

# Default command — overridden per-service in docker-compose.yml
CMD ["uv", "run", "newrelic-admin", "run-program", "gunicorn", "gamer_house.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
