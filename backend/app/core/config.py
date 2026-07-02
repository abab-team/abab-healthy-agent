from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    APP_NAME: str = "family-health-agent"
    ENV: str = "development"
    DEBUG: bool = False
    DATABASE_URL: str = ""
    SECRET_KEY: str = ""
    CORS_ORIGINS: str = ""
    LLM_PROVIDER: str = "mock"
    LOCAL_STORAGE_DIR: str = "backend/storage/local"

    model_config = SettingsConfigDict(
        env_file=(
            PROJECT_ROOT / ".env",
            BACKEND_DIR / ".env",
        ),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        if not self.CORS_ORIGINS:
            return []
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
