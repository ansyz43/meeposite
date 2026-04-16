"""Check competitor_posts in DB."""
import asyncio
import sys
sys.path.insert(0, "/app")

async def main():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    from app.config import settings

    engine = create_async_engine(settings.DATABASE_URL)
    S = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with S() as db:
        r = await db.execute(text(
            "SELECT channel_username, count(*) as c FROM competitor_posts "
            "GROUP BY channel_username ORDER BY c DESC"
        ))
        rows = r.fetchall()
        total = 0
        for row in rows:
            print(f"  {row[0]}: {row[1]} posts")
            total += row[1]
        print(f"\nTotal: {total} posts from {len(rows)} accounts")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
