import secrets
import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, update, text, literal_column
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, Bot, ReferralPartner, ReferralSession, Contact, CashbackTransaction
from app.schemas import (
    BotCatalogItem,
    ReferralPartnerCreate,
    ReferralPartnerUpdate,
    ReferralPartnerResponse,
    ReferralSessionResponse,
    AddCreditsRequest,
    BotPartnerInfo,
    TreeNodeResponse,
    CashbackTransactionResponse,
)
from app.auth import get_current_user

router = APIRouter(prefix="/api/referral", tags=["referral"])


def _generate_ref_code() -> str:
    return secrets.token_urlsafe(6)  # 8 chars, url-safe


def _partner_response(partner: ReferralPartner, bot: Bot) -> ReferralPartnerResponse:
    return ReferralPartnerResponse(
        id=partner.id,
        bot_id=partner.bot_id,
        bot_username=bot.bot_username,
        assistant_name=bot.assistant_name,
        seller_link=partner.seller_link,
        ref_code=partner.ref_code,
        ref_link=f"https://t.me/{bot.bot_username}?start=ref_{partner.ref_code}" if bot.bot_username else "",
        credits=partner.credits,
        is_active=partner.is_active,
        created_at=partner.created_at,
    )


@router.get("/catalog", response_model=list[BotCatalogItem])
async def get_catalog(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List bots that allow partners."""
    result = await db.execute(
        select(Bot).where(Bot.allow_partners == True, Bot.is_active == True, Bot.user_id.isnot(None))
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
async def create_partner(
    data: ReferralPartnerCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Become a partner for a bot."""
    # Check bot exists and allows partners
    bot = await db.get(Bot, data.bot_id)
    if not bot or not bot.allow_partners or not bot.is_active:
        raise HTTPException(status_code=404, detail="Бот не найден или не принимает партнёров")

    # Can't be partner of own bot
    if bot.user_id == user.id:
        raise HTTPException(status_code=400, detail="Нельзя стать партнёром своего бота")

    # Check if already a partner
    existing = await db.execute(
        select(ReferralPartner).where(
            ReferralPartner.user_id == user.id,
            ReferralPartner.bot_id == data.bot_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Вы уже партнёр этого бота")

    # Auto-attach to bot owner's referral tree if not already referred
    if user.referred_by_id is None and bot.user_id is not None:
        user.referred_by_id = bot.user_id

    partner = ReferralPartner(
        user_id=user.id,
        bot_id=data.bot_id,
        seller_link=data.seller_link,
        ref_code=_generate_ref_code(),
        credits=5,
    )
    db.add(partner)
    await db.commit()
    await db.refresh(partner)
    return _partner_response(partner, bot)


@router.get("/partner", response_model=ReferralPartnerResponse | None)
async def get_partner(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's partner data."""
    result = await db.execute(
        select(ReferralPartner, Bot)
        .join(Bot, ReferralPartner.bot_id == Bot.id)
        .where(ReferralPartner.user_id == user.id)
        .limit(1)
    )
    row = result.first()
    if not row:
        return None
    partner, bot = row
    return _partner_response(partner, bot)


@router.put("/partner", response_model=ReferralPartnerResponse)
async def update_partner(
    data: ReferralPartnerUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update partner's seller link."""
    result = await db.execute(
        select(ReferralPartner, Bot)
        .join(Bot, ReferralPartner.bot_id == Bot.id)
        .where(ReferralPartner.user_id == user.id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Партнёрство не найдено")
    partner, bot = row
    partner.seller_link = data.seller_link
    await db.commit()
    await db.refresh(partner)
    return _partner_response(partner, bot)


@router.get("/sessions", response_model=list[ReferralSessionResponse])
async def get_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get partner's referral sessions."""
    result = await db.execute(
        select(ReferralPartner).where(ReferralPartner.user_id == user.id)
    )
    partner = result.scalar_one_or_none()
    if not partner:
        return []

    result = await db.execute(
        select(ReferralSession, Contact)
        .join(Contact, ReferralSession.contact_id == Contact.id)
        .where(ReferralSession.partner_id == partner.id)
        .order_by(ReferralSession.started_at.desc())
        .limit(50)
    )
    rows = result.all()

    now = datetime.datetime.now(datetime.UTC)
    return [
        ReferralSessionResponse(
            id=session.id,
            telegram_id=session.telegram_id,
            telegram_username=contact.telegram_username,
            first_name=contact.first_name,
            started_at=session.started_at,
            expires_at=session.expires_at,
            is_active=session.is_active and session.expires_at > now,
        )
        for session, contact in rows
    ]


@router.post("/credits", response_model=ReferralPartnerResponse)
async def add_credits(
    data: AddCreditsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin: add credits to a partner. For now, only bot owner can add credits."""
    partner = await db.get(ReferralPartner, data.partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Партнёр не найден")

    # Only the bot owner can add credits
    bot = await db.get(Bot, partner.bot_id)
    if not bot or bot.user_id != user.id:
        raise HTTPException(status_code=403, detail="Только владелец бота может начислять кредиты")

    # Atomic credit update
    await db.execute(
        update(ReferralPartner)
        .where(ReferralPartner.id == partner.id)
        .values(credits=ReferralPartner.credits + data.credits)
    )
    # Trigger cashback for the partner who bought credits
    await process_cashback(db, partner.user_id, float(data.credits), "credits")
    await db.commit()
    await db.refresh(partner)

    return _partner_response(partner, bot)


@router.get("/my-partners", response_model=list[BotPartnerInfo])
async def get_my_bot_partners(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bot owner: list all partners of my bot."""
    # Find user's bot
    result = await db.execute(
        select(Bot).where(Bot.user_id == user.id)
    )
    bot = result.scalar_one_or_none()
    if not bot:
        return []

    # Get all partners with session counts in one query using subqueries
    now = datetime.datetime.now(datetime.UTC)
    total_sessions_sq = (
        select(func.count(ReferralSession.id))
        .where(ReferralSession.partner_id == ReferralPartner.id)
        .correlate(ReferralPartner)
        .scalar_subquery()
    )
    active_sessions_sq = (
        select(func.count(ReferralSession.id))
        .where(
            ReferralSession.partner_id == ReferralPartner.id,
            ReferralSession.is_active == True,
            ReferralSession.expires_at > now,
        )
        .correlate(ReferralPartner)
        .scalar_subquery()
    )

    result = await db.execute(
        select(ReferralPartner, User, total_sessions_sq.label("total_sessions"), active_sessions_sq.label("active_sessions"))
        .join(User, ReferralPartner.user_id == User.id)
        .where(ReferralPartner.bot_id == bot.id)
        .order_by(ReferralPartner.created_at.desc())
    )
    rows = result.all()

    partners_info = []
    for partner, partner_user, total_sessions, active_sessions in rows:
        partners_info.append(BotPartnerInfo(
            id=partner.id,
            user_name=partner_user.name,
            user_email=partner_user.email,
            seller_link=partner.seller_link,
            ref_code=partner.ref_code,
            credits=partner.credits,
            total_sessions=total_sessions or 0,
            active_sessions=active_sessions or 0,
            created_at=partner.created_at,
        ))

    return partners_info


# --- Cashback engine ---

CASHBACK_RATES = {1: 0.10, 2: 0.05, 3: 0.03, 4: 0.02}  # level 5+ = 0.01
DEFAULT_RATE = 0.01


async def process_cashback(
    db: AsyncSession,
    spender_user_id: int,
    amount: float,
    source_type: str,
):
    """Walk up the referral chain and credit cashback at each level."""
    current_result = await db.execute(select(User).where(User.id == spender_user_id))
    current_user = current_result.scalar_one_or_none()
    if not current_user or not current_user.referred_by_id:
        return

    level = 1
    visited = {spender_user_id}
    referrer_id = current_user.referred_by_id

    while referrer_id and referrer_id not in visited:
        visited.add(referrer_id)
        referrer_result = await db.execute(select(User).where(User.id == referrer_id))
        referrer = referrer_result.scalar_one_or_none()
        if not referrer:
            break

        rate = CASHBACK_RATES.get(level, DEFAULT_RATE)
        cashback_amount = round(amount * rate, 2)
        if cashback_amount <= 0:
            break

        # Atomic balance update to avoid race conditions
        await db.execute(
            update(User)
            .where(User.id == referrer.id)
            .values(cashback_balance=User.cashback_balance + cashback_amount)
        )
        tx = CashbackTransaction(
            user_id=referrer.id,
            from_user_id=spender_user_id,
            amount=cashback_amount,
            source_amount=amount,
            level=level,
            source_type=source_type,
        )
        db.add(tx)

        referrer_id = referrer.referred_by_id
        level += 1

    await db.flush()


# --- Referral tree ---

@router.get("/my-tree", response_model=list[TreeNodeResponse])
async def get_my_tree(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the referral tree for current user using a single CTE query."""
    # 1. Fetch all descendants in one recursive CTE query
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
    result = await db.execute(select(cte))
    all_nodes = result.all()

    if not all_nodes:
        return []

    # 2. Fetch aggregated cashback data in one query
    node_ids = [n.id for n in all_nodes]
    spent_result = await db.execute(
        select(
            CashbackTransaction.from_user_id,
            func.coalesce(func.sum(CashbackTransaction.source_amount), 0.0),
        )
        .where(CashbackTransaction.from_user_id.in_(node_ids))
        .group_by(CashbackTransaction.from_user_id)
    )
    spent_map = {row[0]: float(row[1]) for row in spent_result.all()}

    earned_result = await db.execute(
        select(
            CashbackTransaction.from_user_id,
            func.coalesce(func.sum(CashbackTransaction.amount), 0.0),
        )
        .where(
            CashbackTransaction.user_id == user.id,
            CashbackTransaction.from_user_id.in_(node_ids),
        )
        .group_by(CashbackTransaction.from_user_id)
    )
    earned_map = {row[0]: float(row[1]) for row in earned_result.all()}

    # 3. Build tree structure in memory
    nodes_by_id = {}
    children_map: dict[int, list] = {}
    for n in all_nodes:
        nodes_by_id[n.id] = n
        parent = n.referred_by_id
        children_map.setdefault(parent, []).append(n)

    def build_tree(parent_id: int, level: int) -> list[TreeNodeResponse]:
        children = children_map.get(parent_id, [])
        return [
            TreeNodeResponse(
                id=c.id,
                name=c.name,
                email=c.email,
                level=level,
                total_spent=spent_map.get(c.id, 0.0),
                cashback_earned=earned_map.get(c.id, 0.0),
                joined_at=c.created_at,
                children=build_tree(c.id, level + 1),
            )
            for c in children
        ]

    return build_tree(user.id, 1)


@router.get("/my-cashback", response_model=list[CashbackTransactionResponse])
async def get_my_cashback(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get cashback transaction history."""
    result = await db.execute(
        select(CashbackTransaction, User)
        .join(User, CashbackTransaction.from_user_id == User.id)
        .where(CashbackTransaction.user_id == user.id)
        .order_by(CashbackTransaction.created_at.desc())
        .limit(100)
    )
    rows = result.all()
    return [
        CashbackTransactionResponse(
            id=tx.id,
            from_user_name=from_user.name,
            amount=tx.amount,
            source_amount=tx.source_amount,
            level=tx.level,
            source_type=tx.source_type,
            created_at=tx.created_at,
        )
        for tx, from_user in rows
    ]
