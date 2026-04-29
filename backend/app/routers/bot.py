import os
import time
import datetime
import logging
import httpx
from pathlib import Path
from PIL import Image
from io import BytesIO
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models import User, Bot, ReferralPartner, PendingBotCreation
from app.schemas import BotUpdateRequest, BotResponse, BotStatusResponse, VkConnectRequest, CreateBotRequest, CreateBotResponse, CreationStatusResponse
from app.auth import get_current_user
from app.config import settings
from app.services.crypto import decrypt_token, encrypt_token
from app.services.subscription import require_active_subscription

router = APIRouter(prefix="/api/bot", tags=["bot"])

TERMS_VERSION = "2025-04-07"


def _tg_api(token: str) -> str:
    """Return Telegram API base URL for a given bot token."""
    if settings.TELEGRAM_API_URL:
        return f"{settings.TELEGRAM_API_URL.rstrip('/')}/bot{token}"
    return f"https://api.telegram.org/bot{token}"


VK_API = "https://api.vk.com/method"


async def _load_user_bots(user: User, db: AsyncSession) -> User:
    result = await db.execute(
        select(User).options(selectinload(User.bots)).where(User.id == user.id)
    )
    return result.scalar_one()


def _get_bot_by_platform(user: User, platform: str = "telegram") -> Bot | None:
    for b in user.bots:
        if b.platform == platform:
            return b
    return None


# ── Telegram bot endpoints ──

@router.post("/claim", response_model=BotResponse, status_code=201)
async def claim_bot(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Assign a free bot from the pool to the current user. DISABLED — use /create instead."""
    raise HTTPException(status_code=410, detail="Используйте кнопку «Создать бота» для создания нового бота")


@router.get("", response_model=BotResponse | None)
async def get_bot(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await _load_user_bots(user, db)
    bot = _get_bot_by_platform(user, "telegram")
    if not bot:
        return None
    return _bot_response(bot)


@router.put("", response_model=BotResponse)
async def update_bot(
    data: BotUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await _load_user_bots(user, db)
    bot = _get_bot_by_platform(user, "telegram")
    if not bot:
        raise HTTPException(status_code=404, detail="No bot connected")

    bot.assistant_name = data.assistant_name
    bot.seller_link = data.seller_link
    bot.greeting_message = data.greeting_message
    bot.bot_description = data.bot_description
    if data.allow_partners is not None:
        bot.allow_partners = data.allow_partners

    # Update bot name in Telegram (non-blocking: save to DB even if TG API fails)
    try:
        token = decrypt_token(bot.bot_token_encrypted)
        base = _tg_api(token)
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{base}/setMyName",
                json={"name": data.assistant_name},
                timeout=10,
            )
            if data.bot_description:
                await client.post(
                    f"{base}/setMyDescription",
                    json={"description": data.bot_description[:512]},
                    timeout=10,
                )
                await client.post(
                    f"{base}/setMyShortDescription",
                    json={"short_description": data.bot_description[:120]},
                    timeout=10,
                )
    except Exception as e:
        logger.warning(f"Failed to update bot info in Telegram: {e}")

    await db.commit()
    await db.refresh(bot)
    return _bot_response(bot)


@router.post("/avatar", response_model=BotResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await _load_user_bots(user, db)
    bot = _get_bot_by_platform(user, "telegram")
    if not bot:
        raise HTTPException(status_code=404, detail="No bot connected")

    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WEBP images are allowed")

    content = await file.read()
    if len(content) > settings.MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="File is too large (max 5MB)")

    try:
        img = Image.open(BytesIO(content))
        img.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    upload_dir = Path(settings.UPLOAD_DIR) / "avatars"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"bot_{bot.id}.png"
    filepath = upload_dir / filename

    img = Image.open(BytesIO(content))
    img = img.convert("RGB")
    img.thumbnail((512, 512))
    img.save(filepath, "PNG")

    bot.avatar_url = f"/uploads/avatars/{filename}?v={int(time.time())}"
    await db.commit()
    await db.refresh(bot)
    return _bot_response(bot)


@router.delete("")
async def disconnect_bot(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await _load_user_bots(user, db)
    bot = _get_bot_by_platform(user, "telegram")
    if not bot:
        raise HTTPException(status_code=404, detail="No bot connected")

    # Release bot back to pool
    bot.user_id = None
    bot.is_active = False
    bot.assistant_name = "Ассистент"
    bot.seller_link = None
    bot.greeting_message = None
    bot.bot_description = None
    bot.avatar_url = None
    bot.allow_partners = False

    # Deactivate orphaned partner records for this bot
    from sqlalchemy import update
    await db.execute(
        update(ReferralPartner)
        .where(ReferralPartner.bot_id == bot.id)
        .values(is_active=False)
    )

    await db.commit()
    return {"message": "Bot disconnected"}


@router.get("/status", response_model=BotStatusResponse)
async def bot_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await _load_user_bots(user, db)
    bot = _get_bot_by_platform(user, "telegram")
    if not bot:
        return BotStatusResponse(is_active=False, bot_username=None)
    return BotStatusResponse(is_active=bot.is_active, bot_username=bot.bot_username)


# ── Managed Bots (auto-creation) ──

@router.post("/create", response_model=CreateBotResponse)
async def create_bot(
    request: Request,
    data: CreateBotRequest | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a t.me/newbot link for managed bot creation."""
    # Require explicit acceptance of the public offer (or pre-accepted user)
    if not user.terms_accepted_at:
        if not data or not data.terms_accepted:
            raise HTTPException(
                status_code=400,
                detail="Необходимо принять условия Оферты и Политики обработки данных",
            )
        # Persist consent
        user.terms_accepted_at = datetime.datetime.utcnow()
        user.terms_version = TERMS_VERSION
        try:
            user.terms_ip = (request.client.host if request.client else None)
        except Exception:
            user.terms_ip = None
        # Re-attach to session (user from get_current_user may be detached)
        await db.merge(user)
        await db.commit()

    user = await _load_user_bots(user, db)
    active_tg = next((b for b in user.bots if b.platform == "telegram" and b.is_active), None)
    if active_tg:
        raise HTTPException(status_code=400, detail="У вас уже есть Telegram-бот")

    # Subscription gate (covers both TG and VK)
    await require_active_subscription(user, db)

    if not settings.MANAGER_BOT_TOKEN:
        raise HTTPException(status_code=503, detail="Автоматическое создание ботов не настроено")

    # Check for existing pending creation
    result = await db.execute(
        select(PendingBotCreation).where(
            PendingBotCreation.user_id == user.id,
            PendingBotCreation.status == "pending",
        ).limit(1)
    )
    existing_pending = result.scalar_one_or_none()
    if existing_pending:
        link = f"https://t.me/newbot/{settings.MANAGER_BOT_USERNAME}/{existing_pending.suggested_username}"
        if existing_pending.suggested_name:
            link += f"?name={quote(existing_pending.suggested_name)}"
        return CreateBotResponse(
            link=link,
            suggested_username=existing_pending.suggested_username,
            pending_id=existing_pending.id,
        )

    # Count previous attempts to generate unique username
    result = await db.execute(
        select(PendingBotCreation).where(
            PendingBotCreation.user_id == user.id,
        )
    )
    attempt_count = len(result.scalars().all())
    if attempt_count == 0:
        suggested_username = f"meepo_u{user.id}_bot"
    else:
        suggested_username = f"meepo_u{user.id}_{attempt_count}_bot"

    suggested_name = data.name if data and data.name else f"Ассистент {user.name}"

    pending = PendingBotCreation(
        user_id=user.id,
        suggested_username=suggested_username,
        suggested_name=suggested_name,
    )
    db.add(pending)
    await db.commit()
    await db.refresh(pending)

    link = f"https://t.me/newbot/{settings.MANAGER_BOT_USERNAME}/{suggested_username}"
    if suggested_name:
        link += f"?name={quote(suggested_name)}"

    return CreateBotResponse(
        link=link,
        suggested_username=suggested_username,
        pending_id=pending.id,
    )


@router.get("/creation-status", response_model=CreationStatusResponse)
async def creation_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if managed bot creation has completed."""
    result = await db.execute(
        select(PendingBotCreation).where(
            PendingBotCreation.user_id == user.id,
        ).order_by(PendingBotCreation.created_at.desc()).limit(1)
    )
    pending = result.scalar_one_or_none()
    if not pending:
        return CreationStatusResponse(status="none")

    if pending.status == "created":
        # Fetch the bot
        user = await _load_user_bots(user, db)
        bot = _get_bot_by_platform(user, "telegram")
        return CreationStatusResponse(
            status="created",
            bot=_bot_response(bot) if bot else None,
        )

    return CreationStatusResponse(status=pending.status)


# ── VK bot endpoints ──

@router.post("/vk/connect", response_model=BotResponse, status_code=201)
async def connect_vk_bot(
    data: VkConnectRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Connect a VK community bot."""
    user = await _load_user_bots(user, db)
    if _get_bot_by_platform(user, "vk"):
        raise HTTPException(status_code=400, detail="У вас уже есть VK-бот")

    # Subscription gate (one subscription covers both TG and VK)
    await require_active_subscription(user, db)

    # Verify VK token works by calling groups.getById
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{VK_API}/groups.getById",
                data={"access_token": data.group_token, "group_id": str(data.group_id), "v": "5.199"},
                timeout=10,
            )
            vk_data = resp.json()
            if "error" in vk_data:
                raise HTTPException(status_code=400, detail=f"Ошибка VK API: {vk_data['error'].get('error_msg', 'unknown')}")
            groups = vk_data.get("response", {}).get("groups", vk_data.get("response", []))
            if not groups:
                raise HTTPException(status_code=400, detail="Сообщество не найдено")
            group_info = groups[0] if isinstance(groups, list) else groups
            group_name = group_info.get("name", f"VK Group {data.group_id}")
            group_screen = group_info.get("screen_name", "")

            # Auto-enable Long Poll events (message_new, message_reply)
            await client.post(
                f"{VK_API}/groups.setLongPollSettings",
                data={
                    "access_token": data.group_token,
                    "group_id": str(data.group_id),
                    "enabled": "1",
                    "message_new": "1",
                    "message_reply": "1",
                    "v": "5.199",
                },
                timeout=10,
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Не удалось проверить токен VK: {e}")

    vk_bot = Bot(
        user_id=user.id,
        platform="vk",
        bot_token_encrypted=encrypt_token(data.group_token),
        bot_username=group_screen or None,
        vk_group_id=data.group_id,
        assistant_name=data.assistant_name,
        seller_link=data.seller_link,
        greeting_message=data.greeting_message,
        bot_description=data.bot_description or f"{data.assistant_name} — VK бот",
        is_active=True,
    )
    db.add(vk_bot)
    await db.commit()
    await db.refresh(vk_bot)
    return _bot_response(vk_bot)


@router.get("/vk", response_model=BotResponse | None)
async def get_vk_bot(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await _load_user_bots(user, db)
    bot = _get_bot_by_platform(user, "vk")
    if not bot:
        return None
    return _bot_response(bot)


@router.put("/vk", response_model=BotResponse)
async def update_vk_bot(
    data: BotUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await _load_user_bots(user, db)
    bot = _get_bot_by_platform(user, "vk")
    if not bot:
        raise HTTPException(status_code=404, detail="VK-бот не подключён")

    bot.assistant_name = data.assistant_name
    bot.seller_link = data.seller_link
    bot.greeting_message = data.greeting_message
    bot.bot_description = data.bot_description

    await db.commit()
    await db.refresh(bot)
    return _bot_response(bot)


@router.delete("/vk")
async def disconnect_vk_bot(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await _load_user_bots(user, db)
    bot = _get_bot_by_platform(user, "vk")
    if not bot:
        raise HTTPException(status_code=404, detail="VK-бот не подключён")

    await db.delete(bot)
    await db.commit()
    return {"message": "VK-бот отключён"}


# ── Helpers ──

def _bot_response(bot: Bot) -> BotResponse:
    return BotResponse(
        id=bot.id,
        platform=bot.platform,
        bot_username=bot.bot_username,
        assistant_name=bot.assistant_name,
        seller_link=bot.seller_link,
        greeting_message=bot.greeting_message,
        bot_description=bot.bot_description,
        avatar_url=bot.avatar_url,
        allow_partners=bot.allow_partners,
        is_active=bot.is_active,
        vk_group_id=bot.vk_group_id,
        created_at=bot.created_at,
    )
