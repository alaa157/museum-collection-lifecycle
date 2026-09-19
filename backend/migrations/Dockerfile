FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY backend/auth-service/requirements.txt /tmp/auth-requirements.txt
COPY backend/collection-service/requirements.txt /tmp/collection-requirements.txt
COPY backend/conservation-service/requirements.txt /tmp/conservation-requirements.txt
COPY backend/loan-service/requirements.txt /tmp/loan-requirements.txt
COPY backend/notification-service/requirements.txt /tmp/notification-requirements.txt
COPY backend/audit-service/requirements.txt /tmp/audit-requirements.txt

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir \
        -r /tmp/auth-requirements.txt \
        -r /tmp/collection-requirements.txt \
        -r /tmp/conservation-requirements.txt \
        -r /tmp/loan-requirements.txt \
        -r /tmp/notification-requirements.txt \
        -r /tmp/audit-requirements.txt

COPY backend/auth-service/app /app/backend/auth-service/app
COPY backend/auth-service/alembic /app/backend/auth-service/alembic
COPY backend/auth-service/alembic.ini /app/backend/auth-service/alembic.ini
COPY backend/collection-service/app /app/backend/collection-service/app
COPY backend/collection-service/alembic /app/backend/collection-service/alembic
COPY backend/collection-service/alembic.ini /app/backend/collection-service/alembic.ini
COPY backend/conservation-service/app /app/backend/conservation-service/app
COPY backend/conservation-service/alembic /app/backend/conservation-service/alembic
COPY backend/conservation-service/alembic.ini /app/backend/conservation-service/alembic.ini
COPY backend/loan-service/app /app/backend/loan-service/app
COPY backend/loan-service/alembic /app/backend/loan-service/alembic
COPY backend/loan-service/alembic.ini /app/backend/loan-service/alembic.ini
COPY backend/notification-service/app /app/backend/notification-service/app
COPY backend/notification-service/alembic /app/backend/notification-service/alembic
COPY backend/notification-service/alembic.ini /app/backend/notification-service/alembic.ini
COPY backend/audit-service/app /app/backend/audit-service/app
COPY backend/audit-service/alembic /app/backend/audit-service/alembic
COPY backend/audit-service/alembic.ini /app/backend/audit-service/alembic.ini
COPY scripts/migrate-and-seed.sh /app/scripts/migrate-and-seed.sh

RUN chmod 0555 /app/scripts/migrate-and-seed.sh \
    && groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid 10001 --no-create-home app \
    && chown -R app:app /app

USER app

ENTRYPOINT ["/app/scripts/migrate-and-seed.sh"]
