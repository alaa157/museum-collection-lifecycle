from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.auth_routes import router as auth_router
from app.api.user_routes import router as user_router
from app.core.config import get_settings
from app.db.session import engine


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Authentication and authorization service.",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
def health():
    return {
        "status": "healthy",
        "service": "auth-service",
    }


@app.get("/ready", tags=["system"])
def readiness():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {
        "status": "ready",
        "service": "auth-service",
        "database": "reachable",
    }
