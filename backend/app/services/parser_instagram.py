"""Instagram profile parser via instagrapi (Private API).

Uses a single authenticated session. Credentials in env.
Respects cache — skips profiles parsed < 24h ago.
Global rate limit: max 30 parse ops / hour.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from functools import partial
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
_client_lock = asyncio.Lock()
_SESSION_PATH = Path("/app/ig_session.json")


def _get_or_create_client():
    """Get or create instagrapi Client (sync). Thread-safe for executor."""
    global _client
    if _client is not None:
        return _client

    from instagrapi import Client

    if not settings.INSTAGRAM_USERNAME or not settings.INSTAGRAM_PASSWORD:
        raise RuntimeError("INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD not configured")

    cl = Client()
    cl.delay_range = [2, 5]

    # Try loading saved session
    if _SESSION_PATH.exists():
        try:
            cl.load_settings(_SESSION_PATH)
            cl.login(settings.INSTAGRAM_USERNAME, settings.INSTAGRAM_PASSWORD)
            logger.info("instagrapi: reused saved session")
            _client = cl
            return _client
        except Exception as e:
            logger.warning("instagrapi: saved session invalid, re-logging: %s", e)

    # Fresh login
    cl.login(settings.INSTAGRAM_USERNAME, settings.INSTAGRAM_PASSWORD)
    cl.dump_settings(_SESSION_PATH)
    logger.info("instagrapi: fresh login, session saved")
    _client = cl
    return _client


def _fetch_medias_sync(username: str, max_posts: int) -> list[dict] | dict:
    """Synchronous instagrapi fetch — runs in thread executor."""
    try:
        cl = _get_or_create_client()
    except RuntimeError as e:
        return {"error": str(e)}

    try:
        user_id = cl.user_id_from_username(username)
    except Exception as e:
        err_str = str(e).lower()
        if "not found" in err_str or "not exist" in err_str:
            return {"error": f"Профиль @{username} не найден"}
        return {"error": f"Ошибка Instagram: {e}"}

    try:
        medias = cl.user_medias(user_id, amount=max_posts)
    except Exception as e:
        return {"error": f"Не удалось загрузить посты: {e}"}

    posts = []
    for media in medias:
        text = media.caption_text or ""
        if not text.strip():
            continue
        posts.append({
            "text": text[:4000],
            "views": media.view_count,
            "reactions": media.like_count,
            "posted_at": media.taken_at,
        })

    # Save session after success
    try:
        cl.dump_settings(_SESSION_PATH)
    except Exception:
        pass

    return posts


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

    # Run sync instagrapi in executor to avoid blocking event loop
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        partial(_fetch_medias_sync, username, max_posts),
    )

    if isinstance(result, dict) and "error" in result:
        return {"status": "error", "error": result["error"], "posts_count": 0, "channel": username}

    posts_data = result
    if not posts_data:
        return {"status": "ok", "posts_count": 0, "channel": username}

    # Delete old cached posts
    await db.execute(
        CompetitorPost.__table__.delete().where(
            CompetitorPost.platform == "instagram",
            CompetitorPost.channel_username == username,
        )
    )

    now = datetime.now(timezone.utc)
    posts_saved = 0
    for p in posts_data:
        post = CompetitorPost(
            platform="instagram",
            channel_username=username,
            text=p["text"],
            views=p.get("views"),
            reactions=p.get("reactions"),
            posted_at=p.get("posted_at"),
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

    logger.info("Parsed IG profile @%s: %d posts", username, posts_saved)
    return {"status": "ok", "posts_count": posts_saved, "channel": username}
