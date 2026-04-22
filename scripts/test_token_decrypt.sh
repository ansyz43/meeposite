#!/bin/bash
set -e
cd /root/meeposite
docker compose exec -T backend python -c "
import asyncio, sys
from sqlalchemy import select
from app.database import async_session
from app.models import Bot
from app.services.crypto import decrypt_token

async def main():
    async with async_session() as db:
        res = await db.execute(select(Bot))
        bots = res.scalars().all()
    ok = 0
    failed = []
    for b in bots:
        try:
            t = decrypt_token(b.bot_token_encrypted)
            assert t and len(t) > 10
            ok += 1
        except Exception as e:
            failed.append((b.id, b.bot_username, str(e)[:80]))
    print(f'Decrypted OK: {ok}/{len(bots)}')
    if failed:
        print('FAILED:')
        for f in failed:
            print(' ', f)
        sys.exit(1)

asyncio.run(main())
"
