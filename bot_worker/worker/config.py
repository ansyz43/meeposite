from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://meepo:changeme@localhost:5432/meepo"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    PROXY_SECRET: str = ""
    TELEGRAM_API_URL: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
