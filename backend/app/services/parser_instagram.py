"""Instagram profile parser via aiograpi (Private API).

Uses a single authenticated session. Credentials in env.
Respects cache — skips profiles parsed < 24h ago.
Global rate limit: max 30 parse ops / hour.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import CompetitorPost, CompetitorSource

logger = logging.getLogger(__name__)

_parse_timestamps: list[datetime] = []
_MAX_PARSES_PER_HOUR = 30
_CACHE_TTL_HOURS = 24

_client = None
_lock = asyncio.Lock()
_SESSION_PATH = Path("/app/ig_session.json")


async def _get_client():
    """Lazy-init singleton aiograpi Client with session persistence."""
    global _client
    if _client is not None:
        return _client

    async with _lock:
        if _client is not None:
            return _client

        from aiograpi import Client

        if not settings.INSTAGRAM_USERNAME or not settings.INSTAGRAM_PASSWORD:
            raise RuntimeError("INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD not configured")

        cl = Client()
        cl.delay_range = [2, 5]

        # Try loading saved session
        if _SESSION_PATH.exists():
            try:
                saved = json.loads(_SESSION_PATH.read_text())
                cl.set_settings(saved)
                await cl.login(settings.INSTAGRAM_USERNAME, settings.INSTAGRAM_PASSWORD)
                logger.info("aiograpi: reused saved session")
                _client = cl
                return _client
            except Exception as e:
                logger.warning("aiograpi: saved session invalid, re-logging: %s", e)

        # Fresh login
        await cl.login(settings.INSTAGRAM_USERNAME, settings.INSTAGRAM_PASSWORD)
        _SESSION_PATH.write_text(json.dumps(cl.get_settings(), default=str))
        logger.info("aiograpi: fresh login, session saved")
        _client = cl
        return _client


def _check_rate_limit() -> bool:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=1)
    _parse_timestamps[:] = [t for t in _parse_timestamps if t > cutoff]
    return len(_parse_timestamps) < _MAX_PARSES_PER_HOUR


async def parse_instagram_profile(
    username: str,
    db: AsyncSession,
    force: bool = False,
    max_posts: int = 20,
) -> dict:
    """Parse a public Instagram profile. Returns summary dict."""
    username = username.lstrip("@").strip().lower()

    # Check cache
    if not force:
        cached = await db.execute(
            select(sa_func.count(CompetitorPost.id)).where(
                CompetitorPost.platform == "instagram",
                CompetitorPost.channel_username == username,
                CompetitorPost.parsed_at > datetime.now(timezone.utc) - timedelta(hours=_CACHE_TTL_HOURS),
            )
        )
        cached_count = cached.scalar() or 0
        if cached_count > 0:
            return {"status": "cached", "posts_count": cached_count, "channel": username}

    if not _check_rate_limit():
        return {"status": "rate_limited", "posts_count": 0, "channel": username}

    try:
        cl = await _get_client()
    except RuntimeError as e:
        logger.warning("aiograpi not available: %s", e)
        return {"status": "error", "error": str(e), "posts_count": 0, "channel": username}

    # Resolve user
    try:
        user_id = await cl.user_id_from_username(username)
    except Exception as e:
        err_str = str(e).lower()
        if "not found" in err_str or "not exist" in err_str:
            return {"status": "error", "error": f"Профиль @{username} не найден", "posts_count": 0, "channel": username}
        logger.warning("aiograpi user lookup error for @%s: %s", username, e)
        return {"status": "error", "error": f"Ошибка Instagram: {e}", "posts_count": 0, "channel": username}

    # Fetch medias
    try:
        medias = await cl.user_medias(user_id, amount=max_posts)
    except Exception as e:
        logger.warning("aiograpi medias error for @%s: %s", username, e)
        return {"status": "error", "error": f"Не удалось загрузить посты: {e}", "posts_count": 0, "channel": username}

    # Delete old cached posts
    await db.execute(
        CompetitorPost.__table__.delete().where(
            CompetitorPost.platform == "instagram",
            CompetitorPost.channel_username == username,
        )
    )

    now = datetime.now(timezone.utc)
    posts_saved = 0
    for media in medias:
        text = media.caption_text or ""
        if not text.strip():
            continue
        post = CompetitorPost(
            platform="instagram",
            channel_username=username,
            text=text[:4000],
            views=media.view_count,
            reactions=media.like_count,
            posted_at=media.taken_at,
            parsed_at=now,
        )
        db.add(post)
        posts_saved += 1

    _parse_timestamps.append(now)

    await db.execute(
        CompetitorSource.__table__.update()
        .where(
            CompetitorSource.platform == "instagram",
            CompetitorSource.channel_username == username,
        )
        .values(last_parsed_at=now)
    )

    await db.commit()

    # Save session after successful operation
    try:
        _SESSION_PATH.write_text(json.dumps(cl.get_settings(), default=str))
    except Exception:
        pass

    logger.info("Parsed IG profile @%s: %d posts", username, posts_saved)
    return {"status": "ok", "posts_count": posts_saved, "channel": username}
