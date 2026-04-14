@echo off
echo REBUILDING > "%~dp0rebuild_result.txt"
ssh -o ConnectTimeout=10 -o ServerAliveInterval=30 root@5.42.112.91 "cd /root/meeposite; docker compose up -d --build backend frontend 2>&1; echo BUILD_EXIT=$?" >> "%~dp0rebuild_result.txt" 2>&1
echo DONE >> "%~dp0rebuild_result.txt"
