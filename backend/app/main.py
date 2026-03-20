import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command

from app.config import settings
from app.database import engine, Base
from app.logging_config import setup_logging, RequestIDMiddleware
from app.routers import auth, profile, bot, conversations, referral, broadcast

setup_logging()
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run Alembic migrations on startup
    alembic_cfg = AlembicConfig(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini")
    )
    alembic_cfg.set_main_option(
        "script_location",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic"),
    )
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    try:
        alembic_command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations applied successfully")
    except Exception:
        logger.exception("Failed to apply database migrations")
        raise
    yield


app = FastAPI(title="Meepo API", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Слишком много запросов. Попробуйте позже."},
    )

# CORS
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)

# Static files for uploads
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Health check
@app.get("/api/health")
async def health_check():
    from app.database import async_session
    async with async_session() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ok"}

# Routers
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(bot.router)
app.include_router(conversations.router)
app.include_router(referral.router)
app.include_router(broadcast.router)
