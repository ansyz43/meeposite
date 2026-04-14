@echo off
ssh root@5.42.112.91 "docker exec meeposite-db-1 psql -U meepo -d meepo -c 'SELECT id, bot_username, platform, user_id, allow_partners, is_active FROM bots;'"
echo ---CONTACTS-SEARCH---
ssh root@5.42.112.91 "docker exec meeposite-db-1 psql -U meepo -d meepo -c 'SELECT id, first_name, last_name, telegram_username, telegram_id, platform, bot_id FROM contacts ORDER BY id DESC LIMIT 30;'"
echo ---DONE---
