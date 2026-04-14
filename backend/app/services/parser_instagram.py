"""Instagram profile parser via Instaloader (anonymous mode).

Parses public profiles without login. Cache-first architecture.
Global rate limit: max 30 parse ops / hour.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from functools import partial

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CompetitorPost, CompetitorSource

logger = logging.getLogger(__name__)

_parse_timestamps: list[datetime] = []
_MAX_PARSES_PER_HOUR = 30
_CACHE_TTL_HOURS = 24


def _check_rate_limit() -> bool:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=1)
    _parse_timestamps[:] = [t for t in _parse_timestamps if t > cutoff]
    return len(_parse_timestamps) < _MAX_PARSES_PER_HOUR


def _fetch_instagram_sync(username: str, max_posts: int) -> list[dict]:
    """Synchronous Instaloader fetch — runs in thread executor."""
    try:
        import instaloader
    except ImportError:
        logger.error("instaloader not installed")
        return []

    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
    )

    try:
        profile = instaloader.Profile.from_username(loader.context, username)
    except instaloader.exceptions.ProfileNotExistsException:
        return [{"error": f"Профиль @{username} не найден"}]
    except instaloader.exceptions.ConnectionException as e:
        logger.warning("Instagram connection error for @%s: %s", username, e)
        return [{"error": f"Instagram заблокировал запрос. Попробуйте позже."}]

    posts = []
    for i, post in enumerate(profile.get_posts()):
        if i >= max_posts:
            break
        text = post.caption or ""
        if not text.strip():
            continue
        posts.append({
            "text": text[:4000],
            "views": post.video_view_count if post.is_video else None,
            "reactions": post.likes,
            "posted_at": post.date_utc,
        })

    return posts


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

    # Run sync instaloader in executor to avoid blocking event loop
    loop = asyncio.get_event_loop()
    posts_data = await loop.run_in_executor(
        None,
        partial(_fetch_instagram_sync, username, max_posts),
    )

    if not posts_data:
        return {"status": "error", "error": "Не удалось получить посты", "posts_count": 0, "channel": username}

    if len(posts_data) == 1 and "error" in posts_data[0]:
        return {"status": "error", "error": posts_data[0]["error"], "posts_count": 0, "channel": username}

    # Delete old cached posts
    await db.execute(
        CompetitorPost.__table__.delete().where(
            CompetitorPost.platform == "instagram",
            CompetitorPost.channel_username == username,
        )
    )

    now = datetime.now(timezone.utc)
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
    logger.info("Parsed IG profile @%s: %d posts", username, len(posts_data))
    return {"status": "ok", "posts_count": len(posts_data), "channel": username}
