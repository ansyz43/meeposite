-- Migration: Create pending_bot_creations table for Managed Bots (Bot API 9.6)

CREATE TABLE IF NOT EXISTS pending_bot_creations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    suggested_username VARCHAR(255) NOT NULL,
    suggested_name VARCHAR(255) NOT NULL,
    bot_telegram_id BIGINT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    bot_id INTEGER REFERENCES bots(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_pending_bot_creations_user_id ON pending_bot_creations(user_id);
