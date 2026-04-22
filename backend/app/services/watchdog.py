"""Background watchdog — recover stuck content plans.

A plan row is created with status='generating' and filled by a FastAPI
BackgroundTask. If the process is killed (OOM, redeploy) mid-generation,
the row is left in 'generating' forever. This watchdog scans for such rows
and flips them to 'error' so the UI stops polling.
"""
import asyncio
import datetime
import logging

from sqlalchemy import select, update

from app.database import async_session
from app.models import ContentPlan

logger = logging.getLogger(__name__)

_SCAN_INTERVAL = 120  # seconds
_STALE_AFTER = datetime.timedelta(minutes=10)


async def _scan_once() -> int:
    cutoff = datetime.datetime.utcnow() - _STALE_AFTER
    async with async_session() as db:
        result = await db.execute(
            select(ContentPlan.id).where(
                ContentPlan.status == "generating",
                ContentPlan.created_at < cutoff,
            )
        )
        stale_ids = [row[0] for row in result.all()]
        if not stale_ids:
            return 0
        await db.execute(
            update(ContentPlan)
            .where(ContentPlan.id.in_(stale_ids))
            .values(
                status="error",
                error_message="Генерация прервана (таймаут watchdog). Попробуйте ещё раз.",
            )
        )
        await db.commit()
        return len(stale_ids)


async def run_plan_watchdog() -> None:
    logger.info("Plan watchdog started (interval=%ds, stale_after=%s)", _SCAN_INTERVAL, _STALE_AFTER)
    while True:
        try:
            n = await _scan_once()
            if n:
                logger.warning("Plan watchdog: marked %d stale plans as error", n)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("Plan watchdog iteration failed: %s", e, exc_info=True)
        await asyncio.sleep(_SCAN_INTERVAL)
