"""
Cashback service — ready for acquiring integration.

When payment processing is connected, call `process_cashback()` to distribute
cashback up the referral chain. Rates are configured via environment variables.

Usage (call from payment webhook handler):
    from app.services.cashback import process_cashback
    await process_cashback(db, paying_user_id=user.id, payment_amount=1000.0, source_type="subscription")
"""
import logging
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, CashbackTransaction

logger = logging.getLogger(__name__)

# Cashback rates per referral level (1 = direct referrer, 2 = referrer's referrer, etc.)
# Format: {level: percentage} — percentage of the payment amount
# These will be configurable via env vars or admin panel later.
# For now, set defaults that can be overridden.
CASHBACK_RATES: dict[int, Decimal] = {
    1: Decimal("0.10"),   # 10% to direct referrer
    2: Decimal("0.05"),   # 5% to level 2
    3: Decimal("0.03"),   # 3% to level 3
}

# Maximum referral depth for cashback distribution
MAX_CASHBACK_DEPTH = 3


def configure_rates(rates: dict[int, float], max_depth: int | None = None):
    """
    Configure cashback rates programmatically.
    Call this at startup or from admin panel.

    Args:
        rates: {level: percentage} e.g. {1: 0.10, 2: 0.05}
        max_depth: max referral levels to distribute cashback
    """
    global MAX_CASHBACK_DEPTH
    CASHBACK_RATES.clear()
    for level, pct in rates.items():
        CASHBACK_RATES[int(level)] = Decimal(str(pct))
    if max_depth is not None:
        MAX_CASHBACK_DEPTH = max_depth


async def process_cashback(
    db: AsyncSession,
    paying_user_id: int,
    payment_amount: float,
    source_type: str = "subscription",
) -> list[CashbackTransaction]:
    """
    Distribute cashback up the referral chain when a payment is made.

    Args:
        db: async database session
        paying_user_id: the user who made the payment
        payment_amount: the payment amount in currency units
        source_type: type of payment ('subscription', 'credits', etc.)

    Returns:
        list of created CashbackTransaction records
    """
    if payment_amount <= 0:
        return []

    amount = Decimal(str(payment_amount))
    transactions: list[CashbackTransaction] = []

    # Walk up the referral chain
    current_user_id = paying_user_id
    for level in range(1, MAX_CASHBACK_DEPTH + 1):
        # Find referrer
        result = await db.execute(
            select(User.id, User.referred_by_id)
            .where(User.id == current_user_id)
        )
        row = result.one_or_none()
        if not row or not row.referred_by_id:
            break

        referrer_id = row.referred_by_id
        rate = CASHBACK_RATES.get(level)
        if not rate or rate <= 0:
            current_user_id = referrer_id
            continue

        cashback_amount = (amount * rate).quantize(Decimal("0.01"))
        if cashback_amount <= 0:
            current_user_id = referrer_id
            continue

        # Create transaction
        txn = CashbackTransaction(
            user_id=referrer_id,
            from_user_id=paying_user_id,
            amount=float(cashback_amount),
            source_amount=float(amount),
            level=level,
            source_type=source_type,
        )
        db.add(txn)

        # Update referrer's balance
        await db.execute(
            update(User)
            .where(User.id == referrer_id)
            .values(cashback_balance=User.cashback_balance + float(cashback_amount))
        )

        transactions.append(txn)
        logger.info(
            f"Cashback: {cashback_amount} to user#{referrer_id} "
            f"(level {level}, {rate*100}% of {amount}) from user#{paying_user_id}"
        )

        # Move up to next level
        current_user_id = referrer_id

    if transactions:
        await db.flush()

    return transactions
