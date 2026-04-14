@echo off
echo S1 > "%~dp0post_reboot.txt"
ssh -o ConnectTimeout=15 root@5.42.112.91 "hostname; uptime" >> "%~dp0post_reboot.txt" 2>&1
echo S2 >> "%~dp0post_reboot.txt"
ssh -o ConnectTimeout=15 root@5.42.112.91 "cd /root/meeposite; docker ps --format 'table {{.Names}}\t{{.Status}}'" >> "%~dp0post_reboot.txt" 2>&1
echo S3 >> "%~dp0post_reboot.txt"
ssh -o ConnectTimeout=15 root@5.42.112.91 "cat /tmp/migrate_output.txt" >> "%~dp0post_reboot.txt" 2>&1
echo S4 >> "%~dp0post_reboot.txt"
