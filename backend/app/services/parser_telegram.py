"""Telegram channel parser — disabled.

Telegram parsing is not supported in this version.
"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def parse_telegram_channel(
    username: str,
    db: AsyncSession,
    force: bool = False,
    max_posts: int = 50,
) -> dict:
    """Telegram parsing is disabled."""
    return {
        "status": "error",
        "error": "Парсинг Telegram не поддерживается. Используйте Instagram.",
        "posts_count": 0,
        "channel": username,
    }
