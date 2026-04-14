@echo off
echo TRYING > "%~dp0ping_test.txt"
ssh -o ConnectTimeout=20 -o ServerAliveInterval=5 root@5.42.112.91 "echo SSH_OK" >> "%~dp0ping_test.txt" 2>&1
echo DONE >> "%~dp0ping_test.txt"
