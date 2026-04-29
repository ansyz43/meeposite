"""Payments router: create Tochka payment link + webhook receiver."""
from __future__ import annotations

import datetime
import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import Payment, User
from app.services import tochka

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["payments"])


class CreateSubscriptionPaymentResponse(BaseModel):
    payment_id: int
    payment_link: str
    operation_id: str
    amount: float


def _generate_order_id() -> str:
    ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"meepo-{ts}-{secrets.token_hex(4)}"


@router.post("/subscription", response_model=CreateSubscriptionPaymentResponse)
async def create_subscription_payment(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a Tochka payment link for the monthly subscription."""
    if not settings.TOCHKA_JWT or not settings.TOCHKA_CUSTOMER_CODE:
        raise HTTPException(status_code=503, detail="Платежный шлюз временно недоступен")

    amount = float(settings.TOCHKA_SUBSCRIPTION_AMOUNT)
    order_id = _generate_order_id()

    payment = Payment(
        user_id=user.id,
        purpose="subscription",
        amount=amount,
        currency="RUB",
        status="created",
        order_id=order_id,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    try:
        result = await tochka.create_payment_operation(
            amount=amount,
            purpose=f"Подписка Meepo Pro (заказ {order_id})",
            order_id=order_id,
            consumer_id=str(user.id),
        )
    except tochka.TochkaError as e:
        logger.error("Failed to create Tochka payment: %s", e)
        payment.status = "failed"
        await db.commit()
        raise HTTPException(status_code=502, detail="Не удалось создать платёж в Точке")

    payment.operation_id = result.get("operation_id")
    payment.payment_link = result.get("payment_link")
    payment.status = "pending"
    payment.raw_response = str(result.get("raw"))[:4000]
    await db.commit()
    await db.refresh(payment)

    if not payment.payment_link or not payment.operation_id:
        raise HTTPException(status_code=502, detail="Точка не вернула ссылку на оплату")

    return CreateSubscriptionPaymentResponse(
        payment_id=payment.id,
        payment_link=payment.payment_link,
        operation_id=payment.operation_id,
        amount=amount,
    )


@router.post("/webhook/tochka/{secret}")
async def tochka_webhook(
    secret: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive payment status updates from Tochka.

    Path-based shared secret (TOCHKA_WEBHOOK_SECRET) is used to authenticate.
    """
    if not settings.TOCHKA_WEBHOOK_SECRET or not secrets.compare_digest(
        secret, settings.TOCHKA_WEBHOOK_SECRET
    ):
        raise HTTPException(status_code=403, detail="forbidden")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid json")

    logger.info("Tochka webhook payload: %s", str(payload)[:1000])

    # Tochka delivers events as {"Data": {"operationId": "...", "status": "APPROVED" | ...}}
    data = payload.get("Data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        data = payload if isinstance(payload, dict) else {}

    operation_id = (
        data.get("operationId")
        or data.get("operation_id")
        or payload.get("operationId")
        if isinstance(payload, dict)
        else None
    )
    status_raw = (data.get("status") or payload.get("status") or "").upper()

    if not operation_id:
        return {"status": "ignored", "reason": "no operationId"}

    result = await db.execute(
        select(Payment).where(Payment.operation_id == operation_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        logger.warning("Tochka webhook: unknown operation_id=%s", operation_id)
        return {"status": "ignored", "reason": "unknown operation"}

    # Idempotency: don't re-process terminal payments.
    if payment.status in ("paid", "failed", "cancelled"):
        return {"status": "ok", "idempotent": True}

    if status_raw in ("APPROVED", "CONFIRMED", "PAID", "SUCCESS"):
        payment.status = "paid"
        payment.paid_at = datetime.datetime.utcnow()
    elif status_raw in ("REJECTED", "FAILED", "DECLINED"):
        payment.status = "failed"
    elif status_raw in ("CANCELED", "CANCELLED", "REFUNDED"):
        payment.status = "cancelled"
    else:
        payment.status = "pending"

    await db.commit()
    return {"status": "ok"}
