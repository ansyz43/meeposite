-- Add is_admin column
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;

-- Set kisuke43@gmail.com as admin
UPDATE users SET is_admin = true WHERE email = 'kisuke43@gmail.com';

-- Wipe: Delete all messages
DELETE FROM messages;

-- Wipe: Delete all referral sessions
DELETE FROM referral_sessions;

-- Wipe: Delete all referral partners
DELETE FROM referral_partners;

-- Wipe: Delete all cashback transactions
DELETE FROM cashback_transactions;

-- Wipe: Delete all broadcasts
DELETE FROM broadcasts;

-- Wipe: Delete all password reset tokens
DELETE FROM password_reset_tokens;

-- Wipe: Delete all contacts
DELETE FROM contacts;

-- Wipe: Delete @fitline02bot completely
DELETE FROM bots WHERE bot_username = 'fitline02bot';

-- Wipe: Delete all users except admin
DELETE FROM users WHERE email != 'kisuke43@gmail.com';

-- Reset remaining bots to pool
UPDATE bots SET user_id = NULL, seller_link = NULL, greeting_message = NULL, bot_description = NULL, avatar_url = NULL, assistant_name = 'Ассистент', allow_partners = false, is_active = false;

-- Reset admin cashback
UPDATE users SET cashback_balance = 0 WHERE email = 'kisuke43@gmail.com';

-- Verify
SELECT 'Users remaining:' as info, count(*) as cnt FROM users
UNION ALL
SELECT 'Bots remaining:', count(*) FROM bots
UNION ALL
SELECT 'Contacts remaining:', count(*) FROM contacts
UNION ALL
SELECT 'Messages remaining:', count(*) FROM messages;

SELECT email, is_admin, is_active FROM users;
SELECT id, bot_username, platform, user_id, is_active FROM bots;
