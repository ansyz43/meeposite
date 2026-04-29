"""Shared helpers for checking active Meepo Pro subscription."""
from __future__ import annotations

import datetime
import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Payment, User
from app.services import tochka

logger = logging.getLogger(__name__)

SUBSCRIPTION_DAYS = 31


def _map_status(status_raw: str) -> Optional[str]:
    s = (status_raw or "").upper()
    if s in ("APPROVED", "CONFIRMED", "PAID", "SUCCESS"):
        return "paid"
    if s in ("REJECTED", "FAILED", "DECLINED"):
        return "failed"
    if s in ("CANCELED", "CANCELLED", "REFUNDED", "EXPIRED"):
        return "cancelled"
    if s in ("CREATED", "PENDING", "PROCESSING", "WAITING"):
        return "pending"
    return None


async def _refresh_pending(payment: Payment, db: AsyncSession) -> Payment:
    if payment.status != "pending" or not payment.operation_id:
        return payment
    try:
        raw = await tochka.get_payment_operation(payment.operation_id)
    except tochka.TochkaError as e:
        logger.warning("Tochka poll failed for op=%s: %s", payment.operation_id, e)
        return payment
    data = raw.get("Data", raw) if isinstance(raw, dict) else {}
    op = None
    if isinstance(data, dict):
        ops = data.get("Operation")
        if isinstance(ops, list) and ops:
            op = ops[0]
        else:
            op = data
    status_str = (op or {}).get("status", "") if isinstance(op, dict) else ""
    new_status = _map_status(status_str)
    if new_status and new_status != payment.status:
        payment.status = new_status
        if new_status == "paid":
            payment.paid_at = datetime.datetime.utcnow()
        await db.commit()
        await db.refresh(payment)
    return payment


async def has_active_subscription(user: User, db: AsyncSession) -> bool:
    """Returns True if user has an active Meepo Pro subscription.

    Polls Tochka for any pending payments to keep DB fresh.
    """
    result = await db.execute(
        select(Payment)
        .where(Payment.user_id == user.id, Payment.purpose == "subscription")
        .order_by(Payment.created_at.desc())
        .limit(10)
    )
    payments = list(result.scalars().all())
    # Refresh pending so freshly-paid users gain access without manual reload
    for p in payments:
        if p.status == "pending":
            await _refresh_pending(p, db)
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=SUBSCRIPTION_DAYS)
    return any(
        p.status == "paid" and p.paid_at and p.paid_at >= cutoff for p in payments
    )


async def require_active_subscription(user: User, db: AsyncSession) -> None:
    """Raise 402 if user has no active subscription. Free pass when Tochka not configured (dev)."""
    if not settings.TOCHKA_JWT or not settings.TOCHKA_CUSTOMER_CODE:
        # Payments not configured — don't block; keeps local dev usable.
        return
    if not await has_active_subscription(user, db):
        raise HTTPException(
            status_code=402,
            detail="Для подключения бота нужна активная подписка Meepo Pro",
        )
