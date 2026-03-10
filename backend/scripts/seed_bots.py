"""
Seed bot tokens into the pool.

Usage:
    python -m scripts.seed_bots TOKEN1 TOKEN2 TOKEN3 ...

Verifies each token via Telegram API, encrypts it, and inserts
into the database as an unassigned pool bot (user_id=NULL).
"""

import asyncio
import sys

import httpx
from sqlalchemy import select

# Adjust path so we can import app modules
sys.path.insert(0, ".")

from app.database import engine, async_session, Base
from app.models import Bot
from app.services.crypto import encrypt_token

TELEGRAM_API = "https://api.telegram.org/bot{token}"


async def verify_token(token: str) -> dict | None:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{TELEGRAM_API.format(token=token)}/getMe", timeout=10)
            data = resp.json()
            if data.get("ok"):
                return data["result"]
        except Exception as e:
            print(f"  Error verifying token: {e}")
    return None


async def main():
    tokens = sys.argv[1:]
    if not tokens:
        print("Usage: python -m scripts.seed_bots TOKEN1 TOKEN2 ...")
        sys.exit(1)

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        for token in tokens:
            token = token.strip()
            if not token:
                continue

            encrypted = encrypt_token(token)

            # Check if already exists
            existing = await session.execute(
                select(Bot).where(Bot.bot_token_encrypted == encrypted)
            )
            if existing.scalar_one_or_none():
                print(f"  SKIP: Token already in pool")
                continue

            # Verify via Telegram
            info = await verify_token(token)
            if not info:
                print(f"  FAIL: Invalid token, skipping")
                continue

            username = info.get("username", "unknown")
            bot = Bot(
                user_id=None,
                bot_token_encrypted=encrypted,
                bot_username=username,
                assistant_name="Ассистент",
                is_active=False,
            )
            session.add(bot)
            print(f"  OK: @{username} added to pool")

        await session.commit()

    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
