"""
Keep only top-5 FitLine accounts and deep-parse them (up to 100 posts each).
Deletes posts from all other accounts.

Usage:
  docker compose exec -T backend python scripts/seed_top5_deep.py
"""
import asyncio
import sys
import logging

sys.path.insert(0, "/app")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TOP5 = [
    ("babich_nutrition", "Ольга Бабич — нутрициолог, FitLine"),
    ("chernienko_nataliya", "Наталья Черниенко — ТОП лидер PM International"),
    ("the_varlam", "VARLAM GRIGORYAN — TOP лидер FitLine PM"),
    ("rinchinova.alena", "Алёна Ринчинова — PM FitLine"),
    ("eshe_dolkar", "Инна — FitLine, Алтан Бургэд, Иркутск"),
]

TOP5_USERNAMES = {u for u, _ in TOP5}


async def main():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession as AS
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select, delete, func
    from app.config import settings
    from app.models import CompetitorPost
    from app.services.parser_instagram import _fetch_medias_sync

    engine = create_async_engine(settings.DATABASE_URL)
    Session = sessionmaker(engine, class_=AS, expire_on_commit=False)

    # ── Step 1: Delete posts from non-top-5 accounts ──
    logger.info("Step 1: Deleting posts from non-top-5 accounts...")
    async with Session() as db:
        # Get all distinct usernames
        all_users = (await db.execute(
            select(CompetitorPost.channel_username).distinct()
        )).scalars().all()

        to_delete = [u for u in all_users if u not in TOP5_USERNAMES]
        if to_delete:
            result = await db.execute(
                delete(CompetitorPost).where(
                    CompetitorPost.channel_username.in_(to_delete)
                )
            )
            await db.commit()
            logger.info(f"  Deleted {result.rowcount} posts from {len(to_delete)} accounts: {', '.join(to_delete)}")
        else:
            logger.info("  Nothing to delete")

    # ── Step 2: Deep-parse top-5 (100 posts each) ──
    logger.info("Step 2: Deep-parsing top-5 accounts (100 posts each)...")
    loop = asyncio.get_event_loop()
    total_new = 0

    for i, (username, desc) in enumerate(TOP5, 1):
        logger.info(f"[{i}/5] Parsing @{username} — {desc}")

        result = None
        for attempt in range(2):
            try:
                result = await loop.run_in_executor(
                    None, _fetch_medias_sync, username, 100
                )
                break
            except Exception as e:
                logger.error(f"  EXECUTOR ERROR (attempt {attempt+1}): {e}")
                if attempt == 0:
                    await asyncio.sleep(15)

        if result is None:
            logger.error(f"  SKIPPED @{username} — no result")
            continue

        if isinstance(result, dict) and "error" in result:
            logger.error(f"  ERROR: {result['error']}")
            continue

        posts = result
        if not posts:
            logger.warning(f"  No posts found for @{username}")
            continue

        # Save new posts (dedup by text)
        async with Session() as db:
            saved = 0
            for post in posts:
                existing = await db.execute(
                    select(CompetitorPost.id).where(
                        CompetitorPost.platform == "instagram",
                        CompetitorPost.channel_username == username,
                        CompetitorPost.text == post["text"],
                    ).limit(1)
                )
                if existing.scalar_one_or_none():
                    continue

                db.add(CompetitorPost(
                    platform="instagram",
                    channel_username=username,
                    text=post["text"],
                    views=post.get("views"),
                    reactions=post.get("reactions"),
                    posted_at=post.get("posted_at"),
                ))
                saved += 1

            await db.commit()
            total_new += saved

            # Count total for this user
            total_user = (await db.execute(
                select(func.count(CompetitorPost.id)).where(
                    CompetitorPost.channel_username == username
                )
            )).scalar()
            logger.info(f"  +{saved} new posts (total for @{username}: {total_user})")

        # Delay between accounts
        delay = 20 if i < 5 else 0
        if delay:
            logger.info(f"  Waiting {delay}s...")
            await asyncio.sleep(delay)

    # ── Summary ──
    async with Session() as db:
        total = (await db.execute(
            select(func.count(CompetitorPost.id))
        )).scalar()
        per_user = (await db.execute(
            select(
                CompetitorPost.channel_username,
                func.count(CompetitorPost.id).label("cnt"),
                func.avg(CompetitorPost.reactions).label("avg_r"),
            ).group_by(CompetitorPost.channel_username)
            .order_by(func.avg(CompetitorPost.reactions).desc())
        )).all()

    logger.info(f"\n{'='*50}")
    logger.info(f"DONE! Added {total_new} new posts. Total in DB: {total}")
    for u, cnt, avg_r in per_user:
        logger.info(f"  @{u}: {cnt} posts (avg reactions: {avg_r:.0f})")
    logger.info(f"{'='*50}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
