@echo off
ssh -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=10 -o StrictHostKeyChecking=no root@5.42.112.91 "cd /root/meeposite && docker compose up -d --build frontend 2>&1 && echo BUILD_OK && docker ps --format 'table {{.Names}} {{.Status}}'" > deploy_shader2_out.txt 2>&1
echo DONE >> deploy_shader2_out.txt
