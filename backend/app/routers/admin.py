import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import User, Bot, Contact, Message, Broadcast, ReferralPartner, ReferralSession, CashbackTransaction, PasswordResetToken
from app.auth import get_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ─── Stats ───────────────────────────────────────────
@router.get("/stats")
async def admin_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    active_users = (await db.execute(select(func.count(User.id)).where(User.is_active == True))).scalar() or 0
    total_bots = (await db.execute(select(func.count(Bot.id)))).scalar() or 0
    assigned_bots = (await db.execute(select(func.count(Bot.id)).where(Bot.user_id.isnot(None)))).scalar() or 0
    pool_bots = (await db.execute(select(func.count(Bot.id)).where(Bot.user_id.is_(None)))).scalar() or 0
    total_contacts = (await db.execute(select(func.count(Contact.id)))).scalar() or 0
    total_messages = (await db.execute(select(func.count(Message.id)))).scalar() or 0
    total_broadcasts = (await db.execute(select(func.count(Broadcast.id)))).scalar() or 0

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_bots": total_bots,
        "assigned_bots": assigned_bots,
        "pool_bots": pool_bots,
        "total_contacts": total_contacts,
        "total_messages": total_messages,
        "total_broadcasts": total_broadcasts,
    }


# ─── Users ───────────────────────────────────────────
@router.get("/users")
async def admin_list_users(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    search: str = Query("", max_length=100),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = select(User).options(selectinload(User.bots))
    count_query = select(func.count(User.id))

    if search:
        flt = or_(User.name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%"))
        query = query.where(flt)
        count_query = count_query.where(flt)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.order_by(User.created_at.desc()).limit(limit).offset(offset))
    users = result.scalars().all()

    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name,
                "is_active": u.is_active,
                "is_admin": u.is_admin,
                "auth_provider": u.auth_provider,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "bots": [
                    {
                        "id": b.id,
                        "platform": b.platform,
                        "bot_username": b.bot_username,
                        "is_active": b.is_active,
                    }
                    for b in u.bots
                ],
            }
            for u in users
        ],
        "total": total,
    }


@router.get("/users/{user_id}")
async def admin_get_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).options(selectinload(User.bots)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Count contacts and messages across all user's bots
    bot_ids = [b.id for b in user.bots]
    contacts_count = 0
    messages_count = 0
    if bot_ids:
        contacts_count = (await db.execute(
            select(func.count(Contact.id)).where(Contact.bot_id.in_(bot_ids))
        )).scalar() or 0
        messages_count = (await db.execute(
            select(func.count(Message.id)).where(
                Message.contact_id.in_(select(Contact.id).where(Contact.bot_id.in_(bot_ids)))
            )
        )).scalar() or 0

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "auth_provider": user.auth_provider,
        "telegram_id": user.telegram_id,
        "google_id": user.google_id,
        "ref_code": user.ref_code,
        "cashback_balance": float(user.cashback_balance or 0),
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "contacts_count": contacts_count,
        "messages_count": messages_count,
        "bots": [
            {
                "id": b.id,
                "platform": b.platform,
                "bot_username": b.bot_username,
                "assistant_name": b.assistant_name,
                "seller_link": b.seller_link,
                "is_active": b.is_active,
                "vk_group_id": b.vk_group_id,
            }
            for b in user.bots
        ],
    }


@router.delete("/users/{user_id}")
async def admin_delete_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).options(selectinload(User.bots)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Невозможно удалить администратора")

    # Release bots back to pool (don't delete them)
    for bot in user.bots:
        bot.user_id = None
        bot.seller_link = None
        bot.greeting_message = None
        bot.bot_description = None
        bot.avatar_url = None
        bot.assistant_name = "Ассистент"
        bot.allow_partners = False
        bot.is_active = False

    # Delete the user (cascades: contacts→messages, referral_partners→sessions, cashback_transactions, password_reset_tokens)
    await db.delete(user)
    await db.commit()

    logger.info(f"Admin {admin.email} deleted user {user.email} (id={user_id})")
    return {"detail": f"Пользователь {user.email} удалён"}


@router.patch("/users/{user_id}/toggle")
async def admin_toggle_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Невозможно деактивировать администратора")

    user.is_active = not user.is_active
    await db.commit()

    logger.info(f"Admin {admin.email} toggled user {user.email} is_active={user.is_active}")
    return {"id": user.id, "is_active": user.is_active}


# ─── Bots ────────────────────────────────────────────
@router.get("/bots")
async def admin_list_bots(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    search: str = Query("", max_length=100),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = select(Bot).options(selectinload(Bot.owner))
    count_query = select(func.count(Bot.id))

    if search:
        flt = Bot.bot_username.ilike(f"%{search}%")
        query = query.where(flt)
        count_query = count_query.where(flt)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.order_by(Bot.id).limit(limit).offset(offset))
    bots = result.scalars().all()

    # Get contact counts
    bot_ids = [b.id for b in bots]
    contact_counts = {}
    if bot_ids:
        counts_result = await db.execute(
            select(Contact.bot_id, func.count(Contact.id))
            .where(Contact.bot_id.in_(bot_ids))
            .group_by(Contact.bot_id)
        )
        contact_counts = dict(counts_result.all())

    return {
        "bots": [
            {
                "id": b.id,
                "platform": b.platform,
                "bot_username": b.bot_username,
                "assistant_name": b.assistant_name,
                "seller_link": b.seller_link,
                "is_active": b.is_active,
                "vk_group_id": b.vk_group_id,
                "owner_email": b.owner.email if b.owner else None,
                "owner_name": b.owner.name if b.owner else None,
                "contacts_count": contact_counts.get(b.id, 0),
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in bots
        ],
        "total": total,
    }


@router.delete("/bots/{bot_id}")
async def admin_delete_bot(
    bot_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")

    username = bot.bot_username
    await db.delete(bot)
    await db.commit()

    logger.info(f"Admin {admin.email} deleted bot @{username} (id={bot_id})")
    return {"detail": f"Бот @{username} удалён"}


# ─── Conversations ───────────────────────────────────
@router.get("/conversations/{contact_id}")
async def admin_view_conversation(
    contact_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    contact = (await db.execute(
        select(Contact).where(Contact.id == contact_id)
    )).scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Контакт не найден")

    total = (await db.execute(
        select(func.count(Message.id)).where(Message.contact_id == contact_id)
    )).scalar() or 0

    messages = (await db.execute(
        select(Message)
        .where(Message.contact_id == contact_id)
        .order_by(Message.created_at)
        .limit(limit)
        .offset(offset)
    )).scalars().all()

    return {
        "contact": {
            "id": contact.id,
            "platform": contact.platform,
            "telegram_id": contact.telegram_id,
            "vk_id": contact.vk_id,
            "telegram_username": contact.telegram_username,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "message_count": contact.message_count,
        },
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
        "total": total,
    }
