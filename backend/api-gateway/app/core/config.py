from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = Path(__file__).resolve().parents[4]

class Settings(BaseSettings):
    app_name: str = "Museum Collection Lifecycle API Gateway"
    app_version: str = "1.0.0"
    api_gateway_host: str = "127.0.0.1"
    api_gateway_port: int = 8000

    auth_service_url: str = "http://127.0.0.1:8001"
    collection_service_url: str = "http://127.0.0.1:8002"
    conservation_service_url: str = "http://127.0.0.1:8003"
    loan_service_url: str = "http://127.0.0.1:8004"
    notification_service_url: str = "http://127.0.0.1:8005"
    audit_service_url: str = "http://127.0.0.1:8006"

    cors_allowed_origins: str = "http://127.0.0.1:3000,http://localhost:3000"
    request_timeout_seconds: float = 15.0

    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", SERVICE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
