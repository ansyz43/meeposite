from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import User
from app.schemas import ProfileResponse, ProfileUpdateRequest, ChangePasswordRequest
from app.auth import get_current_user, hash_password, verify_password
from app.config import settings

router = APIRouter(prefix="/api/profile", tags=["profile"])


async def _load_user_with_bot(user: User, db: AsyncSession) -> User:
    result = await db.execute(
        select(User).options(selectinload(User.bots)).where(User.id == user.id)
    )
    return result.scalar_one()


@router.get("", response_model=ProfileResponse)
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await _load_user_with_bot(user, db)

    # Count direct referrals
    result = await db.execute(
        select(func.count(User.id)).where(User.referred_by_id == user.id)
    )
    referrals_count = result.scalar() or 0

    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")] if settings.CORS_ORIGINS else ["http://localhost"]
    base_url = next((o for o in origins if ':3000' not in o and ':5173' not in o), origins[0])
    ref_link = f"{base_url}/register?ref={user.ref_code}" if user.ref_code else None

    return ProfileResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
        has_bot=len(user.bots) > 0,
        ref_code=user.ref_code,
        ref_link=ref_link,
        cashback_balance=user.cashback_balance or 0.0,
        referrals_count=referrals_count,
    )


@router.put("", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await _load_user_with_bot(user, db)
    user.name = data.name
    await db.commit()
    await db.refresh(user)

    # Count direct referrals
    result = await db.execute(
        select(func.count(User.id)).where(User.referred_by_id == user.id)
    )
    referrals_count = result.scalar() or 0

    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")] if settings.CORS_ORIGINS else ["http://localhost"]
    base_url = next((o for o in origins if ':3000' not in o and ':5173' not in o), origins[0])
    ref_link = f"{base_url}/register?ref={user.ref_code}" if user.ref_code else None

    return ProfileResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
        has_bot=len(user.bots) > 0,
        ref_code=user.ref_code,
        ref_link=ref_link,
        cashback_balance=user.cashback_balance or 0.0,
        referrals_count=referrals_count,
    )


@router.put("/password")
async def change_password(
    data: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.password_hash:
        raise HTTPException(status_code=400, detail="Account uses social login, no password to change")

    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    user.password_hash = hash_password(data.new_password)
    await db.commit()
    return {"message": "Password changed successfully"}
