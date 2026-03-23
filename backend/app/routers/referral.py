from fastapi import APIRouter, Depends
from sqlalchemy import select, func, literal_column
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import SimpleReferralResponse, TreeNodeResponse
from app.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/referral", tags=["referral"])


@router.get("/my-referrals", response_model=list[SimpleReferralResponse])
async def get_my_referrals(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of users who registered via current user's referral link."""
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
            email=u.email,
            created_at=u.created_at,
        )
        for u in referrals
    ]


@router.get("/my-tree", response_model=list[TreeNodeResponse])
async def get_my_tree(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the referral tree for current user using a single CTE query."""
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

    # Build tree structure in memory
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
                email=c.email,
                level=level,
                joined_at=c.created_at,
                children=build_tree(c.id, level + 1),
            )
            for c in children
        ]

    return build_tree(user.id, 1)
