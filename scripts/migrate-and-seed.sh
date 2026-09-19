#!/usr/bin/env bash

set -euo pipefail

ROOT="/app/backend"

run_migration() {
  local service="$1"
  echo "Applying ${service} migrations"
  cd "$ROOT/${service}"
  alembic upgrade head
}

run_migration "auth-service"
echo "Seeding authentication roles, permissions, and administrator"
cd "$ROOT/auth-service"
python -m app.seed

run_migration "collection-service"
echo "Seeding collection reference data"
cd "$ROOT/collection-service"
python -m app.seed

run_migration "conservation-service"
run_migration "loan-service"
run_migration "notification-service"
run_migration "audit-service"

echo "Migrations and idempotent bootstrap completed."
