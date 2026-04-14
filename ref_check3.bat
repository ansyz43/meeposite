@echo off
ssh root@5.42.112.91 "docker exec meeposite-db-1 psql -U meepo -d meepo -c 'SELECT id, name, email, ref_code, referred_by_id FROM users ORDER BY id;' -c 'SELECT * FROM referral_partners;' -c 'SELECT * FROM referral_sessions ORDER BY id DESC LIMIT 20;' -c 'SELECT id, first_name, last_name, telegram_username, telegram_id, platform, bot_id FROM contacts ORDER BY id DESC LIMIT 30;'"
