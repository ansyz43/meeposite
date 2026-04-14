@echo off
echo === MIGRATION OUTPUT === > "%~dp0full_status.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cat /tmp/migrate_output.txt 2>/dev/null; echo EXIT" >> "%~dp0full_status.txt" 2>&1
echo === DB CHECK === >> "%~dp0full_status.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose exec -T db psql -U postgres -d meepo -c 'SELECT email, is_admin FROM users;'" >> "%~dp0full_status.txt" 2>&1
echo === BOTS === >> "%~dp0full_status.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose exec -T db psql -U postgres -d meepo -c 'SELECT id, bot_username, platform, user_id FROM bots;'" >> "%~dp0full_status.txt" 2>&1
echo === DOCKER === >> "%~dp0full_status.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose ps --format 'table {{.Names}}\t{{.Status}}'" >> "%~dp0full_status.txt" 2>&1
echo === DONE === >> "%~dp0full_status.txt"
