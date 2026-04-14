@echo off
ssh root@5.42.112.91 "docker exec meeposite-db-1 psql -U morphius -d morphius -t -A -c 'SELECT count(*) FROM referral_partners;'"
echo ---PARTNERS---
ssh root@5.42.112.91 "docker exec meeposite-db-1 psql -U morphius -d morphius -c 'SELECT rp.id, u.name, u.email, rp.ref_code, rp.credits, rp.is_active FROM referral_partners rp JOIN users u ON u.id=rp.user_id;'"
echo ---SESSIONS---
ssh root@5.42.112.91 "docker exec meeposite-db-1 psql -U morphius -d morphius -c 'SELECT rs.id, rs.partner_id, rs.telegram_id, rs.is_active, rs.started_at FROM referral_sessions rs ORDER BY rs.started_at DESC LIMIT 20;'"
echo ---USERS-INNA-MASHA---
ssh root@5.42.112.91 "docker exec meeposite-db-1 psql -U morphius -d morphius -c 'SELECT id, name, email, ref_code, referred_by_id FROM users;'"
echo ---DONE---
