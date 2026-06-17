import logging

from pydantic import ConfigDict, field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://monitor_user:monitor_pass@postgres:5432/website_monitor"

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    EMAIL_TO: str = ""

    # App
    APP_ENV: str = "development"

    model_config = ConfigDict(env_file=".env", extra="ignore")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if isinstance(value, str):
            if value.startswith("postgres://"):
                normalized = value.replace("postgres://", "postgresql+asyncpg://", 1)
                logger.info("Normalized DATABASE_URL from postgres:// to postgresql+asyncpg://")
                return normalized
            if value.startswith("postgresql://"):
                normalized = value.replace("postgresql://", "postgresql+asyncpg://", 1)
                logger.info("Normalized DATABASE_URL from postgresql:// to postgresql+asyncpg://")
                return normalized
        return value


settings = Settings()
