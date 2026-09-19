from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from pathlib import Path
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SERVICE_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = Path(__file__).resolve().parents[3]

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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
