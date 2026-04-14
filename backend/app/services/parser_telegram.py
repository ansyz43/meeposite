"""Telegram channel parser via Telethon (User API).

Uses a single server-side session. One-time auth required on first run.
Respects cache — skips channels parsed < 24h ago.
Global rate limit: max 50 parse ops / hour.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from telethon import TelegramClient
from telethon.errors import (
    ChannelPrivateError,
    UsernameNotOccupiedError,
    FloodWaitError,
)
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import CompetitorPost, CompetitorSource

logger = logging.getLogger(__name__)

# Global rate limiter — sliding window
_parse_timestamps: list[datetime] = []
_MAX_PARSES_PER_HOUR = 50
_CACHE_TTL_HOURS = 24

_client: TelegramClient | None = None
_lock = asyncio.Lock()


async def _get_client() -> TelegramClient:
    """Lazy-init singleton Telethon client."""
    global _client
    if _client is None or not _client.is_connected():
        async with _lock:
            if _client is None or not _client.is_connected():
                if not settings.TELEGRAM_API_ID or not settings.TELEGRAM_API_HASH:
                    raise RuntimeError("TELEGRAM_API_ID and TELEGRAM_API_HASH not configured")
                _client = TelegramClient(
                    settings.TELEGRAM_SESSION_NAME,
                    settings.TELEGRAM_API_ID,
                    settings.TELEGRAM_API_HASH,
                )
                await _client.connect()
                if not await _client.is_user_authorized():
                    raise RuntimeError(
                        "Telethon session not authorized. "
                        "Run auth interactively: docker exec -it meeposite-backend-1 python -m app.services.parser_telegram"
                    )
                logger.info("Telethon client connected")
    return _client


def _check_rate_limit() -> bool:
    """Return True if we can parse, False if rate-limited."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=1)
    _parse_timestamps[:] = [t for t in _parse_timestamps if t > cutoff]
    return len(_parse_timestamps) < _MAX_PARSES_PER_HOUR


async def parse_telegram_channel(
    username: str,
    db: AsyncSession,
    force: bool = False,
    max_posts: int = 50,
) -> dict:
    """Parse a public Telegram channel. Returns summary dict.

    Cache-first: if channel was parsed < 24h ago, return cached count.
    """
    username = username.lstrip("@").strip().lower()

    # Check cache
    if not force:
        cached = await db.execute(
            select(sa_func.count(CompetitorPost.id)).where(
                CompetitorPost.platform == "telegram",
                CompetitorPost.channel_username == username,
                CompetitorPost.parsed_at > datetime.now(timezone.utc) - timedelta(hours=_CACHE_TTL_HOURS),
            )
        )
        cached_count = cached.scalar() or 0
        if cached_count > 0:
            return {"status": "cached", "posts_count": cached_count, "channel": username}

    # Rate limit
    if not _check_rate_limit():
        return {"status": "rate_limited", "posts_count": 0, "channel": username}

    try:
        client = await _get_client()
    except RuntimeError as e:
        logger.warning("Telethon not available: %s", e)
        return {"status": "error", "error": str(e), "posts_count": 0, "channel": username}

    try:
        entity = await client.get_entity(username)
        channel_title = getattr(entity, "title", username)
    except UsernameNotOccupiedError:
        return {"status": "error", "error": f"Канал @{username} не найден", "posts_count": 0, "channel": username}
    except ChannelPrivateError:
        return {"status": "error", "error": f"Канал @{username} приватный", "posts_count": 0, "channel": username}
    except FloodWaitError as e:
        logger.warning("Telegram flood wait: %s seconds", e.seconds)
        return {"status": "rate_limited", "posts_count": 0, "channel": username}

    # Delete old cached posts for this channel
    await db.execute(
        CompetitorPost.__table__.delete().where(
            CompetitorPost.platform == "telegram",
            CompetitorPost.channel_username == username,
        )
    )

    # Fetch messages
    posts_saved = 0
    now = datetime.now(timezone.utc)
    async for message in client.iter_messages(entity, limit=max_posts):
        if not message.text:
            continue
        post = CompetitorPost(
            platform="telegram",
            channel_username=username,
            text=message.text[:4000],  # cap at 4000 chars
            views=message.views,
            reactions=sum(r.count for r in (message.reactions.results if message.reactions else [])),
            posted_at=message.date,
            parsed_at=now,
        )
        db.add(post)
        posts_saved += 1

    _parse_timestamps.append(now)

    # Update source last_parsed_at for all users tracking this channel
    await db.execute(
        CompetitorSource.__table__.update()
        .where(
            CompetitorSource.platform == "telegram",
            CompetitorSource.channel_username == username,
        )
        .values(last_parsed_at=now, channel_title=channel_title)
    )

    await db.commit()
    logger.info("Parsed TG channel @%s: %d posts", username, posts_saved)
    return {"status": "ok", "posts_count": posts_saved, "channel": username, "title": channel_title}


# ── Interactive auth (run once on server) ───────────────────
if __name__ == "__main__":
    import sys

    async def _auth():
        if not settings.TELEGRAM_API_ID or not settings.TELEGRAM_API_HASH:
            print("Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env first")
            sys.exit(1)
        client = TelegramClient(
            settings.TELEGRAM_SESSION_NAME,
            settings.TELEGRAM_API_ID,
            settings.TELEGRAM_API_HASH,
        )
        await client.start()
        me = await client.get_me()
        print(f"Authorized as {me.first_name} (ID: {me.id})")
        await client.disconnect()

    asyncio.run(_auth())
