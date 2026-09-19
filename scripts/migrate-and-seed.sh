#!/usr/bin/env bash

set -euo pipefail

ROOT="/app/backend"

wait_for_postgres() {
  echo "Waiting for PostgreSQL at ${DATABASE_HOST}:${DATABASE_PORT}"
  for attempt in $(seq 1 30); do
    if python - <<'PY'
import os
import socket

with socket.create_connection(
    (os.environ["DATABASE_HOST"], int(os.environ["DATABASE_PORT"])),
    timeout=2,
):
    pass
PY
    then
      echo "PostgreSQL is accepting TCP connections"
      return
    fi
    echo "PostgreSQL is not reachable yet (attempt ${attempt}/30)"
    sleep 2
  done
  echo "PostgreSQL did not become reachable." >&2
  exit 1
}

run_migration() {
  local service="$1"
  echo "Applying ${service} migrations"
  cd "$ROOT/${service}"
  alembic upgrade head
}

prepare_collection_revision_table() {
  cd "$ROOT/collection-service"
  python - <<'PY'
from app.core.config import get_settings
from sqlalchemy import create_engine, text

engine = create_engine(get_settings().database_url)
with engine.begin() as connection:
    connection.execute(
        text(
            "ALTER TABLE collection_alembic_version "
            "ALTER COLUMN version_num TYPE VARCHAR(128)"
        )
    )
PY
}

wait_for_postgres
run_migration "auth-service"
echo "Seeding authentication roles, permissions, and administrator"
cd "$ROOT/auth-service"
python -m app.seed

echo "Applying collection-service migrations through the compatible revision"
cd "$ROOT/collection-service"
alembic upgrade 0004_movement_request_fk
prepare_collection_revision_table
alembic upgrade head
echo "Seeding collection reference data"
python -m app.seed

run_migration "conservation-service"
run_migration "loan-service"
run_migration "notification-service"
run_migration "audit-service"

echo "Migrations and idempotent bootstrap completed."
