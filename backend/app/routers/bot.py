import os
import time
import logging
import httpx
from pathlib import Path
from PIL import Image
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models import User, Bot
from app.schemas import BotUpdateRequest, BotResponse, BotStatusResponse
from app.auth import get_current_user
from app.config import settings
from app.services.crypto import decrypt_token

router = APIRouter(prefix="/api/bot", tags=["bot"])

TELEGRAM_API = "https://api.telegram.org/bot{token}"


async def get_user_with_bot(user: User, db: AsyncSession) -> User:
    result = await db.execute(
        select(User).options(selectinload(User.bot)).where(User.id == user.id)
    )
    return result.scalar_one()


@router.post("/claim", response_model=BotResponse, status_code=201)
async def claim_bot(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Assign a free bot from the pool to the current user."""
    user = await get_user_with_bot(user, db)
    if user.bot:
        raise HTTPException(status_code=400, detail="У вас уже есть бот")

    # Find an unassigned bot
    result = await db.execute(
        select(Bot).where(Bot.user_id.is_(None)).order_by(Bot.id).limit(1)
    )
    free_bot = result.scalar_one_or_none()
    if not free_bot:
        raise HTTPException(status_code=409, detail="Нет свободных ботов. Обратитесь к администратору.")

    free_bot.user_id = user.id
    free_bot.assistant_name = f"Ассистент {user.name}"
    free_bot.greeting_message = f"Привет! Я ассистент {user.name}. Чем могу помочь?"
    free_bot.bot_description = f"{free_bot.assistant_name} — ваш персональный помощник по продукции FitLine"
    free_bot.is_active = True

    # Set bot info in Telegram API
    try:
        token = decrypt_token(free_bot.bot_token_encrypted)
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{TELEGRAM_API.format(token=token)}/getMe", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    free_bot.bot_username = data["result"].get("username")
            # Set bot display name
            await client.post(
                f"{TELEGRAM_API.format(token=token)}/setMyName",
                json={"name": free_bot.assistant_name},
                timeout=10,
            )
            # Set description (visible before /start)
            if free_bot.bot_description:
                await client.post(
                    f"{TELEGRAM_API.format(token=token)}/setMyDescription",
                    json={"description": free_bot.bot_description[:512]},
                    timeout=10,
                )
                await client.post(
                    f"{TELEGRAM_API.format(token=token)}/setMyShortDescription",
                    json={"short_description": free_bot.bot_description[:120]},
                    timeout=10,
                )
    except Exception as e:
        logger.warning(f"Failed to set bot info in Telegram: {e}")

    await db.commit()
    await db.refresh(free_bot)
    return _bot_response(free_bot)


@router.get("", response_model=BotResponse | None)
async def get_bot(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_with_bot(user, db)
    if not user.bot:
        return None
    return _bot_response(user.bot)


@router.put("", response_model=BotResponse)
async def update_bot(
    data: BotUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_with_bot(user, db)
    if not user.bot:
        raise HTTPException(status_code=404, detail="No bot connected")

    user.bot.assistant_name = data.assistant_name
    user.bot.seller_link = data.seller_link
    user.bot.greeting_message = data.greeting_message
    user.bot.bot_description = data.bot_description
    if data.allow_partners is not None:
        user.bot.allow_partners = data.allow_partners

    # Update bot name in Telegram
    token = decrypt_token(user.bot.bot_token_encrypted)
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{TELEGRAM_API.format(token=token)}/setMyName",
            json={"name": data.assistant_name},
            timeout=10,
        )
        if data.bot_description:
            await client.post(
                f"{TELEGRAM_API.format(token=token)}/setMyDescription",
                json={"description": data.bot_description[:512]},
                timeout=10,
            )
            await client.post(
                f"{TELEGRAM_API.format(token=token)}/setMyShortDescription",
                json={"short_description": data.bot_description[:120]},
                timeout=10,
            )

    await db.commit()
    await db.refresh(user.bot)
    return _bot_response(user.bot)


@router.post("/avatar", response_model=BotResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_with_bot(user, db)
    if not user.bot:
        raise HTTPException(status_code=404, detail="No bot connected")

    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WEBP images are allowed")

    content = await file.read()
    if len(content) > settings.MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="File is too large (max 5MB)")

    # Validate it's actually an image
    try:
        img = Image.open(BytesIO(content))
        img.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    upload_dir = Path(settings.UPLOAD_DIR) / "avatars"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"bot_{user.bot.id}.png"
    filepath = upload_dir / filename

    # Re-open and save as PNG
    img = Image.open(BytesIO(content))
    img = img.convert("RGB")
    img.thumbnail((512, 512))
    img.save(filepath, "PNG")

    user.bot.avatar_url = f"/uploads/avatars/{filename}?v={int(time.time())}"
    await db.commit()
    await db.refresh(user.bot)
    return _bot_response(user.bot)


@router.delete("")
async def disconnect_bot(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_with_bot(user, db)
    if not user.bot:
        raise HTTPException(status_code=404, detail="No bot connected")

    # Release bot back to pool
    user.bot.user_id = None
    user.bot.is_active = False
    user.bot.assistant_name = "Ассистент"
    user.bot.seller_link = None
    user.bot.greeting_message = None
    user.bot.bot_description = None
    user.bot.avatar_url = None
    await db.commit()
    return {"message": "Bot disconnected"}


@router.get("/status", response_model=BotStatusResponse)
async def bot_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_with_bot(user, db)
    if not user.bot:
        return BotStatusResponse(is_active=False, bot_username=None)
    return BotStatusResponse(is_active=user.bot.is_active, bot_username=user.bot.bot_username)


def _bot_response(bot: Bot) -> BotResponse:
    return BotResponse(
        id=bot.id,
        bot_username=bot.bot_username,
        assistant_name=bot.assistant_name,
        seller_link=bot.seller_link,
        greeting_message=bot.greeting_message,
        bot_description=bot.bot_description,
        avatar_url=bot.avatar_url,
        allow_partners=bot.allow_partners,
        is_active=bot.is_active,
        created_at=bot.created_at,
    )
