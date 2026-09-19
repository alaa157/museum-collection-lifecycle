from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy import select
from app.consumer import start_consumer
from app.db import AuditLog, engine, get_db
from app.security import current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_consumer()
    yield
    engine.dispose()


app = FastAPI(
    title="Museum Audit Service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "audit-service"}


@app.get("/ready")
def ready():
    return {"status": "ready", "service": "audit-service"}


@app.get("/api/v1/audit")
def list_audit(
    user=Depends(current_user),
    db=Depends(get_db),
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    _user_id, roles = user

    if not roles.intersection({"ADMIN", "REGISTRAR", "CURATOR", "CONSERVATOR"}):
        raise HTTPException(
            status_code=403,
            detail="Audit access is restricted.",
        )

    statement = select(AuditLog).order_by(
        AuditLog.timestamp.desc()
    )

    if entity_type:
        statement = statement.where(
            AuditLog.entity_type == entity_type
        )

    if entity_id:
        statement = statement.where(
            AuditLog.entity_id == entity_id
        )

    return db.scalars(
        statement.limit(limit)
    ).all()
