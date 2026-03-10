"""
One-time migration script: XOR→Fernet re-encryption + Float→Numeric columns + new indexes.
Run inside the backend container:
    docker compose exec backend python /app/migrate_v2.py
"""
import asyncio
import base64
import hashlib
import os

from cryptography.fernet import Fernet
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://meepo:changeme@localhost:5432/meepo")
SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key-change-in-production")


def _old_decrypt_xor(encrypted: str) -> str:
    """Old XOR decryption for migration."""
    key = hashlib.sha256(SECRET_KEY.encode()).digest()
    encrypted_bytes = base64.urlsafe_b64decode(encrypted.encode())
    decrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(encrypted_bytes))
    return decrypted.decode()


def _new_encrypt_fernet(token: str) -> str:
    """New Fernet encryption."""
    key = hashlib.sha256(SECRET_KEY.encode()).digest()
    f = Fernet(base64.urlsafe_b64encode(key))
    return f.encrypt(token.encode()).decode()


async def migrate():
    engine = create_async_engine(DATABASE_URL, echo=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession)

    async with session_factory() as session:
        # 1. Re-encrypt bot tokens: XOR → Fernet
        print("=== Re-encrypting bot tokens ===")
        result = await session.execute(text("SELECT id, bot_token_encrypted FROM bots"))
        rows = result.all()
        for row in rows:
            bot_id, old_encrypted = row
            try:
                plain_token = _old_decrypt_xor(old_encrypted)
                new_encrypted = _new_encrypt_fernet(plain_token)
                await session.execute(
                    text("UPDATE bots SET bot_token_encrypted = :enc WHERE id = :id"),
                    {"enc": new_encrypted, "id": bot_id},
                )
                print(f"  Bot #{bot_id}: OK")
            except Exception as e:
                print(f"  Bot #{bot_id}: SKIP ({e})")

        # 2. Alter columns: Float → Numeric(12,2)
        print("\n=== Altering column types ===")
        alter_statements = [
            "ALTER TABLE users ALTER COLUMN cashback_balance TYPE NUMERIC(12,2) USING cashback_balance::NUMERIC(12,2)",
            "ALTER TABLE cashback_transactions ALTER COLUMN amount TYPE NUMERIC(12,2) USING amount::NUMERIC(12,2)",
            "ALTER TABLE cashback_transactions ALTER COLUMN source_amount TYPE NUMERIC(12,2) USING source_amount::NUMERIC(12,2)",
        ]
        for stmt in alter_statements:
            try:
                await session.execute(text(stmt))
                print(f"  OK: {stmt[:60]}...")
            except Exception as e:
                print(f"  SKIP: {e}")

        # 3. Create indexes if not exist
        print("\n=== Creating indexes ===")
        index_statements = [
            "CREATE INDEX IF NOT EXISTS ix_users_referred_by_id ON users (referred_by_id)",
            "CREATE INDEX IF NOT EXISTS ix_contacts_telegram_id ON contacts (telegram_id)",
            "CREATE INDEX IF NOT EXISTS ix_referral_sessions_telegram_id ON referral_sessions (telegram_id)",
            "CREATE INDEX IF NOT EXISTS ix_cashback_transactions_from_user_id ON cashback_transactions (from_user_id)",
        ]
        for stmt in index_statements:
            try:
                await session.execute(text(stmt))
                print(f"  OK: {stmt[:60]}...")
            except Exception as e:
                print(f"  SKIP: {e}")

        await session.commit()
        print("\n=== Migration complete ===")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())
