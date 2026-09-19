# Single-VM Compose Deployment

## First install

1. Copy `.env.example` to a protected deployment environment file and replace
   every example credential, especially `DATABASE_PASSWORD`,
   `RABBITMQ_PASSWORD`, `JWT_SECRET`, and `SEED_ADMIN_PASSWORD`.
2. Set the public hostname in `PUBLIC_FRONTEND_URL` and
   `CORS_ALLOWED_ORIGINS`. Set `AUTH_COOKIE_SECURE=true` when HTTPS is active.
3. Validate the environment before starting containers:

   ```bash
   set -a
   . /path/to/museum.env
   set +a
   ./scripts/validate-deployment-env.sh
   ```

4. Build and start the dependency services, then run the one-shot migration and
   bootstrap job:

   ```bash
   docker compose --env-file /path/to/museum.env up -d postgres redis rabbitmq
   docker compose --env-file /path/to/museum.env run --rm migrations
   ```

   The job applies all six Alembic migration streams and idempotently creates
   system permissions, roles, the configured administrator, and collection
   reference data.

5. Start the application services:

   ```bash
   docker compose --env-file /path/to/museum.env up -d
   ```

The application services are gated on successful completion of `migrations`.
If the job fails, inspect its logs, correct the environment or database issue,
and rerun it; application services must not be started against a failed schema
upgrade.

The migration job includes a 60-second PostgreSQL TCP readiness retry. A
Docker host must permit container-to-container traffic on the
`museum-internal` bridge network; if DNS resolves but TCP connections time
out, inspect the host's Docker bridge/firewall policy rather than adding a
second database inside the migration image.

## Upgrades

Build or pull the new image set, validate the deployment environment, run the
migration job, and then recreate the application services:

```bash
docker compose --env-file /path/to/museum.env build
docker compose --env-file /path/to/museum.env run --rm migrations
docker compose --env-file /path/to/museum.env up -d
```

Retain the previous image tags, Compose files, migration revision, and secret
version identifiers until the new release passes smoke tests. Do not run
destructive database commands as part of rollback.

## Bootstrap behavior

The migration job is safe to rerun. Existing roles and permissions are reused,
the configured administrator is reactivated and assigned the `ADMIN` role, and
collection reference records are created only when absent. The administrator
password is not printed or stored by the repository.

## Current exposure

Until the reverse proxy phase is complete, Compose publishes the frontend and
gateway ports directly for staging verification. Do not expose this topology
to the public internet without HTTPS, exact CORS configuration, and the Phase
5 reverse proxy.