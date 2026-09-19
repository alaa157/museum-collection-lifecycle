from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / ".env").exists()),
    Path("/app"),
)


class Settings(BaseSettings):
    app_name: str = "Museum Collection Lifecycle Auth Service"
    app_version: str = "1.0.0"
    auth_service_host: str = "127.0.0.1"
    auth_service_port: int = 8001
    auth_cookie_secure: bool = False

    database_host: str = "127.0.0.1"
    database_port: int = 5432
    database_name: str = "museum_collection"
    database_user: str = "postgres"
    database_password: str = "postgres"

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    cors_allowed_origins: str = "http://127.0.0.1:3000,http://localhost:3000"

    seed_admin_email: str = "admin@museum.org"
    seed_admin_password: str = "ChangeThisPassword123!"
    seed_admin_first_name: str = "System"
    seed_admin_last_name: str = "Administrator"

    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", SERVICE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_allowed_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
