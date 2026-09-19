from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import get_settings
from app.db.session import engine
from app.api import router
from app.consumer import start_consumer
from app.outbox_publisher import start_outbox_publisher


settings = get_settings()
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    start_consumer()
    start_outbox_publisher()
    yield
    engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Museum collection cataloging and lifecycle service.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1/collection")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "collection-service"}


@app.get("/ready")
def ready():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"status": "ready", "service": "collection-service"}

