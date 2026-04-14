@echo off
echo S1 > "%~dp0server_status.txt"
ssh -o ConnectTimeout=15 root@5.42.112.91 "hostname" >> "%~dp0server_status.txt" 2>&1
echo S2 >> "%~dp0server_status.txt"
ssh -o ConnectTimeout=15 root@5.42.112.91 "cat /tmp/migrate_output.txt" >> "%~dp0server_status.txt" 2>&1
echo S3 >> "%~dp0server_status.txt"
