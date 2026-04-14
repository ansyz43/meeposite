@echo off
echo STEP1 > "%~dp0migrate_result.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose exec -T db psql -U meepo -d meepo -c 'ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;'" >> "%~dp0migrate_result.txt" 2>&1
echo STEP2 >> "%~dp0migrate_result.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose exec -T db psql -U meepo -d meepo -c ""UPDATE users SET is_admin = true WHERE email = 'kisuke43@gmail.com';"" " >> "%~dp0migrate_result.txt" 2>&1
echo STEP3 >> "%~dp0migrate_result.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose exec -T db psql -U meepo -d meepo -c 'DELETE FROM messages;'" >> "%~dp0migrate_result.txt" 2>&1
echo STEP4 >> "%~dp0migrate_result.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose exec -T db psql -U meepo -d meepo -c 'DELETE FROM referral_sessions;'" >> "%~dp0migrate_result.txt" 2>&1
echo STEP5 >> "%~dp0migrate_result.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose exec -T db psql -U meepo -d meepo -c 'DELETE FROM referral_partners;'" >> "%~dp0migrate_result.txt" 2>&1
echo STEP6 >> "%~dp0migrate_result.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose exec -T db psql -U meepo -d meepo -c 'DELETE FROM cashback_transactions;'" >> "%~dp0migrate_result.txt" 2>&1
echo STEP7 >> "%~dp0migrate_result.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose exec -T db psql -U meepo -d meepo -c 'DELETE FROM broadcasts;'" >> "%~dp0migrate_result.txt" 2>&1
echo STEP8 >> "%~dp0migrate_result.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose exec -T db psql -U meepo -d meepo -c 'DELETE FROM password_reset_tokens;'" >> "%~dp0migrate_result.txt" 2>&1
echo STEP9 >> "%~dp0migrate_result.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose exec -T db psql -U meepo -d meepo -c 'DELETE FROM contacts;'" >> "%~dp0migrate_result.txt" 2>&1
echo STEP10 >> "%~dp0migrate_result.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose exec -T db psql -U meepo -d meepo -c ""DELETE FROM bots WHERE bot_username = 'fitline02bot';"" " >> "%~dp0migrate_result.txt" 2>&1
echo STEP11 >> "%~dp0migrate_result.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose exec -T db psql -U meepo -d meepo -c ""DELETE FROM users WHERE email != 'kisuke43@gmail.com';"" " >> "%~dp0migrate_result.txt" 2>&1
echo STEP12 >> "%~dp0migrate_result.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose exec -T db psql -U meepo -d meepo -c ""UPDATE bots SET user_id = NULL, seller_link = NULL, greeting_message = NULL, bot_description = NULL, avatar_url = NULL, assistant_name = 'Ассистент', allow_partners = false, is_active = false;"" " >> "%~dp0migrate_result.txt" 2>&1
echo STEP13 >> "%~dp0migrate_result.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose exec -T db psql -U meepo -d meepo -c ""UPDATE users SET cashback_balance = 0 WHERE email = 'kisuke43@gmail.com';"" " >> "%~dp0migrate_result.txt" 2>&1
echo VERIFY1 >> "%~dp0migrate_result.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose exec -T db psql -U meepo -d meepo -c 'SELECT email, is_admin FROM users;'" >> "%~dp0migrate_result.txt" 2>&1
echo VERIFY2 >> "%~dp0migrate_result.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose exec -T db psql -U meepo -d meepo -c 'SELECT id, bot_username, platform, user_id FROM bots;'" >> "%~dp0migrate_result.txt" 2>&1
echo ALLDONE >> "%~dp0migrate_result.txt"
