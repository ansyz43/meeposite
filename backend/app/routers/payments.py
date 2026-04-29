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


def _map_tochka_status(status_raw: str) -> str | None:
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


async def _refresh_payment_from_tochka(payment: Payment, db: AsyncSession) -> Payment:
    """Poll Tochka for current status and update Payment row in place."""
    if payment.status in ("paid", "failed", "cancelled"):
        return payment
    if not payment.operation_id:
        return payment
    try:
        raw = await tochka.get_payment_operation(payment.operation_id)
    except tochka.TochkaError as e:
        logger.warning("Tochka poll failed for op=%s: %s", payment.operation_id, e)
        return payment
    # Tochka returns: {"Data": {"Operation": [{...}]}}
    data = raw.get("Data", raw) if isinstance(raw, dict) else {}
    op = None
    if isinstance(data, dict):
        ops = data.get("Operation")
        if isinstance(ops, list) and ops:
            op = ops[0]
        else:
            op = data
    status_str = (op or {}).get("status", "") if isinstance(op, dict) else ""
    new_status = _map_tochka_status(status_str)
    if new_status and new_status != payment.status:
        payment.status = new_status
        if new_status == "paid":
            payment.paid_at = datetime.datetime.utcnow()
        await db.commit()
        await db.refresh(payment)
    return payment


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
            client_email=user.email,
            item_name="Подписка Meepo Pro · 1 месяц",
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


class PaymentStatusResponse(BaseModel):
    payment_id: int
    operation_id: str | None
    status: str
    amount: float
    paid_at: datetime.datetime | None


@router.get("/status/{operation_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    operation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Polling endpoint: fetch current status of a payment, refreshing it from Tochka if pending."""
    result = await db.execute(
        select(Payment).where(
            Payment.operation_id == operation_id, Payment.user_id == user.id
        )
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Платёж не найден")
    payment = await _refresh_payment_from_tochka(payment, db)
    return PaymentStatusResponse(
        payment_id=payment.id,
        operation_id=payment.operation_id,
        status=payment.status,
        amount=float(payment.amount),
        paid_at=payment.paid_at,
    )


@router.get("/me")
async def my_payments(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's payments. Refreshes any pending ones via Tochka polling."""
    result = await db.execute(
        select(Payment).where(Payment.user_id == user.id).order_by(Payment.created_at.desc()).limit(20)
    )
    payments = result.scalars().all()
    # Refresh pending payments in background-ish manner (sequentially, but bounded by limit=20)
    for p in payments:
        if p.status == "pending":
            await _refresh_payment_from_tochka(p, db)
    has_active_subscription = any(
        p.status == "paid" and p.purpose == "subscription"
        and p.paid_at and (datetime.datetime.utcnow() - p.paid_at).days < 31
        for p in payments
    )
    return {
        "has_active_subscription": has_active_subscription,
        "payments": [
            {
                "id": p.id,
                "operation_id": p.operation_id,
                "status": p.status,
                "amount": float(p.amount),
                "purpose": p.purpose,
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in payments
        ],
    }


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