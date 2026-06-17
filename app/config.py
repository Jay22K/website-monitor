from pydantic import ConfigDict
from pydantic_settings import BaseSettings


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


settings = Settings()
