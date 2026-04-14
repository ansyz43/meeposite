@echo off
echo CHECK > "%~dp0docker_status.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite; docker compose ps --format 'table {{.Names}}\t{{.Status}}' 2>&1" >> "%~dp0docker_status.txt" 2>&1
echo DONE >> "%~dp0docker_status.txt"
