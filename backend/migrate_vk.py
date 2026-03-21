"""
Migration: Add VK platform support.

Adds platform/vk_group_id columns to bots, platform/vk_id columns to contacts,
updates unique constraints.
"""

import asyncio
import asyncpg


async def migrate():
    conn = await asyncpg.connect(
        "postgresql://meepo:changeme@db:5432/meepo"
    )

    try:
        await conn.execute("BEGIN")

        # ── Bots table ──
        # Add platform column
        await conn.execute("""
            ALTER TABLE bots ADD COLUMN IF NOT EXISTS platform VARCHAR(10) NOT NULL DEFAULT 'telegram'
        """)

        # Add vk_group_id column
        await conn.execute("""
            ALTER TABLE bots ADD COLUMN IF NOT EXISTS vk_group_id BIGINT
        """)

        # Drop old unique constraint on user_id alone
        await conn.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'bots_user_id_key'
                    AND conrelid = 'bots'::regclass
                ) THEN
                    ALTER TABLE bots DROP CONSTRAINT bots_user_id_key;
                END IF;
            END $$
        """)

        # Add composite unique constraint (user_id, platform)
        await conn.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'uq_bot_user_platform'
                    AND conrelid = 'bots'::regclass
                ) THEN
                    ALTER TABLE bots ADD CONSTRAINT uq_bot_user_platform UNIQUE (user_id, platform);
                END IF;
            END $$
        """)

        # Add index on user_id (was previously covered by unique constraint)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_bots_user_id ON bots (user_id)
        """)

        # ── Contacts table ──
        # Add platform column
        await conn.execute("""
            ALTER TABLE contacts ADD COLUMN IF NOT EXISTS platform VARCHAR(10) NOT NULL DEFAULT 'telegram'
        """)

        # Make telegram_id nullable
        await conn.execute("""
            ALTER TABLE contacts ALTER COLUMN telegram_id DROP NOT NULL
        """)

        # Add vk_id column
        await conn.execute("""
            ALTER TABLE contacts ADD COLUMN IF NOT EXISTS vk_id BIGINT
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_contacts_vk_id ON contacts (vk_id)
        """)

        # Drop old unnamed unique constraint on (bot_id, telegram_id)
        await conn.execute("""
            DO $$
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN
                    SELECT conname FROM pg_constraint
                    WHERE conrelid = 'contacts'::regclass
                    AND contype = 'u'
                    AND conname NOT IN ('uq_contact_bot_tg', 'uq_contact_bot_vk')
                LOOP
                    EXECUTE 'ALTER TABLE contacts DROP CONSTRAINT ' || quote_ident(r.conname);
                END LOOP;
            END $$
        """)

        # Add named unique constraints
        await conn.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'uq_contact_bot_tg'
                    AND conrelid = 'contacts'::regclass
                ) THEN
                    ALTER TABLE contacts ADD CONSTRAINT uq_contact_bot_tg UNIQUE (bot_id, telegram_id);
                END IF;
            END $$
        """)
        await conn.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'uq_contact_bot_vk'
                    AND conrelid = 'contacts'::regclass
                ) THEN
                    ALTER TABLE contacts ADD CONSTRAINT uq_contact_bot_vk UNIQUE (bot_id, vk_id);
                END IF;
            END $$
        """)

        await conn.execute("COMMIT")
        print("VK migration completed successfully!")

    except Exception as e:
        await conn.execute("ROLLBACK")
        print(f"Migration failed: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
