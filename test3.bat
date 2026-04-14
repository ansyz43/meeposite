@echo off
echo S1 > "%~dp0test3.txt"
ssh root@5.42.112.91 "hostname" >> "%~dp0test3.txt" 2>&1
echo S2 >> "%~dp0test3.txt"
ssh root@5.42.112.91 "ls /tmp/migrate_output.txt" >> "%~dp0test3.txt" 2>&1
echo S3 >> "%~dp0test3.txt"
ssh root@5.42.112.91 "wc -l /tmp/migrate_output.txt" >> "%~dp0test3.txt" 2>&1
echo S4 >> "%~dp0test3.txt"
