@echo off
ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no root@5.42.112.91 "cd /root/meeposite && git pull origin main && docker compose up -d --build frontend 2>&1 | tail -8 && echo '---' && docker ps --format 'table {{.Names}}\t{{.Status}}'" > deploy_shader_out.txt 2>&1
echo DONE >> deploy_shader_out.txt
