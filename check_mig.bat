@echo off
ssh root@5.42.112.91 "cat /tmp/migrate_output.txt 2>/dev/null || echo FILE_NOT_FOUND" > "%~dp0mig_check.txt" 2>&1
