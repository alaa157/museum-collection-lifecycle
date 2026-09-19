# Phase 0 Release Contract

Status: baseline established  
Target: single Linux VM running Docker Compose  
Branch: `deployability-plan-single-vm-compose`

This contract defines the release boundary and acceptance checks for the
deployment work. It contains no credentials and does not change runtime
behavior.

## Baseline and source control

| Item | Value |
| --- | --- |
| Repository | `alaa157/museum-collection-lifecycle` |
| Existing default branch | `master` |
| Source baseline (`master`) | `17e7d15b877d4a9a2fcf2afbe3271a68946bcdbf` |
| Release branch | `deployability-plan-single-vm-compose` |
| Release branch tip after Phase 0 | Recorded in the Phase 0 commit |
| Deployment target | One Linux VM with Docker Engine and Compose v2 |
| Public entry point | Reverse proxy only; frontend and gateway are not directly exposed |

All deployment changes must be committed to the release branch. The existing
`master` branch is not modified by this work. Images must be tagged with the
release commit SHA; mutable tags such as `latest` are not rollback references.

## Environment contract

The initial staging topology uses Compose-managed PostgreSQL, Redis, and
RabbitMQ with named persistent volumes. Before production, the dependency
decision must be revisited:

- PostgreSQL may remain Compose-managed only if VM storage, backups, restore
  testing, and failover expectations are acceptable.
- Redis is a cache and must not be treated as the system of record.
- RabbitMQ requires durable configuration and a documented recovery procedure.

The following values are intentionally placeholders until a real domain and
secret-management method are selected:

| Setting | Staging contract |
| --- | --- |
| Staging hostname | `staging.<your-domain>` |
| Public frontend URL | `https://staging.<your-domain>` |
| Allowed CORS origin | `https://staging.<your-domain>` only |
| Public HTTP port | `80`, redirecting to HTTPS |
| Public HTTPS port | `443` |
| Internal frontend port | `3000` |
| Internal API gateway port | `8000` |
| Internal service ports | Auth `8001`, collection `8002`, conservation `8003`, loan `8004`, notification `8005`, audit `8006` |
| PostgreSQL | Compose service DNS name and internal port `5432` |
| Redis | Compose service DNS name and internal port `6379` |
| RabbitMQ | Compose service DNS name and internal port `5672` |
| Upload storage | Dedicated persistent volume, backed up off-host |

No real hostname, password, JWT secret, access token, or private key belongs
in this document, the repository, an image, or a pull request.

## Required smoke-test journey

The deployment is staging-ready only after the following checks pass against
the public HTTPS endpoint:

1. **Availability:** `GET /health` returns a healthy response from the
   gateway, and `GET /ready` reports that required dependencies are available.
2. **Frontend:** the landing page, login page, JavaScript bundles, and CSS load
   without browser console errors caused by deployment configuration.
3. **Authentication:** log in with the bootstrap administrator, receive an
   access token, refresh the session, and verify logout/revocation.
4. **Collection:** perform an authenticated collection list/search request and
   create or update a disposable staging record.
5. **Attachments:** upload an allowed test file, download it, verify its
   metadata, then remove the disposable record/file according to the API
   workflow.
6. **Notifications:** trigger or use a staging event, list notifications, and
   mark one notification and all notifications as read.
7. **Audit:** confirm the collection operation produces an audit record that
   can be queried by an authorized user.
8. **Dependencies:** restart one dependency at a time and verify readiness
   fails clearly, recovers, and does not falsely report success.
9. **Persistence:** recreate application containers and confirm the
   administrator, database records, and uploaded test file remain available.
10. **Security boundary:** confirm external access reaches only ports 80/443;
    internal service, database, Redis, and RabbitMQ ports are not publicly
    reachable.

Disposable test data must use a documented staging prefix and be removed after
the smoke test unless retained as a fixture for repeatable checks.

## Release and rollback artifacts

Every staging or production release must retain:

- The exact image digest or commit-SHA tag for the frontend, gateway, and all
  domain services.
- The exact Compose files and proxy configuration used for the release.
- The migration revision reached by the database.
- The environment variable names and secret-store version identifiers, never
  the secret values themselves.
- The smoke-test result, deployment timestamp, and operator identity.
- The previous complete image/configuration set until the new release passes
  its observation window.

Rollback means restoring the previous image/configuration set and restarting
the stack. Database migrations must be backward-compatible with the previous
application version or have an explicitly reviewed down/forward recovery
procedure; an application rollback must never blindly destroy data.

## Phase gates

### Staging-ready gate

- Backend and frontend images build from a clean checkout without generated
  host artifacts.
- Compose networking uses service DNS names and dependency health checks.
- Migrations and idempotent bootstrap run successfully on an empty database.
- HTTPS, exact CORS, persistent uploads, and the smoke-test journey pass.
- Logs, health endpoints, and rollback artifacts are available.

### Production-ready gate

- A real hostname and certificate renewal process are configured.
- Secrets come from the selected secret manager or protected deployment
  secrets, with rotation ownership documented.
- Database and upload backups have been restored successfully in an isolated
  environment.
- Resource limits, alerts, log retention, and disk-capacity monitoring are
  active.
- A previous release has been rolled back successfully using only the recorded
  artifacts.
- The exhibition feature status is explicitly communicated; the current
  frontend/API mismatch is not silently presented as complete functionality.

## Phase 0 exit checklist

- [x] Release branch created without changing `master`.
- [x] Source baseline recorded.
- [x] Single-VM Compose target recorded.
- [x] Staging hostname and public URL placeholders defined.
- [x] Internal ports and dependency topology recorded.
- [x] Smoke-test journey defined.
- [x] Rollback artifacts and compatibility rule defined.
- [x] No credentials or tokens stored in the repository.

