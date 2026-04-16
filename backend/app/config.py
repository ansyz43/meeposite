import sys

from pydantic import model_validator
from pydantic_settings import BaseSettings

_INSECURE_DEFAULTS = {
    "super-secret-key-change-in-production",
    "changeme",
    "secret",
    "",
}


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://meepo:changeme@localhost:5432/meepo"
    SECRET_KEY: str = "super-secret-key-change-in-production"
    OPENAI_API_KEY: str = ""
    CORS_ORIGINS: str = "http://localhost:3000"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    UPLOAD_DIR: str = "uploads"
    MAX_AVATAR_SIZE: int = 5 * 1024 * 1024  # 5 MB

    COOKIE_SECURE: bool | None = None  # Auto-detected from CORS_ORIGINS if not set

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    SENTRY_DSN: str = ""
    TELEGRAM_API_URL: str = ""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    TELEGRAM_BOT_TOKEN_LOGIN: str = ""

    # Managed Bots — auto-creation via Bot API 9.6
    MANAGER_BOT_TOKEN: str = ""
    MANAGER_BOT_USERNAME: str = "Fitline01bot"

    # Content Plan — Telegram User API for channel parsing
    TELEGRAM_API_ID: int = 0
    TELEGRAM_API_HASH: str = ""
    TELEGRAM_SESSION_NAME: str = "content_parser"

    model_config = {"env_file": ".env"}

    @model_validator(mode="after")
    def _validate_secrets(self) -> "Settings":
        if self.SECRET_KEY in _INSECURE_DEFAULTS:
            print(
                "FATAL: SECRET_KEY is not set or uses a default value. "
                "Set a strong SECRET_KEY in .env before starting.",
                file=sys.stderr,
            )
            sys.exit(1)
        # Auto-detect COOKIE_SECURE from CORS_ORIGINS
        if self.COOKIE_SECURE is None:
            self.COOKIE_SECURE = any(
                o.strip().startswith("https://")
                for o in self.CORS_ORIGINS.split(",")
            )
        return self


settings = Settings()
