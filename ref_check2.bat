@echo off
ssh root@5.42.112.91 "docker exec meeposite-db-1 psql -U meepo -d meepo -c 'SELECT rp.id, u.name, u.email, rp.ref_code, rp.credits, rp.is_active FROM referral_partners rp JOIN users u ON u.id=rp.user_id;'"
echo ---SESSIONS---
ssh root@5.42.112.91 "docker exec meeposite-db-1 psql -U meepo -d meepo -c 'SELECT rs.id, rs.partner_id, rs.telegram_id, rs.is_active, rs.started_at FROM referral_sessions rs ORDER BY rs.started_at DESC LIMIT 20;'"
echo ---USERS---
ssh root@5.42.112.91 "docker exec meeposite-db-1 psql -U meepo -d meepo -c 'SELECT id, name, email, ref_code, referred_by_id FROM users ORDER BY id;'"
echo ---CONTACTS---
ssh root@5.42.112.91 "docker exec meeposite-db-1 psql -U meepo -d meepo -c 'SELECT c.id, c.first_name, c.last_name, c.telegram_username, c.telegram_id, c.platform, c.bot_id FROM contacts c ORDER BY c.id DESC LIMIT 30;'"
echo ---DONE---
