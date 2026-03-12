import asyncio
import logging
import os
import time
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.models import User, Bot, Contact, Broadcast
from app.schemas import BroadcastResponse
from app.auth import get_current_user
from app.services.crypto import decrypt_token
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bot", tags=["broadcast"])

TELEGRAM_API = "https://api.telegram.org/bot{token}"


async def _get_user_bot(user: User, db: AsyncSession) -> Bot:
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(User).options(selectinload(User.bot)).where(User.id == user.id)
    )
    u = result.scalar_one()
    if not u.bot:
        raise HTTPException(status_code=404, detail="Нет подключённого бота")
    return u.bot


@router.post("/broadcast", response_model=BroadcastResponse, status_code=201)
async def create_broadcast(
    message_text: str = Form(..., min_length=1, max_length=4096),
    image: UploadFile | None = File(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot = await _get_user_bot(user, db)

    # Count contacts
    count_result = await db.execute(
        select(sa_func.count(Contact.id)).where(Contact.bot_id == bot.id)
    )
    total = count_result.scalar() or 0
    if total == 0:
        raise HTTPException(status_code=400, detail="У бота нет контактов для рассылки")

    # Handle image upload
    image_url = None
    if image and image.filename:
        if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
            raise HTTPException(status_code=400, detail="Только JPEG, PNG или WEBP")
        content = await image.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Максимум 5 МБ")
        upload_dir = Path(settings.UPLOAD_DIR) / "broadcasts"
        upload_dir.mkdir(parents=True, exist_ok=True)
        ext = image.filename.rsplit(".", 1)[-1] if "." in image.filename else "jpg"
        filename = f"bc_{bot.id}_{int(time.time())}.{ext}"
        filepath = upload_dir / filename
        with open(filepath, "wb") as f:
            f.write(content)
        image_url = f"/uploads/broadcasts/{filename}"

    broadcast = Broadcast(
        bot_id=bot.id,
        message_text=message_text,
        image_url=image_url,
        total_contacts=total,
        status="pending",
    )
    db.add(broadcast)
    await db.commit()
    await db.refresh(broadcast)

    # Fire background task
    asyncio.create_task(_send_broadcast(broadcast.id, bot.id, bot.bot_token_encrypted))

    return broadcast


@router.get("/broadcasts", response_model=list[BroadcastResponse])
async def list_broadcasts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot = await _get_user_bot(user, db)
    result = await db.execute(
        select(Broadcast)
        .where(Broadcast.bot_id == bot.id)
        .order_by(Broadcast.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()


async def _send_broadcast(broadcast_id: int, bot_id: int, token_encrypted: str):
    """Background task: send broadcast message to all bot contacts."""
    token = decrypt_token(token_encrypted)
    api_url = TELEGRAM_API.format(token=token)

    async with async_session() as db:
        # Mark as sending
        bc = await db.get(Broadcast, broadcast_id)
        if not bc:
            return
        bc.status = "sending"
        await db.commit()

        # Load broadcast data
        message_text = bc.message_text
        image_url = bc.image_url
        image_path = None
        if image_url:
            image_path = Path(settings.UPLOAD_DIR) / image_url.lstrip("/uploads/")

        # Get all contacts
        result = await db.execute(
            select(Contact.telegram_id).where(Contact.bot_id == bot_id)
        )
        contact_ids = [row[0] for row in result.all()]

    sent = 0
    failed = 0

    async with httpx.AsyncClient(timeout=30) as client:
        for i, chat_id in enumerate(contact_ids):
            try:
                if image_path and image_path.exists():
                    with open(image_path, "rb") as f:
                        resp = await client.post(
                            f"{api_url}/sendPhoto",
                            data={"chat_id": chat_id, "caption": message_text, "parse_mode": "HTML"},
                            files={"photo": (image_path.name, f, "image/jpeg")},
                        )
                else:
                    resp = await client.post(
                        f"{api_url}/sendMessage",
                        json={"chat_id": chat_id, "text": message_text, "parse_mode": "HTML"},
                    )

                if resp.status_code == 200 and resp.json().get("ok"):
                    sent += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

            # Rate limit: ~25 messages per second
            if (i + 1) % 25 == 0:
                await asyncio.sleep(1)

            # Update counts every 50 messages
            if (i + 1) % 50 == 0:
                async with async_session() as db:
                    bc = await db.get(Broadcast, broadcast_id)
                    if bc:
                        bc.sent_count = sent
                        bc.failed_count = failed
                        await db.commit()

    # Final update
    async with async_session() as db:
        bc = await db.get(Broadcast, broadcast_id)
        if bc:
            bc.sent_count = sent
            bc.failed_count = failed
            bc.status = "completed"
            await db.commit()

    logger.info(f"Broadcast {broadcast_id} done: sent={sent}, failed={failed}")
