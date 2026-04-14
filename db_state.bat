@echo off
echo CHECK1 > "%~dp0db_state.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose exec -T db psql -U meepo -d meepo -c 'SELECT email, is_admin FROM users;' 2>&1" >> "%~dp0db_state.txt" 2>&1
echo CHECK2 >> "%~dp0db_state.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; cat docker-compose.yml | grep -A5 POSTGRES 2>&1" >> "%~dp0db_state.txt" 2>&1
echo CHECK3 >> "%~dp0db_state.txt"
