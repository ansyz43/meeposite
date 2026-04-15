import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, literal_column, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import User, Bot, ReferralPartner, ReferralSession
from app.schemas import (
    SimpleReferralResponse, TreeNodeResponse,
    BotCatalogItem, ReferralPartnerCreate, ReferralPartnerUpdate,
    ReferralPartnerResponse, AddCreditsRequest, BotPartnerInfo,
    ReferralSessionResponse,
)
from app.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/referral", tags=["referral"])


def _mask_email(email: str) -> str:
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    return f"{local[0]}***@{domain}" if local else f"***@{domain}"


def _generate_partner_ref_code() -> str:
    return secrets.token_urlsafe(6)


# ── Catalog & Partner CRUD ───────────────────────────────────


@router.get("/catalog", response_model=list[BotCatalogItem])
async def get_catalog(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bot).where(
            Bot.allow_partners == True,
            Bot.is_active == True,
            Bot.user_id.isnot(None),
            Bot.user_id != user.id,
        )
    )
    bots = result.scalars().all()
    return [
        BotCatalogItem(
            id=b.id,
            bot_username=b.bot_username,
            assistant_name=b.assistant_name,
            avatar_url=b.avatar_url,
        )
        for b in bots
    ]


@router.post("/partner", response_model=ReferralPartnerResponse, status_code=201)
async def become_partner(
    data: ReferralPartnerCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Bot).where(Bot.id == data.bot_id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")
    if not bot.allow_partners:
        raise HTTPException(status_code=400, detail="Бот не принимает партнёров")
    if bot.user_id == user.id:
        raise HTTPException(status_code=400, detail="Нельзя стать партнёром своего бота")

    existing = await db.execute(
        select(ReferralPartner).where(
            ReferralPartner.user_id == user.id,
            ReferralPartner.bot_id == data.bot_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Вы уже партнёр этого бота")

    # Generate unique ref_code with collision retry
    ref_code = None
    for _ in range(5):
        candidate = _generate_partner_ref_code()
        dup = await db.execute(select(ReferralPartner.id).where(ReferralPartner.ref_code == candidate))
        if not dup.scalar_one_or_none():
            ref_code = candidate
            break
    if not ref_code:
        raise HTTPException(status_code=500, detail="Не удалось сгенерировать уникальный код")

    partner = ReferralPartner(
        user_id=user.id,
        bot_id=data.bot_id,
        seller_link=data.seller_link,
        ref_code=ref_code,
    )
    db.add(partner)
    await db.commit()
    await db.refresh(partner)
    return _partner_response(partner, bot)


@router.get("/partner", response_model=list[ReferralPartnerResponse])
async def get_my_partnerships(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReferralPartner, Bot)
        .join(Bot, ReferralPartner.bot_id == Bot.id)
        .where(ReferralPartner.user_id == user.id)
        .order_by(ReferralPartner.created_at.desc())
    )
    rows = result.all()
    return [_partner_response(p, b) for p, b in rows]


@router.put("/partner/{partner_id}", response_model=ReferralPartnerResponse)
async def update_partnership(
    partner_id: int,
    data: ReferralPartnerUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReferralPartner, Bot)
        .join(Bot, ReferralPartner.bot_id == Bot.id)
        .where(ReferralPartner.id == partner_id, ReferralPartner.user_id == user.id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Партнёрство не найдено")
    partner, bot = row
    partner.seller_link = data.seller_link
    await db.commit()
    await db.refresh(partner)
    return _partner_response(partner, bot)


# ── Bot owner: manage partners ──────────────────────────────


@router.get("/my-partners", response_model=list[BotPartnerInfo])
async def get_my_bot_partners(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Bot.id).where(Bot.user_id == user.id))
    bot_ids = [r[0] for r in result.all()]
    if not bot_ids:
        return []

    total_sub = (
        select(func.count(ReferralSession.id))
        .where(ReferralSession.partner_id == ReferralPartner.id)
        .correlate(ReferralPartner)
        .scalar_subquery()
    )
    active_sub = (
        select(func.count(ReferralSession.id))
        .where(
            ReferralSession.partner_id == ReferralPartner.id,
            ReferralSession.is_active == True,
        )
        .correlate(ReferralPartner)
        .scalar_subquery()
    )
    result = await db.execute(
        select(ReferralPartner, User, total_sub.label("total_sessions"), active_sub.label("active_sessions"))
        .join(User, ReferralPartner.user_id == User.id)
        .where(ReferralPartner.bot_id.in_(bot_ids))
        .order_by(ReferralPartner.created_at.desc())
    )
    rows = result.all()
    return [
        BotPartnerInfo(
            id=p.id,
            user_name=u.name,
            user_email=u.email,
            seller_link=p.seller_link,
            ref_code=p.ref_code,
            credits=p.credits,
            total_sessions=ts or 0,
            active_sessions=acs or 0,
            created_at=p.created_at,
        )
        for p, u, ts, acs in rows
    ]


@router.post("/credits", response_model=BotPartnerInfo)
async def add_credits(
    data: AddCreditsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReferralPartner, Bot, User)
        .join(Bot, ReferralPartner.bot_id == Bot.id)
        .join(User, ReferralPartner.user_id == User.id)
        .where(ReferralPartner.id == data.partner_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Партнёр не найден")
    partner, bot, partner_user = row
    if bot.user_id != user.id:
        raise HTTPException(status_code=403, detail="Это не ваш бот")

    partner.credits += data.credits
    await db.commit()
    await db.refresh(partner)

    total = await db.scalar(
        select(func.count(ReferralSession.id)).where(ReferralSession.partner_id == partner.id)
    )
    active = await db.scalar(
        select(func.count(ReferralSession.id)).where(
            ReferralSession.partner_id == partner.id, ReferralSession.is_active == True,
        )
    )
    return BotPartnerInfo(
        id=partner.id,
        user_name=partner_user.name,
        user_email=partner_user.email,
        seller_link=partner.seller_link,
        ref_code=partner.ref_code,
        credits=partner.credits,
        total_sessions=total or 0,
        active_sessions=active or 0,
        created_at=partner.created_at,
    )


# ── Partner sessions ─────────────────────────────────────────


@router.get("/sessions", response_model=list[ReferralSessionResponse])
async def get_my_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models import Contact
    result = await db.execute(
        select(ReferralSession, Contact)
        .join(ReferralPartner, ReferralSession.partner_id == ReferralPartner.id)
        .join(Contact, ReferralSession.contact_id == Contact.id)
        .where(ReferralPartner.user_id == user.id)
        .order_by(ReferralSession.started_at.desc())
        .limit(200)
    )
    rows = result.all()
    return [
        ReferralSessionResponse(
            id=s.id,
            telegram_id=s.telegram_id,
            telegram_username=c.telegram_username,
            first_name=c.first_name,
            started_at=s.started_at,
            expires_at=s.expires_at,
            is_active=s.is_active,
        )
        for s, c in rows
    ]


# ── Helper ───────────────────────────────────────────────────


def _partner_response(partner: ReferralPartner, bot: Bot) -> ReferralPartnerResponse:
    ref_link = f"https://t.me/{bot.bot_username}?start=p_{partner.ref_code}" if bot.bot_username else ""
    return ReferralPartnerResponse(
        id=partner.id,
        bot_id=partner.bot_id,
        bot_username=bot.bot_username,
        assistant_name=bot.assistant_name,
        seller_link=partner.seller_link,
        ref_code=partner.ref_code,
        ref_link=ref_link,
        credits=partner.credits,
        is_active=partner.is_active,
        created_at=partner.created_at,
    )


# ── User Referrals (existing) ───────────────────────────────


@router.get("/my-referrals", response_model=list[SimpleReferralResponse])
async def get_my_referrals(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User)
        .where(User.referred_by_id == user.id)
        .order_by(User.created_at.desc())
    )
    referrals = result.scalars().all()
    return [
        SimpleReferralResponse(
            id=u.id,
            name=u.name,
            email=_mask_email(u.email),
            created_at=u.created_at,
        )
        for u in referrals
    ]


@router.get("/my-tree", response_model=list[TreeNodeResponse])
async def get_my_tree(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cte = (
        select(
            User.id,
            User.name,
            User.email,
            User.referred_by_id,
            User.created_at,
            literal_column("1").label("level"),
        )
        .where(User.referred_by_id == user.id)
        .cte(name="tree", recursive=True)
    )
    cte = cte.union_all(
        select(
            User.id,
            User.name,
            User.email,
            User.referred_by_id,
            User.created_at,
            (cte.c.level + 1).label("level"),
        )
        .join(cte, User.referred_by_id == cte.c.id)
        .where(cte.c.level < 10)
    )
    result = await db.execute(select(cte).limit(1000))
    all_nodes = result.all()

    if not all_nodes:
        return []

    children_map: dict[int, list] = {}
    for n in all_nodes:
        parent = n.referred_by_id
        children_map.setdefault(parent, []).append(n)

    def build_tree(parent_id: int, level: int) -> list[TreeNodeResponse]:
        children = children_map.get(parent_id, [])
        return [
            TreeNodeResponse(
                id=c.id,
                name=c.name,
                email=_mask_email(c.email),
                level=level,
                joined_at=c.created_at,
                children=build_tree(c.id, level + 1),
            )
            for c in children
        ]

    return build_tree(user.id, 1)
