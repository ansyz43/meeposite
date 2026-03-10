from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://meepo:changeme@localhost:5432/meepo"
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
