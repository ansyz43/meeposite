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
    # Optional — separate key for Fernet token encryption. If empty, falls back to SECRET_KEY
    # (backward-compatible). Set a distinct value for new deployments.
    ENCRYPTION_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""  # e.g. Cloudflare AI Gateway URL
    CF_AIG_TOKEN: str = ""  # Cloudflare AI Gateway auth token
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

    # Content Plan — Instagram parsing via instagrapi
    INSTAGRAM_USERNAME: str = ""
    INSTAGRAM_PASSWORD: str = ""
    INSTAGRAM_SESSION_ID: str = ""  # browser cookie sessionid — preferred over password login
    INSTAGRAM_PROXY: str = ""  # e.g. http://user:pass@host:port or socks5://user:pass@host:port
    INSTAGRAM_PARSER_ENABLED: bool = False  # Disabled by default until Graph API migration.

    # Tochka acquiring (https://developers.tochka.com)
    TOCHKA_JWT: str = ""
    TOCHKA_CUSTOMER_CODE: str = ""
    TOCHKA_BASE_URL: str = "https://enter.tochka.com/uapi/acquiring/v1.0"
    TOCHKA_REDIRECT_URL: str = "https://meepo.su/dashboard/profile?paid=1"
    TOCHKA_FAIL_URL: str = "https://meepo.su/dashboard/profile?paid=0"
    TOCHKA_WEBHOOK_SECRET: str = ""  # shared secret in webhook URL path
    TOCHKA_SUBSCRIPTION_AMOUNT: float = 10000.00  # ₽ per month

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
