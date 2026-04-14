@echo off
echo CHECKING > "%~dp0quick_db.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "ls -la /tmp/migrate_output.txt 2>&1; echo SEP; cd /root/meeposite; docker compose exec -T db psql -U postgres -d meepo -c '\dt'" >> "%~dp0quick_db.txt" 2>&1
echo DONE >> "%~dp0quick_db.txt"
