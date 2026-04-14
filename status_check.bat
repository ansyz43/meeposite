@echo off
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o ServerAliveInterval=15 root@5.42.112.91 "cd /root/meeposite && docker compose ps --format 'table {{.Name}}\t{{.Status}}'" > c:\Users\Admin\Downloads\morphius\status_ui.txt 2>&1
echo STATUS_DONE >> c:\Users\Admin\Downloads\morphius\status_ui.txt
