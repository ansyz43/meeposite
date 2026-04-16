"""Seed 30 top FitLine seller accounts from Russia/CIS into competitor_posts.

Usage:
  docker compose exec -T backend python scripts/seed_fitline_competitors.py

Parses each account's last 15 posts via the existing Instagram parser.
Uses delays to avoid 429 rate limits.
"""
import asyncio
import sys
import time
import logging

sys.path.insert(0, "/app")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Top 30 Russian-speaking FitLine sellers (curated from IG search) ──
FITLINE_ACCOUNTS = [
    # username | description
    ("the_varlam", "VARLAM GRIGORYAN — TOP лидер FitLine PM"),
    ("chernienko_nataliya", "Наталья Черниенко — ТОП лидер PM International"),
    ("daria_grigorenko", "Дарья Григоренко — меняю жизни, FitLine"),
    ("maria_sport_pp", "Мария Ратманская — FitLine, спорт, МЛМ"),
    ("juliasandal_", "Юлия Сандал — МЛМ ТОП лидер PM International"),
    ("svetlanavladimirovapm", "Светлана Владимирова — Президент PM FitLine"),
    ("xristianka.style", "Ксения Поздняк — PM FitLine, здоровье, красота"),
    ("diana.alaikova", "Диана Алайкова — FitLine PM"),
    ("stepkin005", "Владимир Стёпкин — FitLine PM"),
    ("aivanovapp", "Алина Дерябина — FitLine PM"),
    ("dana_sagat", "Дана Нурмахатова — PM FitLine"),
    ("innashakti", "Изобильная Инна — PM FitLine"),
    ("osodoev", "Сергей — энергия, продуктивность, Фитлайн"),
    ("lena_tsyrenova", "Елена Цыренова — лидер PM Фитлайн"),
    ("rinchinova.alena", "Алёна Ринчинова — PM FitLine"),
    ("nastya_fitline", "Анастасия — Фитлайн, здоровье, спорт"),
    ("babich_nutrition", "Ольга Бабич — нутрициолог, FitLine"),
    ("marina__melkonian", "Марина Мелконян — FitLine PM, декрет с бизнесом"),
    ("ekaterina_doncova_", "Екатерина Донцова — FitLine PM International"),
    ("eco_irina", "Ирина Суховеева — Фитлайн"),
    ("tamara_valery_", "Тамара Васильева — Фитлайн, путешествия"),
    ("ekaterina_novikowa_", "Лидер PM International, Фитлайн, наставник"),
    ("gubin.sergej", "Сергей Губин — Фитлайн PM FitLine"),
    ("fitline_premteam", "Наталия — Фитлайн"),
    ("pm_international_russia", "Витамины FitLine в России — Official"),
    ("fitline.russia", "FitLine Russia"),
    ("ayuna_chimitova23", "Аюна Чимитова — Фитлайн"),
    ("nadenka181276", "Надежда Белоусова — лидер PM International"),
    ("valeriia.maltsevaa", "Мастер спорта: биохакинг, энергия, FitLine"),
    ("eshe_dolkar", "Инна — FitLine, Алтан Бургэд, Иркутск"),
]


async def main():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession as AS
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select, text
    from app.config import settings
    from app.models import CompetitorPost, CompetitorSource

    engine = create_async_engine(settings.DATABASE_URL)
    Session = sessionmaker(engine, class_=AS, expire_on_commit=False)

    # Import parser internals
    from app.services.parser_instagram import (
        _extract_username,
        _fetch_medias_sync,
    )

    total_posts = 0
    errors = []

    for i, (username, desc) in enumerate(FITLINE_ACCOUNTS, 1):
        logger.info(f"[{i}/{len(FITLINE_ACCOUNTS)}] Parsing @{username} — {desc}")

        # Run sync fetch in executor (same as the parser does)
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None, _fetch_medias_sync, username, 15
            )
        except Exception as e:
            logger.error(f"  EXECUTOR ERROR: {e}")
            errors.append(username)
            await asyncio.sleep(10)
            continue

        if isinstance(result, dict) and "error" in result:
            logger.error(f"  ERROR: {result['error']}")
            errors.append(username)
            await asyncio.sleep(5)
            continue

        posts = result
        if not posts:
            logger.warning(f"  No posts found for @{username}")
            await asyncio.sleep(3)
            continue

        # Save posts to DB
        async with Session() as db:
            saved = 0
            for post in posts:
                # Check if already exists (by text hash)
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
            total_posts += saved
            logger.info(f"  Saved {saved} new posts (total so far: {total_posts})")

        # Delay between accounts to avoid rate limits
        delay = 8 if i % 5 == 0 else 4
        logger.info(f"  Waiting {delay}s...")
        await asyncio.sleep(delay)

    # Summary
    logger.info(f"\n{'='*50}")
    logger.info(f"DONE! Total new posts saved: {total_posts}")
    logger.info(f"Successful: {len(FITLINE_ACCOUNTS) - len(errors)}/{len(FITLINE_ACCOUNTS)}")
    if errors:
        logger.info(f"Failed accounts: {', '.join(errors)}")
    logger.info(f"{'='*50}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
