from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.db import engine
from app.api import router
from app.outbox_publisher import start_outbox_publisher


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_outbox_publisher()

    yield

    engine.dispose()


app = FastAPI(
    title="Museum Conservation Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(
    router,
    prefix="/api/v1/conservation",
)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "conservation-service",
    }


@app.get("/ready")
def ready():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "status": "ready",
        "service": "conservation-service",
    }