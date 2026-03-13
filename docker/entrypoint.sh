#!/usr/bin/env bash
# docker/entrypoint.sh
# Runs inside the container before the main process starts.
# Used by: web, celery-worker, celery-beat services.

set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# 1. Wait for PostgreSQL to accept connections
# ──────────────────────────────────────────────────────────────────────────────
echo "⏳  Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT} …"

MAX_TRIES=30
COUNT=0
until uv run python -c "
import sys, psycopg2, os
try:
    psycopg2.connect(
        dbname=os.environ['POSTGRES_NAME'],
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        host=os.environ['POSTGRES_HOST'],
        port=os.environ['POSTGRES_PORT'],
    )
except psycopg2.OperationalError:
    sys.exit(1)
" 2>/dev/null; do
  COUNT=$((COUNT + 1))
  if [ "$COUNT" -ge "$MAX_TRIES" ]; then
    echo "❌  PostgreSQL did not become ready in time. Exiting."
    exit 1
  fi
  echo "   … retry $COUNT/$MAX_TRIES"
  sleep 2
done
echo "✅  PostgreSQL is ready."

# ──────────────────────────────────────────────────────────────────────────────
# 2. Run only on the web service (skip for celery worker / beat)
# ──────────────────────────────────────────────────────────────────────────────
if [ "${SKIP_DJANGO_SETUP:-false}" != "true" ]; then

  echo "⏳  Running migrations …"
  uv run python manage.py migrate --noinput
  echo "✅  Migrations complete."

  echo "⏳  Collecting static files …"
  uv run python manage.py collectstatic --noinput
  echo "✅  Static files collected."

  # ── Seed DB only when the User table is empty ───────────────────────────────
  USER_COUNT=$(uv run python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamer_house.settings')
django.setup()
from django.contrib.auth import get_user_model
print(get_user_model().all_objects.count())
")
  if [ "$USER_COUNT" -eq "0" ]; then
    echo "⏳  DB is empty — seeding initial data …"
    uv run python manage.py seed_db
    echo "✅  DB seeded."
  else
    echo "ℹ️   DB already has data — skipping seed."
  fi

fi

# ──────────────────────────────────────────────────────────────────────────────
# 3. Hand off to the requested command (gunicorn / celery worker / celery beat)
# ──────────────────────────────────────────────────────────────────────────────
exec "$@"
