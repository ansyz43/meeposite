@echo off
ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no root@5.42.112.91 "cd /root/meeposite && git log --oneline -1 && docker compose up -d --build frontend 2>&1 | tail -5 && docker ps --format 'table {{.Names}}\t{{.Status}}'" > deploy_round2_check.txt 2>&1
echo DONE >> deploy_round2_check.txt
