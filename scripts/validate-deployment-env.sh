#!/usr/bin/env bash

set -euo pipefail

required_vars=(
  DATABASE_HOST DATABASE_PORT DATABASE_NAME DATABASE_USER DATABASE_PASSWORD
  RABBITMQ_HOST RABBITMQ_PORT RABBITMQ_USER RABBITMQ_PASSWORD
  JWT_SECRET SEED_ADMIN_EMAIL SEED_ADMIN_PASSWORD
  PUBLIC_FRONTEND_URL CORS_ALLOWED_ORIGINS
)

for name in "${required_vars[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required deployment variable: ${name}" >&2
    exit 1
  fi
done

if [[ "${DATABASE_PASSWORD}" == "change_me" ||
      "${RABBITMQ_PASSWORD}" == "guest" ||
      "${JWT_SECRET}" == "replace_with_a_long_random_secret" ||
      "${SEED_ADMIN_PASSWORD}" == "ChangeThisPassword123!" ]]; then
  echo "Default/example deployment credentials are not allowed." >&2
  exit 1
fi

if [[ "${JWT_SECRET}" == "default" || ${#JWT_SECRET} -lt 32 ]]; then
  echo "JWT_SECRET must be at least 32 characters." >&2
  exit 1
fi

echo "Deployment environment validation passed."
