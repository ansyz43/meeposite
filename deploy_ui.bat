@echo off
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite && git pull origin main && docker compose up -d --build frontend" > c:\Users\Admin\Downloads\morphius\deploy_ui.txt 2>&1
echo DEPLOY_DONE >> c:\Users\Admin\Downloads\morphius\deploy_ui.txt
