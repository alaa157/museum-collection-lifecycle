#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/6] Seeding authentication"
cd "$ROOT/backend/auth-service"
# source .venv/bin/activate
python -m app.seed

echo "[2/6] Seeding collection"
cd "$ROOT/backend/collection-service"
alembic upgrade head
# source .venv/bin/activate
python -m app.seed

echo "[3/6] Applying conservation migrations"
cd "$ROOT/backend/conservation-service"
# source .venv/bin/activate
alembic upgrade head

echo "[4/6] Applying loan migrations"
cd "$ROOT/backend/loan-service"
# source .venv/bin/activate
alembic upgrade head

echo "[5/6] Applying notification migrations"
cd "$ROOT/backend/notification-service"
# source .venv/bin/activate
alembic upgrade head

echo "[6/6] Applying audit migrations"
cd "$ROOT/backend/audit-service"
# source .venv/bin/activate
alembic upgrade head

echo
echo "Development seed completed."
echo
echo "Admin:"
echo "  Email: admin@gmail.com"
echo "  Password: read from .env"
