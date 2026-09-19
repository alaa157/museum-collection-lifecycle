# Deployment Plan: Single-VM Docker Compose Release

Branch: `deployability-plan-single-vm-compose`

This document is an implementation plan only. It does not change application
behavior, Dockerfiles, Compose configuration, infrastructure, or secrets.
The existing default branch remains the reference implementation until the
phases below are completed and verified.

## Goal and target

Make the Museum Collection Lifecycle Platform deployable on one Linux VM with
Docker Compose, using:

- A normal Docker bridge network for application-to-application traffic.
- PostgreSQL, Redis, and RabbitMQ as explicit Compose dependencies for the
  first deployment, with persistent volumes and a documented migration path
  to managed services.
- Multi-stage, reproducible images for the six FastAPI services and the
  Next.js frontend.
- A reverse proxy as the only public entry point, with HTTPS, health checks,
  secrets, persistent uploads, logs, metrics, backups, and rollback steps.

The first milestone is a repeatable staging deployment. Production readiness
is a separate milestone and requires the security, backup, and operational
checks described below.

## Out of scope for this deployment effort

- Rewriting domain services or changing business rules.
- Adding exhibition API routes. The frontend currently references exhibition
  endpoints that are not exposed by the loan service; this remains a tracked
  release blocker for the advertised exhibition-management feature.
- Kubernetes manifests or cloud-specific infrastructure.
- Migrating existing data without a separately approved backup and restore
  exercise.

## Current blockers to resolve

1. Backend Dockerfiles require absent `build/wheels` directories and use
   `pip --no-index`.
2. The frontend Dockerfile expects pre-existing `node_modules` and `.next`
   directories instead of building them.
3. Compose uses `network_mode: host`, fixed host ports, and loopback defaults.
4. PostgreSQL, Redis, and RabbitMQ are not defined in Compose.
5. Startup ordering is based on `depends_on` without readiness checks.
6. Migrations and admin seeding are performed by a development shell script.
7. Uploaded files use a local bind mount without a production backup policy.
8. There is no production edge proxy, TLS configuration, CI/CD pipeline, or
   release rollback procedure.
9. `docs/deployment.md` and `docs/architecture.md` are currently empty.

## Phase 0 — Branch, baseline, and release contract

### Tasks

- Work only on a new feature/release branch; do not alter the existing branch.
- Record the source commit and expected service ports in release notes.
- Define the staging hostname, public frontend URL, and allowed CORS origins.
- Decide whether PostgreSQL, Redis, and RabbitMQ run in Compose or are replaced
  by managed services before production. The initial implementation assumes
  Compose-managed dependencies.
- Define the required smoke-test journey:
  health check, readiness check, login, authenticated collection request,
  attachment upload/download, notification read, audit lookup, and frontend
  navigation.
- Define the rollback artifact: the previous image tag plus the previous
  Compose configuration and environment secret versions.

### Exit criteria

- The branch has a written release contract and no untracked credentials.
- A clean checkout can identify exactly which files and commands comprise a
  release.

## Phase 1 — Reproducible backend images

### Files to change

- `backend/*/Dockerfile`
- `backend/*/requirements.txt` only if dependency separation is needed
- Add a repository-level build helper or CI workflow for image builds.

### Implementation

- Replace offline-only installation with a multi-stage build:
  dependency/build stage creates a virtual environment or installs wheels
  from the locked requirements; runtime stage copies only installed packages
  and application code.
- Keep Python 3.12 and run each service as a non-root user.
- Use `--no-cache-dir`, a fixed working directory, and explicit UTF-8/
  unbuffered environment settings.
- Copy only the files each service needs, including Alembic files for services
  with migrations.
- Add image labels for commit SHA, version, and build timestamp.
- Do not embed `.env`, development credentials, test data, or host-specific
  URLs in images.
- Add a common healthcheck convention that calls each service's `/health`;
  readiness checks remain responsible for dependency availability.

### Verification

- Build every backend image from a clean checkout with no generated
  `build/wheels` directory.
- Run each image with a minimal environment and verify it binds to `0.0.0.0`
  on its configured internal port.
- Scan images for critical/high OS and Python vulnerabilities and record any
  accepted exceptions.

### Exit criteria

- All six backend images build offline after the dependency layers are
  cached by the builder, and online from a clean CI runner.
- No service requires files generated on the host before `docker build`.

## Phase 2 — Reproducible Next.js frontend image

### Files to change

- `frontend/Dockerfile`
- `frontend/.dockerignore` (add if needed)
- `frontend/package.json` or lockfile only when required by the build.

### Implementation

- Use a multi-stage Node 22 build:
  dependency stage runs `pnpm install --frozen-lockfile`;
  builder stage runs `pnpm build`;
  runtime stage copies the standalone Next.js output and required static/
  public assets.
- Do not copy host `node_modules` or `.next`.
- Configure the gateway rewrite through a runtime/build-time deployment
  contract. Ensure the browser's `/api` requests resolve through the public
  reverse proxy rather than exposing internal service addresses.
- Run the runtime as a non-root user and expose only port 3000 internally.
- Preserve `NEXT_PUBLIC_APP_NAME` and the intended API base path.

### Verification

- Build from a clean checkout with no `node_modules` or `.next`.
- Start the image and verify the landing page, login page, static assets, and
  `/api` rewrite.
- Run type checking and the enabled Playwright authentication flow once the
  test configuration is restored.

### Exit criteria

- The frontend image is self-contained and starts with only deployment
  environment variables.
- No development server or source tree is required at runtime.

## Phase 3 — Compose network and dependency topology

### Files to change

- `docker-compose.yml`
- `.env.example`
- Service configuration modules that currently default to loopback addresses,
  if those defaults prevent container-to-container operation.
- Add a Compose override for local development only if production settings
  would otherwise be mixed with development settings.

### Implementation

- Remove `network_mode: host`.
- Create an internal bridge network, for example `museum-internal`; publish
  only the reverse proxy port and, if needed, a restricted metrics port.
- Use service DNS names (`postgres`, `redis`, `rabbitmq`, and service names)
  rather than `127.0.0.1`.
- Define PostgreSQL, Redis, and RabbitMQ services with named volumes,
  explicit credentials, resource limits, and restart policies.
- Add `healthcheck` blocks for all dependencies and application services.
- Make application services depend on dependency health, not merely container
  creation.
- Keep internal ports stable but stop publishing the six service ports to the
  VM host unless an operational requirement explicitly needs them.
- Mount the upload volume only into the collection service and document its
  backup/restore ownership.
- Add a dedicated reverse-proxy service connected to the internal network.

### Verification

- `docker compose config` succeeds with a fully populated environment file.
- A clean `docker compose up -d` reaches healthy status without manual host
  services.
- From the proxy, the frontend and gateway are reachable; from outside the
  VM, internal service ports are not reachable.
- Stop each dependency and confirm the corresponding readiness endpoint fails
  clearly, then recovers when the dependency returns.

### Exit criteria

- The complete stack starts on a fresh VM using one documented Compose command
  plus the migration job.
- No container uses loopback to reach another container.

## Phase 4 — Configuration, secrets, migrations, and seed data

### Files to change

- `.env.example`
- `scripts/seed-development.sh` (rename or split development and deployment
  responsibilities)
- Add a production migration/seed command or one-shot Compose profile.
- Add deployment documentation in `docs/deployment.md`.

### Implementation

- Separate schema migrations from initial administrator creation.
- Run Alembic migrations as a one-shot release job before starting or updating
  application services.
- Make the migration job fail loudly and remain inspectable in logs.
- Make admin creation idempotent and read the configured email/password; remove
  the hardcoded email from output.
- Require production secrets rather than silently accepting example/default
  values. Required values include database credentials, RabbitMQ credentials,
  JWT secret, admin bootstrap credentials, CORS origins, and public URLs.
- Document secret injection from a root-readable file, Docker secrets, or the
  VM's secret manager. Never commit the real `.env`.
- Set production cookie/security options and exact CORS origins after confirming
  the public hostname.

### Verification

- A new database can be migrated exactly once and a second run is a no-op.
- A failed migration prevents rollout of the new application version.
- Re-running bootstrap does not duplicate the admin or roles.
- Changing a JWT secret is documented as a deliberate token invalidation event.

### Exit criteria

- Configuration is explicit, validated, and environment-specific.
- There is a documented, repeatable first-install and upgrade procedure.

## Phase 5 — Public edge, TLS, and persistent storage

### Files to change

- Add reverse-proxy configuration (Caddy, Traefik, or Nginx).
- Add proxy-related Compose service/configuration.
- `.env.example`
- `storage/` mount definitions and backup scripts/documentation.

### Implementation

- Terminate HTTPS at the reverse proxy and redirect HTTP to HTTPS.
- Route `/` to the frontend and `/api/*` to the gateway; do not expose
  backend services directly.
- Configure request size limits appropriate for museum attachments, timeouts,
  access logs, security headers, and trusted proxy behavior.
- Use a real domain and certificate renewal mechanism.
- Define a durable upload strategy: named encrypted volume for the VM phase,
  plus scheduled off-host backups; keep the path stable for restoration.
- Define database backup retention, RabbitMQ/Redis recovery expectations, and
  a tested restore procedure. Redis should not be treated as the system of
  record.

### Verification

- Browser login and refresh work over HTTPS.
- Secure and HTTP-only cookie behavior is confirmed in a real browser.
- Upload/download works after a container recreation.
- Restore a database and uploads into an isolated stack and run the smoke
  tests.

### Exit criteria

- The VM has one public HTTPS endpoint and documented DNS/certificate setup.
- Data recovery objectives and the last successful restore test are recorded.

## Phase 6 — Observability and operational controls

### Files to change

- `infrastructure/prometheus/prometheus.yml`
- Add dashboard/alert configuration as needed.
- Add Compose logging, resource, and healthcheck settings.
- Add a runbook under `docs/`.

### Implementation

- Update Prometheus targets from loopback assumptions to reachable service
  names or scrape through the internal network.
- Collect gateway and service health/readiness metrics, request latency,
  error rate, database connectivity, queue health, disk usage, and upload
  volume capacity.
- Configure log rotation and structured correlation-ID logging.
- Add alerts for unhealthy services, failed migrations, database storage,
  certificate expiry, backup failures, and sustained 5xx responses.
- Set CPU/memory limits and document expected VM sizing.
- Add a runbook for restart, rollback, dependency outage, credential rotation,
  and restore.

### Exit criteria

- An operator can identify a failing dependency and recover the stack without
  SSH-level guesswork.
- Logs and metrics do not expose passwords, tokens, or uploaded sensitive data.

## Phase 7 — CI/CD and release process

### Files to add/change

- `.github/workflows/ci.yml`
- `.github/workflows/build-images.yml`
- `.github/workflows/deploy.yml` only after staging is proven.
- Add image tags and release metadata documentation.

### Implementation

- CI: run backend tests for all services, frontend typecheck/build, Compose
  config validation, and a clean image build.
- Add dependency/image scanning and fail on agreed severity thresholds.
- Publish immutable images tagged with commit SHA; optionally add a human
  release tag.
- Deploy by pulling the exact image set, running the migration job, starting
  the new stack, and executing smoke tests.
- Keep the previous image set available for rollback.
- Use protected GitHub environments and deployment secrets; do not deploy
  from pull requests.

### Verification

- A pull request fails when a Docker build depends on ignored/generated host
  files.
- A release can be reproduced from its commit SHA.
- A failed smoke test leaves the previous release available and does not
  silently report success.

## Recommended implementation order

1. Phase 0 baseline and acceptance contract.
2. Phases 1 and 2 image builds.
3. Phase 3 Compose networking and dependencies.
4. Phase 4 migrations, seed, and secrets.
5. Phase 5 proxy, TLS, and storage.
6. Phase 6 observability and runbooks.
7. Phase 7 CI/CD and staged deployment.
8. Address the exhibition API gap before marketing exhibition management as
   complete.

Do not skip ahead to public exposure before Phase 4 is complete. Do not call
the system production-ready until the restore test, secret handling, HTTPS,
health checks, and rollback procedure have all passed.

## Definition of done

- A clean checkout builds every image without generated host artifacts.
- One VM can start the complete stack with Compose and documented secrets.
- Only the reverse proxy is publicly exposed.
- Migrations are automated, idempotent, and run before rollout.
- Login, collection CRUD/read, attachment persistence, notifications, audit,
  health/readiness, and frontend navigation pass smoke tests.
- Backups have been restored successfully in an isolated environment.
- CI builds and scans the exact images deployed to staging.
- A previous release can be restored using the documented rollback procedure.
