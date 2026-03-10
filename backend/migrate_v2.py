"""
Migration script: XOR → Fernet re-encryption + Float → Numeric columns.

Run ONCE after deploying the new code:
    docker compose exec backend python migrate_v2.py

This script:
1. Alters cashback_balance, amount, source_amount from FLOAT to NUMERIC(12,2)
2. Re-encrypts all bot tokens from old XOR to new Fernet encryption
3. Adds missing indexes
"""

import asyncio
import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://meepo:changeme@db:5432/meepo")
SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key-change-in-production")


def _xor_decrypt(encrypted: str) -> str:
    """Old XOR decryption for migration purposes."""
    key = hashlib.sha256(SECRET_KEY.encode()).digest()
    encrypted_bytes = base64.urlsafe_b64decode(encrypted.encode())
    decrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(encrypted_bytes))
    return decrypted.decode()


def _fernet_encrypt(token: str) -> str:
    """New Fernet encryption."""
    key = hashlib.sha256(SECRET_KEY.encode()).digest()
    f = Fernet(base64.urlsafe_b64encode(key))
    return f.encrypt(token.encode()).decode()


def _fernet_decrypt(encrypted: str) -> str:
    """Try Fernet decryption (to check if already migrated)."""
    key = hashlib.sha256(SECRET_KEY.encode()).digest()
    f = Fernet(base64.urlsafe_b64encode(key))
    return f.decrypt(encrypted.encode()).decode()


async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession)

    async with session_factory() as session:
        # 1. Alter columns from FLOAT to NUMERIC(12,2) (idempotent)
        print("[1/3] Altering money columns to NUMERIC(12,2)...")
        alter_statements = [
            "ALTER TABLE users ALTER COLUMN cashback_balance TYPE NUMERIC(12,2) USING cashback_balance::numeric(12,2)",
            "ALTER TABLE cashback_transactions ALTER COLUMN amount TYPE NUMERIC(12,2) USING amount::numeric(12,2)",
            "ALTER TABLE cashback_transactions ALTER COLUMN source_amount TYPE NUMERIC(12,2) USING source_amount::numeric(12,2)",
        ]
        for stmt in alter_statements:
            try:
                await session.execute(text(stmt))
                print(f"  OK: {stmt.split('ALTER COLUMN')[1].split('TYPE')[0].strip() if 'ALTER COLUMN' in stmt else stmt}")
            except Exception as e:
                if "already" in str(e).lower() or "numeric" in str(e).lower():
                    print(f"  SKIP (already done): {e}")
                else:
                    print(f"  WARN: {e}")
        await session.commit()

        # 2. Add missing indexes (idempotent with IF NOT EXISTS)
        print("[2/3] Adding missing indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS ix_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS ix_users_ref_code ON users(ref_code)",
            "CREATE INDEX IF NOT EXISTS ix_users_referred_by_id ON users(referred_by_id)",
            "CREATE INDEX IF NOT EXISTS ix_contacts_bot_id ON contacts(bot_id)",
            "CREATE INDEX IF NOT EXISTS ix_contacts_telegram_id ON contacts(telegram_id)",
            "CREATE INDEX IF NOT EXISTS ix_messages_contact_id ON messages(contact_id)",
            "CREATE INDEX IF NOT EXISTS ix_referral_partners_user_id ON referral_partners(user_id)",
            "CREATE INDEX IF NOT EXISTS ix_referral_partners_bot_id ON referral_partners(bot_id)",
            "CREATE INDEX IF NOT EXISTS ix_referral_partners_ref_code ON referral_partners(ref_code)",
            "CREATE INDEX IF NOT EXISTS ix_referral_sessions_partner_id ON referral_sessions(partner_id)",
            "CREATE INDEX IF NOT EXISTS ix_referral_sessions_telegram_id ON referral_sessions(telegram_id)",
            "CREATE INDEX IF NOT EXISTS ix_cashback_transactions_user_id ON cashback_transactions(user_id)",
            "CREATE INDEX IF NOT EXISTS ix_cashback_transactions_from_user_id ON cashback_transactions(from_user_id)",
        ]
        for stmt in indexes:
            try:
                await session.execute(text(stmt))
            except Exception as e:
                print(f"  WARN: {e}")
        await session.commit()
        print(f"  OK: {len(indexes)} indexes ensured")

        # 3. Re-encrypt bot tokens from XOR to Fernet
        print("[3/3] Re-encrypting bot tokens (XOR → Fernet)...")
        result = await session.execute(text("SELECT id, bot_token_encrypted FROM bots"))
        bots = result.all()
        migrated = 0
        skipped = 0
        for bot_id, encrypted_token in bots:
            # Check if already Fernet-encrypted
            try:
                _fernet_decrypt(encrypted_token)
                skipped += 1
                continue  # Already migrated
            except (InvalidToken, Exception):
                pass

            # Try XOR decryption and re-encrypt with Fernet
            try:
                plaintext = _xor_decrypt(encrypted_token)
                # Validate token format (Telegram tokens look like "123456:ABC-DEF...")
                if ":" not in plaintext:
                    print(f"  WARN: bot #{bot_id} - decrypted token doesn't look valid, skipping")
                    continue
                new_encrypted = _fernet_encrypt(plaintext)
                await session.execute(
                    text("UPDATE bots SET bot_token_encrypted = :token WHERE id = :id"),
                    {"token": new_encrypted, "id": bot_id},
                )
                migrated += 1
            except Exception as e:
                print(f"  ERROR: bot #{bot_id} - {e}")

        await session.commit()
        print(f"  OK: {migrated} migrated, {skipped} already Fernet")

    await engine.dispose()
    print("\nMigration complete!")


if __name__ == "__main__":
    asyncio.run(main())
