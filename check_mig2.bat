@echo off
echo START > "%~dp0mig_check2.txt"
ssh root@5.42.112.91 "ls -la /tmp/migrate_output.txt 2>&1; echo ---SEP---; test -f /tmp/migrate_output.txt && head -20 /tmp/migrate_output.txt || echo NO_SUCH_FILE" >> "%~dp0mig_check2.txt" 2>&1
echo END >> "%~dp0mig_check2.txt"
