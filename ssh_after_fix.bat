@echo off
echo S1 > "%~dp0ssh_after_fix.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "echo SSH_WORKS; hostname; uptime" >> "%~dp0ssh_after_fix.txt" 2>&1
echo S2 >> "%~dp0ssh_after_fix.txt"
