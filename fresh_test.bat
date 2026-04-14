@echo off
echo RUNNING > "%~dp0fresh_test.txt"
ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no root@5.42.112.91 "echo OK_FRESH" >> "%~dp0fresh_test.txt" 2>&1
echo DONE >> "%~dp0fresh_test.txt"
