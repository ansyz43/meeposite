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

    total_partners = (await db.execute(select(func.count(ReferralPartner.id)))).scalar() or 0
    active_partners = (await db.execute(select(func.count(ReferralPartner.id)).where(ReferralPartner.is_active == True))).scalar() or 0
    total_sessions = (await db.execute(select(func.count(ReferralSession.id)))).scalar() or 0
    total_cashback = (await db.execute(select(func.coalesce(func.sum(CashbackTransaction.amount), 0)))).scalar() or 0

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_bots": total_bots,
        "assigned_bots": assigned_bots,
        "pool_bots": pool_bots,
        "total_contacts": total_contacts,
        "total_messages": total_messages,
        "total_broadcasts": total_broadcasts,
        "total_partners": total_partners,
        "active_partners": active_partners,
        "total_sessions": total_sessions,
        "total_cashback": float(total_cashback),
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


@router.get("/bots/{bot_id}")
async def admin_get_bot(
    bot_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bot).options(selectinload(Bot.owner)).where(Bot.id == bot_id)
    )
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")

    contacts_count = (await db.execute(
        select(func.count(Contact.id)).where(Contact.bot_id == bot_id)
    )).scalar() or 0

    messages_count = (await db.execute(
        select(func.count(Message.id)).where(
            Message.contact_id.in_(select(Contact.id).where(Contact.bot_id == bot_id))
        )
    )).scalar() or 0

    broadcasts_count = (await db.execute(
        select(func.count(Broadcast.id)).where(Broadcast.bot_id == bot_id)
    )).scalar() or 0

    # Referral partners for this bot
    partners_result = await db.execute(
        select(ReferralPartner)
        .options(selectinload(ReferralPartner.user))
        .where(ReferralPartner.bot_id == bot_id)
        .order_by(ReferralPartner.created_at.desc())
    )
    partners = partners_result.scalars().all()

    partner_ids = [p.id for p in partners]
    session_counts = {}
    if partner_ids:
        sc_result = await db.execute(
            select(ReferralSession.partner_id, func.count(ReferralSession.id))
            .where(ReferralSession.partner_id.in_(partner_ids))
            .group_by(ReferralSession.partner_id)
        )
        session_counts = dict(sc_result.all())

    return {
        "id": bot.id,
        "platform": bot.platform,
        "bot_username": bot.bot_username,
        "assistant_name": bot.assistant_name,
        "seller_link": bot.seller_link,
        "greeting_message": bot.greeting_message,
        "bot_description": bot.bot_description,
        "avatar_url": bot.avatar_url,
        "vk_group_id": bot.vk_group_id,
        "allow_partners": bot.allow_partners,
        "is_active": bot.is_active,
        "created_at": bot.created_at.isoformat() if bot.created_at else None,
        "owner_id": bot.owner.id if bot.owner else None,
        "owner_email": bot.owner.email if bot.owner else None,
        "owner_name": bot.owner.name if bot.owner else None,
        "contacts_count": contacts_count,
        "messages_count": messages_count,
        "broadcasts_count": broadcasts_count,
        "referral_partners": [
            {
                "id": p.id,
                "user_name": p.user.name if p.user else None,
                "user_email": p.user.email if p.user else None,
                "ref_code": p.ref_code,
                "seller_link": p.seller_link,
                "credits": p.credits,
                "is_active": p.is_active,
                "sessions_count": session_counts.get(p.id, 0),
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in partners
        ],
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


# ─── Referrals ───────────────────────────────────────
@router.get("/referrals")
async def admin_list_referrals(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    search: str = Query("", max_length=100),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = select(ReferralPartner).options(
        selectinload(ReferralPartner.user),
        selectinload(ReferralPartner.bot),
    )
    count_query = select(func.count(ReferralPartner.id))

    if search:
        safe = search.replace("%", "\\%").replace("_", "\\_")
        like = f"%{safe}%"
        query = query.join(ReferralPartner.user).filter(
            or_(User.name.ilike(like), User.email.ilike(like), ReferralPartner.ref_code.ilike(like))
        )
        count_query = count_query.join(ReferralPartner.user).filter(
            or_(User.name.ilike(like), User.email.ilike(like), ReferralPartner.ref_code.ilike(like))
        )

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(ReferralPartner.created_at.desc()).limit(limit).offset(offset)
    )
    partners = result.scalars().all()

    partner_ids = [p.id for p in partners]
    session_counts = {}
    active_session_counts = {}
    if partner_ids:
        sc_result = await db.execute(
            select(ReferralSession.partner_id, func.count(ReferralSession.id))
            .where(ReferralSession.partner_id.in_(partner_ids))
            .group_by(ReferralSession.partner_id)
        )
        session_counts = dict(sc_result.all())
        asc_result = await db.execute(
            select(ReferralSession.partner_id, func.count(ReferralSession.id))
            .where(ReferralSession.partner_id.in_(partner_ids), ReferralSession.is_active == True)
            .group_by(ReferralSession.partner_id)
        )
        active_session_counts = dict(asc_result.all())

    return {
        "partners": [
            {
                "id": p.id,
                "user_id": p.user_id,
                "user_name": p.user.name if p.user else None,
                "user_email": p.user.email if p.user else None,
                "bot_id": p.bot_id,
                "bot_username": p.bot.bot_username if p.bot else None,
                "bot_platform": p.bot.platform if p.bot else None,
                "ref_code": p.ref_code,
                "seller_link": p.seller_link,
                "credits": p.credits,
                "is_active": p.is_active,
                "sessions_count": session_counts.get(p.id, 0),
                "active_sessions": active_session_counts.get(p.id, 0),
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in partners
        ],
        "total": total,
    }


@router.get("/cashback")
async def admin_list_cashback(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    total = (await db.execute(select(func.count(CashbackTransaction.id)))).scalar() or 0
    result = await db.execute(
        select(CashbackTransaction)
        .options(
            selectinload(CashbackTransaction.user),
            selectinload(CashbackTransaction.from_user),
        )
        .order_by(CashbackTransaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    txns = result.scalars().all()

    return {
        "transactions": [
            {
                "id": t.id,
                "user_name": t.user.name if t.user else None,
                "user_email": t.user.email if t.user else None,
                "from_user_name": t.from_user.name if t.from_user else None,
                "from_user_email": t.from_user.email if t.from_user else None,
                "amount": float(t.amount),
                "source_amount": float(t.source_amount),
                "level": t.level,
                "source_type": t.source_type,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in txns
        ],
        "total": total,
    }


# ─── Conversations ───────────────────────────────────
@router.get("/conversations")
async def admin_list_conversations(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    search: str = Query("", max_length=100),
    platform: str = Query("", max_length=10),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List all conversations across all users (admin only)."""
    query = select(Contact).where(Contact.message_count > 0)
    count_query = select(func.count(Contact.id)).where(Contact.message_count > 0)

    if platform in ("telegram", "vk"):
        query = query.where(Contact.platform == platform)
        count_query = count_query.where(Contact.platform == platform)

    if search:
        safe = search.replace("%", "\\%").replace("_", "\\_")
        like = f"%{safe}%"
        flt = or_(
            Contact.first_name.ilike(like),
            Contact.last_name.ilike(like),
            Contact.telegram_username.ilike(like),
        )
        query = query.where(flt)
        count_query = count_query.where(flt)

    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(
        query.order_by(Contact.last_message_at.desc())
        .limit(limit)
        .offset(offset)
    )
    contacts = result.scalars().all()

    # Batch fetch last messages
    contact_ids = [c.id for c in contacts]
    last_messages = {}
    if contact_ids:
        last_msg_sq = (
            select(
                Message.contact_id,
                func.max(Message.id).label("last_msg_id"),
            )
            .where(Message.contact_id.in_(contact_ids))
            .group_by(Message.contact_id)
            .subquery()
        )
        msg_result = await db.execute(
            select(Message)
            .join(last_msg_sq, Message.id == last_msg_sq.c.last_msg_id)
        )
        for msg in msg_result.scalars().all():
            last_messages[msg.contact_id] = msg.content[:100] if msg.content else None

    # Batch fetch bot owner info
    bot_ids = list({c.bot_id for c in contacts})
    bot_owners = {}
    if bot_ids:
        bots_result = await db.execute(
            select(Bot).options(selectinload(Bot.owner)).where(Bot.id.in_(bot_ids))
        )
        for b in bots_result.scalars().all():
            bot_owners[b.id] = {
                "bot_username": b.bot_username,
                "owner_name": b.owner.name if b.owner else None,
                "owner_email": b.owner.email if b.owner else None,
            }

    conversations = []
    for c in contacts:
        owner_info = bot_owners.get(c.bot_id, {})
        conversations.append({
            "contact_id": c.id,
            "platform": c.platform,
            "telegram_username": c.telegram_username,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "last_message": last_messages.get(c.id),
            "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
            "message_count": c.message_count,
            "link_sent": c.link_sent,
            "bot_username": owner_info.get("bot_username"),
            "owner_name": owner_info.get("owner_name"),
            "owner_email": owner_info.get("owner_email"),
        })

    return {"conversations": conversations, "total": total}


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
