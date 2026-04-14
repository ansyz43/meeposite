@echo off
echo START > "%~dp0server_check.txt"
ssh root@5.42.112.91 "ls -la /tmp/migrate_output.txt; echo EXITLS" >> "%~dp0server_check.txt" 2>&1
echo MID >> "%~dp0server_check.txt"
ssh root@5.42.112.91 "wc -l /tmp/migrate_output.txt; head -30 /tmp/migrate_output.txt; echo HEADEND" >> "%~dp0server_check.txt" 2>&1
echo END >> "%~dp0server_check.txt"
