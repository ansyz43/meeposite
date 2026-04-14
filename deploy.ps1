$ErrorActionPreference = "Continue"

Write-Host "=== Step 1: Testing connection ==="
ssh root@5.42.112.91 "echo CONNECTED_OK"

Write-Host "=== Step 2: Adding is_admin column ==="
ssh root@5.42.112.91 "docker compose -f /root/meeposite/docker-compose.yml exec -T db psql -U postgres -d meepo -c 'ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;'"

Write-Host "=== Step 3: Setting admin ==="
ssh root@5.42.112.91 "docker compose -f /root/meeposite/docker-compose.yml exec -T db psql -U postgres -d meepo -c ""UPDATE users SET is_admin = true WHERE email = 'kisuke43@gmail.com';"""

Write-Host "=== Step 4: Deleting messages ==="
ssh root@5.42.112.91 "docker compose -f /root/meeposite/docker-compose.yml exec -T db psql -U postgres -d meepo -c 'DELETE FROM messages;'"

Write-Host "=== Step 5: Deleting referral_sessions ==="
ssh root@5.42.112.91 "docker compose -f /root/meeposite/docker-compose.yml exec -T db psql -U postgres -d meepo -c 'DELETE FROM referral_sessions;'"

Write-Host "=== Step 6: Deleting referral_partners ==="
ssh root@5.42.112.91 "docker compose -f /root/meeposite/docker-compose.yml exec -T db psql -U postgres -d meepo -c 'DELETE FROM referral_partners;'"

Write-Host "=== Step 7: Deleting cashback_transactions ==="
ssh root@5.42.112.91 "docker compose -f /root/meeposite/docker-compose.yml exec -T db psql -U postgres -d meepo -c 'DELETE FROM cashback_transactions;'"

Write-Host "=== Step 8: Deleting broadcasts ==="
ssh root@5.42.112.91 "docker compose -f /root/meeposite/docker-compose.yml exec -T db psql -U postgres -d meepo -c 'DELETE FROM broadcasts;'"

Write-Host "=== Step 9: Deleting password_reset_tokens ==="
ssh root@5.42.112.91 "docker compose -f /root/meeposite/docker-compose.yml exec -T db psql -U postgres -d meepo -c 'DELETE FROM password_reset_tokens;'"

Write-Host "=== Step 10: Deleting contacts ==="
ssh root@5.42.112.91 "docker compose -f /root/meeposite/docker-compose.yml exec -T db psql -U postgres -d meepo -c 'DELETE FROM contacts;'"

Write-Host "=== Step 11: Deleting fitline02bot ==="
ssh root@5.42.112.91 "docker compose -f /root/meeposite/docker-compose.yml exec -T db psql -U postgres -d meepo -c ""DELETE FROM bots WHERE bot_username = 'fitline02bot';"""

Write-Host "=== Step 12: Deleting other users ==="
ssh root@5.42.112.91 "docker compose -f /root/meeposite/docker-compose.yml exec -T db psql -U postgres -d meepo -c ""DELETE FROM users WHERE email != 'kisuke43@gmail.com';"""

Write-Host "=== Step 13: Resetting bots to pool ==="
ssh root@5.42.112.91 "docker compose -f /root/meeposite/docker-compose.yml exec -T db psql -U postgres -d meepo -c ""UPDATE bots SET user_id = NULL, seller_link = NULL, greeting_message = NULL, bot_description = NULL, avatar_url = NULL, assistant_name = 'Ассистент', allow_partners = false, is_active = false;"""

Write-Host "=== Step 14: Resetting admin cashback ==="
ssh root@5.42.112.91 "docker compose -f /root/meeposite/docker-compose.yml exec -T db psql -U postgres -d meepo -c ""UPDATE users SET cashback_balance = 0 WHERE email = 'kisuke43@gmail.com';"""

Write-Host "=== Step 15: Verification ==="
ssh root@5.42.112.91 "docker compose -f /root/meeposite/docker-compose.yml exec -T db psql -U postgres -d meepo -c 'SELECT * FROM users;'"
ssh root@5.42.112.91 "docker compose -f /root/meeposite/docker-compose.yml exec -T db psql -U postgres -d meepo -c 'SELECT id, bot_username, platform, user_id, is_active FROM bots;'"

Write-Host "=== Step 16: Rebuilding containers ==="
ssh root@5.42.112.91 "cd /root/meeposite; docker compose up -d --build backend frontend bot_worker"

Write-Host "=== DONE ==="
