from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / ".env").exists()),
    Path("/app"),
)


class Settings(BaseSettings):
    app_name: str = "Museum Collection Service"
    app_version: str = "1.0.0"

    collection_service_host: str = "127.0.0.1"
    collection_service_port: int = 8002

    database_host: str = "127.0.0.1"
    database_port: int = 5432
    database_name: str = "museum_collection"
    database_user: str = "postgres"
    database_password: str = "postgres"

    jwt_secret: str
    jwt_algorithm: str = "HS256"

    redis_host: str = "127.0.0.1"
    redis_port: int = 6379

    rabbitmq_host: str = "127.0.0.1"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"

    file_storage_path: str = "./storage"
    public_frontend_url: str = "http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", SERVICE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
