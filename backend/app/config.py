from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://meepo:changeme@localhost:5432/meepo"
    SECRET_KEY: str = "super-secret-key-change-in-production"
    OPENAI_API_KEY: str = ""
    CORS_ORIGINS: str = "http://localhost:3000"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    UPLOAD_DIR: str = "uploads"
    MAX_AVATAR_SIZE: int = 5 * 1024 * 1024  # 5 MB

    COOKIE_SECURE: bool = False  # Set True in production with HTTPS

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    TELEGRAM_BOT_TOKEN_LOGIN: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
