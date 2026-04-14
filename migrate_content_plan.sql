-- Migration 0002: Content Plan tables
-- Safe: all CREATE TABLE IF NOT EXISTS, no changes to existing tables

CREATE TABLE IF NOT EXISTS content_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    niche VARCHAR(255) NOT NULL,
    platforms TEXT NOT NULL DEFAULT 'instagram,telegram',
    tone VARCHAR(100) NOT NULL DEFAULT 'friendly',
    target_audience TEXT NOT NULL DEFAULT '',
    topics TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_content_profiles_user_id ON content_profiles(user_id);

CREATE TABLE IF NOT EXISTS competitor_sources (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER NOT NULL REFERENCES content_profiles(id) ON DELETE CASCADE,
    platform VARCHAR(20) NOT NULL,
    channel_username VARCHAR(255) NOT NULL,
    channel_title VARCHAR(255),
    last_parsed_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_comp_profile_chan UNIQUE (profile_id, platform, channel_username)
);
CREATE INDEX IF NOT EXISTS ix_competitor_sources_profile_id ON competitor_sources(profile_id);

CREATE TABLE IF NOT EXISTS competitor_posts (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,
    channel_username VARCHAR(255) NOT NULL,
    text TEXT NOT NULL,
    views INTEGER,
    reactions INTEGER,
    posted_at TIMESTAMP,
    parsed_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_competitor_posts_platform ON competitor_posts(platform);
CREATE INDEX IF NOT EXISTS ix_competitor_posts_channel ON competitor_posts(channel_username);

CREATE TABLE IF NOT EXISTS content_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    period_days INTEGER DEFAULT 7,
    status VARCHAR(20) DEFAULT 'generating',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_content_plans_user_id ON content_plans(user_id);

CREATE TABLE IF NOT EXISTS content_plan_items (
    id SERIAL PRIMARY KEY,
    plan_id INTEGER NOT NULL REFERENCES content_plans(id) ON DELETE CASCADE,
    day_number INTEGER NOT NULL,
    post_type VARCHAR(50) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    text TEXT NOT NULL,
    hashtags TEXT,
    best_time VARCHAR(20),
    is_edited BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_content_plan_items_plan_id ON content_plan_items(plan_id);
