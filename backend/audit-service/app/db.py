from functools import lru_cache
from datetime import datetime
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import DateTime, Integer, JSON, String, Text, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

SERVICE_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / ".env").exists()),
    Path("/app"),
)

class Settings(BaseSettings):
    database_host: str = "127.0.0.1"
    database_port: int = 5432
    database_name: str = "museum_collection"
    database_user: str = "postgres"
    database_password: str = "postgres"

    jwt_secret: str
    jwt_algorithm: str = "HS256"

    rabbitmq_host: str = "127.0.0.1"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"

    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", SERVICE_DIR / ".env"),
        extra="ignore",
    )

    @property
    def database_url(self):
        return (
            f"postgresql+psycopg://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True)
    action: Mapped[str] = mapped_column(String(150), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(150))
    entity_id: Mapped[str | None] = mapped_column(String(150))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    ip_address: Mapped[str | None] = mapped_column(String(64))
    correlation_id: Mapped[str | None] = mapped_column(String(100))
    old_state: Mapped[dict | None] = mapped_column(JSON)
    new_state: Mapped[dict | None] = mapped_column(JSON)
    event_payload: Mapped[dict] = mapped_column(JSON, nullable=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
