@echo off
echo S1 > "%~dp0ssh_fixed.txt"
ssh -o ConnectTimeout=15 root@5.42.112.91 "echo SSH_OK; hostname" >> "%~dp0ssh_fixed.txt" 2>&1
echo S2 >> "%~dp0ssh_fixed.txt"
