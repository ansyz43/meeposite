import asyncio
from app.database import async_session
from sqlalchemy import text


async def main() -> None:
    async with async_session() as db:
        q = text(
            """
            SELECT id, user_id, platform, status, created_at,
                   left(coalesce(error_message, ''), 200) AS err
            FROM content_plans
            ORDER BY created_at DESC
            LIMIT 20
            """
        )
        rows = (await db.execute(q)).fetchall()
        for r in rows:
            print(
                f"id={r.id} user={r.user_id} platform={r.platform} "
                f"status={r.status} created={r.created_at} err={r.err}"
            )


if __name__ == "__main__":
    asyncio.run(main())
