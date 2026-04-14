@echo off
echo START > "%~dp0simple_check.txt"
ssh -o ConnectTimeout=10 root@5.42.112.91 "test -f /tmp/migrate_output.txt && echo EXISTS || echo NOT_EXISTS" >> "%~dp0simple_check.txt" 2>&1
echo END >> "%~dp0simple_check.txt"
