from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://meepo:changeme@localhost:5432/meepo"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    CF_AIG_TOKEN: str = ""
    PROXY_SECRET: str = ""
    TELEGRAM_API_URL: str = ""
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALERT_CHAT_ID: str = ""  # Telegram chat_id for admin alerts
    ALERT_BOT_TOKEN: str = ""  # Bot token used to send alerts

    model_config = {"env_file": ".env"}


settings = Settings()
