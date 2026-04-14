@echo off
ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no root@5.42.112.91 "cd /root/meeposite && git pull origin main && nohup docker compose up -d --build frontend > /tmp/build.log 2>&1 &" > deploy_popup_out.txt 2>&1
echo LAUNCHED >> deploy_popup_out.txt
