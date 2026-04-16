"""
Manager Bot polling service — receives ManagedBotUpdated via getUpdates
and auto-provisions new bots for users.

Flow:
  1. User clicks t.me/newbot/{MANAGER_USERNAME}/{suggested_username}
  2. Telegram delivers ManagedBotUpdated to manager bot
  3. We call getManagedBotToken(bot_user_id) → get token
  4. Encrypt token, create Bot row, mark PendingBotCreation as created
  5. bot_worker picks up the new bot via sync_bots
"""

import asyncio
import logging
import re
from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from app.models import Bot, PendingBotCreation, User
from app.services.crypto import encrypt_token

logger = logging.getLogger(__name__)

_POLL_TIMEOUT = 30  # long-polling timeout (seconds)
_offset: int = 0


def _api_url(method: str) -> str:
    """Build Telegram Bot API URL for the manager bot."""
    base = settings.TELEGRAM_API_URL.rstrip("/") if settings.TELEGRAM_API_URL else "https://api.telegram.org"
    return f"{base}/bot{settings.MANAGER_BOT_TOKEN}/{method}"


async def _get_updates(client: httpx.AsyncClient) -> list[dict]:
    """Long-poll for updates, filtering for managed_bot only."""
    global _offset
    try:
        resp = await client.post(
            _api_url("getUpdates"),
            json={
                "offset": _offset,
                "timeout": _POLL_TIMEOUT,
                "allowed_updates": ["managed_bot"],
            },
            timeout=_POLL_TIMEOUT + 10,
        )
        data = resp.json()
        if not data.get("ok"):
            logger.error("getUpdates error: %s", data)
            return []
        updates = data.get("result", [])
        if updates:
            _offset = updates[-1]["update_id"] + 1
        return updates
    except httpx.TimeoutException:
        return []
    except Exception:
        logger.exception("getUpdates failed")
        return []


async def _handle_managed_bot_update(update: dict) -> None:
    """Process a single ManagedBotUpdated."""
    managed = update.get("managed_bot")
    if not managed:
        return

    bot_info = managed.get("bot", {})
    user_info = managed.get("user", {})
    bot_tg_id = bot_info.get("id")
    bot_username = bot_info.get("username")
    creator_tg_id = user_info.get("id")

    if not bot_tg_id:
        logger.warning("ManagedBotUpdated without bot id, skipping")
        return

    logger.info(
        "ManagedBotUpdated: bot_id=%s username=%s creator_tg_id=%s",
        bot_tg_id, bot_username, creator_tg_id,
    )

    # 1. Get the token for the managed bot (with retry)
    token = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    _api_url("getManagedBotToken"),
                    json={"user_id": bot_tg_id},
                    timeout=15,
                )
                data = resp.json()
                if data.get("ok"):
                    token = data["result"]
                    break
                logger.error("getManagedBotToken failed (attempt %d): %s", attempt + 1, data)
        except Exception as e:
            logger.error("getManagedBotToken error (attempt %d): %s", attempt + 1, e)
        if attempt < 2:
            await asyncio.sleep(2 ** attempt)  # 1s, 2s

    if not token:
        logger.error("getManagedBotToken exhausted retries for bot %s", bot_tg_id)
        # Mark pending as failed so user can retry
        async with async_session() as db:
            if bot_username:
                result = await db.execute(
                    select(PendingBotCreation).where(
                        PendingBotCreation.suggested_username == bot_username,
                        PendingBotCreation.status == "pending",
                    ).limit(1)
                )
                pending = result.scalar_one_or_none()
                if pending:
                    pending.status = "failed"
                    pending.completed_at = datetime.utcnow()
                    await db.commit()
        return

    # 2. Find the platform user by matching on PendingBotCreation or telegram_id
    async with async_session() as db:
        # Try to find pending creation by suggested_username
        pending = None
        if bot_username:
            result = await db.execute(
                select(PendingBotCreation).where(
                    PendingBotCreation.suggested_username == bot_username,
                    PendingBotCreation.status == "pending",
                ).order_by(PendingBotCreation.created_at.desc()).limit(1)
            )
            pending = result.scalar_one_or_none()

        # Fallback: match by user_id pattern in username  (meepo_u{user_id}_bot)
        platform_user_id = None
        if pending:
            platform_user_id = pending.user_id
        elif bot_username:
            m = re.match(r"meepo_u(\d+)_bot", bot_username)
            if m:
                platform_user_id = int(m.group(1))

        # Last resort: match by creator's telegram_id
        if not platform_user_id and creator_tg_id:
            result = await db.execute(
                select(User.id).where(User.telegram_id == creator_tg_id).limit(1)
            )
            row = result.scalar_one_or_none()
            if row:
                platform_user_id = row

        if not platform_user_id:
            logger.warning("Cannot determine platform user for managed bot %s", bot_username)
            return

        # 3. Check user doesn't already have a telegram bot
        result = await db.execute(
            select(Bot).where(Bot.user_id == platform_user_id, Bot.platform == "telegram").limit(1)
        )
        existing = result.scalar_one_or_none()
        if existing:
            logger.info("User %s already has a telegram bot (id=%s), skipping", platform_user_id, existing.id)
            # Still mark pending as created
            if pending:
                pending.status = "created"
                pending.bot_telegram_id = bot_tg_id
                pending.bot_id = existing.id
                pending.completed_at = datetime.utcnow()
                await db.commit()
            return

        # 4. Load user to get name
        result = await db.execute(select(User).where(User.id == platform_user_id).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            logger.warning("User id=%s not found", platform_user_id)
            return

        # 5. Create Bot record
        suggested_name = pending.suggested_name if pending else f"Ассистент {user.name}"
        new_bot = Bot(
            user_id=user.id,
            platform="telegram",
            bot_token_encrypted=encrypt_token(token),
            bot_username=bot_username,
            assistant_name=suggested_name,
            seller_link=None,
            greeting_message=f"Привет! Я ассистент {user.name}. Чем могу помочь?",
            bot_description=f"{suggested_name} — ваш персональный помощник по продукции FitLine",
            is_active=True,
        )
        db.add(new_bot)
        await db.flush()

        # 6. Set bot name & description via TG API
        bot_api_base = (
            f"{settings.TELEGRAM_API_URL.rstrip('/')}/bot{token}"
            if settings.TELEGRAM_API_URL
            else f"https://api.telegram.org/bot{token}"
        )
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{bot_api_base}/setMyName",
                    json={"name": suggested_name},
                    timeout=10,
                )
                desc = new_bot.bot_description or ""
                if desc:
                    await client.post(
                        f"{bot_api_base}/setMyDescription",
                        json={"description": desc[:512]},
                        timeout=10,
                    )
                    await client.post(
                        f"{bot_api_base}/setMyShortDescription",
                        json={"short_description": desc[:120]},
                        timeout=10,
                    )
        except Exception as e:
            logger.warning("Failed to set managed bot info: %s", e)

        # 7. Update pending record
        if pending:
            pending.status = "created"
            pending.bot_telegram_id = bot_tg_id
            pending.bot_id = new_bot.id
            pending.completed_at = datetime.utcnow()

        await db.commit()
        logger.info(
            "Managed bot provisioned: bot_id=%s username=%s for user_id=%s",
            new_bot.id, bot_username, user.id,
        )


async def run_manager_bot_polling() -> None:
    """Main polling loop — runs as a background task during app lifespan."""
    if not settings.MANAGER_BOT_TOKEN:
        logger.info("MANAGER_BOT_TOKEN not set, manager bot polling disabled")
        return

    # Only one gunicorn worker should poll — use file lock
    try:
        import fcntl
        _lock_fd = open("/tmp/manager_bot_polling.lock", "w")
        fcntl.flock(_lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (ImportError, OSError):
        logger.info("Another worker is already polling manager bot, skipping")
        return

    logger.info("Starting manager bot polling (username=%s)", settings.MANAGER_BOT_USERNAME)

    async with httpx.AsyncClient() as client:
        while True:
            try:
                updates = await _get_updates(client)
                for upd in updates:
                    try:
                        await _handle_managed_bot_update(upd)
                    except Exception:
                        logger.exception("Error handling managed_bot update %s", upd.get("update_id"))
            except asyncio.CancelledError:
                logger.info("Manager bot polling stopped")
                return
            except Exception:
                logger.exception("Manager bot polling error, retrying in 5s")
                await asyncio.sleep(5)
