#!/bin/bash
# Re-encrypt all bot tokens with primary ENCRYPTION_KEY.
set -e
cd /root/meeposite
docker compose exec -T backend python -c "
import asyncio
from sqlalchemy import select
from app.database import async_session
from app.models import Bot
from app.services.crypto import decrypt_token, encrypt_token

async def main():
    migrated = 0
    skipped = 0
    async with async_session() as db:
        res = await db.execute(select(Bot))
        bots = res.scalars().all()
        for b in bots:
            try:
                plain = decrypt_token(b.bot_token_encrypted)
            except Exception as e:
                print(f'  skip bot {b.id} ({b.bot_username}): {e}')
                skipped += 1
                continue
            b.bot_token_encrypted = encrypt_token(plain)
            migrated += 1
        await db.commit()
    print(f'Migrated: {migrated}, skipped: {skipped}')

asyncio.run(main())
"
