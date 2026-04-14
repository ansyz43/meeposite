@echo off
ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no root@5.42.112.91 "cd /root/meeposite && git pull origin main && docker compose up -d --build frontend" > deploy_round2_out.txt 2>&1
echo DONE >> deploy_round2_out.txt
