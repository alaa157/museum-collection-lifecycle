from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from app.consumer import start_consumer
from app.db import Notification, engine, get_db
from app.security import current_user_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_consumer()
    yield
    engine.dispose()


app = FastAPI(
    title="Museum Notification Service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "notification-service"}


@app.get("/ready")
def ready():
    return {"status": "ready", "service": "notification-service"}


@app.get("/api/v1/notifications")
def list_notifications(
    user_id: int = Depends(current_user_id),
    db=Depends(get_db),
):
    return db.scalars(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(100)
    ).all()


@app.patch("/api/v1/notifications/{notification_id}/read")
def mark_read(
    notification_id: int,
    user_id: int = Depends(current_user_id),
    db=Depends(get_db),
):
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found.")

    notification.is_read = True
    db.commit()

    return notification


@app.post("/api/v1/notifications/read-all")
def mark_all_read(
    user_id: int = Depends(current_user_id),
    db=Depends(get_db),
):
    notifications = db.scalars(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
    ).all()

    for notification in notifications:
        notification.is_read = True

    db.commit()

    return {"updated": len(notifications)}
