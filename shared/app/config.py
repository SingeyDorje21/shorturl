from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Short URL Service"
    DEBUG: bool = True
    VERSION: str = "v1"
    ENVIRONMENT: str = "development"

    # Database — use aiosqlite for async; switch to postgresql+asyncpg in prod
    DATABASE_URL: str = "sqlite+aiosqlite:///./shorturl.db"

    # Security
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production-at-least-32-characters-long"
    )

    # CORS
    CORS_ORIGINS: str = "*"

    # URL Settings
    MAX_URL_LENGTH: int = 2048
    URL_ACTIVE_DAYS_DEFAULT: int = 30
    URL_ACTIVE_DAYS_MAX: int = 365

    # Service ports (used in docker-compose and gateway routing)
    GATEWAY_PORT: int = 8000
    SHORTENER_PORT: int = 8001
    REDIRECT_PORT: int = 8002
    CLEANUP_PORT: int = 8003

    # Internal base URLs (gateway uses these to forward requests)
    SHORTENER_BASE_URL: str = "http://shortener:8001"
    REDIRECT_BASE_URL: str = "http://redirect:8002"

    # Cleanup schedule (cron-style seconds interval)
    CLEANUP_INTERVAL_SECONDS: int = 3600  # run every hour

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    # SQLite does NOT support pool_size / max_overflow.
    # For Postgres, set these via env vars.
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.DATABASE_URL

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "env_file_encoding": "utf-8",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
