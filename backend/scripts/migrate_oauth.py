"""
Migration: Add OAuth columns to users table.
Run inside backend container:
  python scripts/migrate_oauth.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database import engine


async def migrate():
    async with engine.begin() as conn:
        # Make password_hash nullable
        await conn.execute(text(
            "ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL"
        ))
        print("✓ password_hash is now nullable")

        # Add telegram_id column
        await conn.execute(text("""
            DO $$ BEGIN
                ALTER TABLE users ADD COLUMN telegram_id BIGINT UNIQUE;
            EXCEPTION WHEN duplicate_column THEN NULL;
            END $$;
        """))
        print("✓ telegram_id column added")

        # Add google_id column
        await conn.execute(text("""
            DO $$ BEGIN
                ALTER TABLE users ADD COLUMN google_id VARCHAR(255) UNIQUE;
            EXCEPTION WHEN duplicate_column THEN NULL;
            END $$;
        """))
        print("✓ google_id column added")

        # Add auth_provider column
        await conn.execute(text("""
            DO $$ BEGIN
                ALTER TABLE users ADD COLUMN auth_provider VARCHAR(20);
            EXCEPTION WHEN duplicate_column THEN NULL;
            END $$;
        """))
        print("✓ auth_provider column added")

        # Create indexes
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_users_telegram_id ON users (telegram_id);
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id);
        """))
        print("✓ indexes created")

    print("\n🎉 OAuth migration completed!")


if __name__ == "__main__":
    asyncio.run(migrate())
