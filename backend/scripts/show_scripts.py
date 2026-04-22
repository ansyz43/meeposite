import asyncio
from app.database import async_session
from sqlalchemy import text

async def show():
    async with async_session() as db:
        r = await db.execute(text("SELECT post_type, script FROM content_plan_items WHERE plan_id=10 AND script IS NOT NULL LIMIT 2"))
        for row in r.fetchall():
            print(f"=== {row[0]} ===")
            print(row[1])
            print()

asyncio.run(show())
