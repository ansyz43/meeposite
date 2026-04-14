@echo off
ssh -o ConnectTimeout=10 -o ServerAliveInterval=15 -o ServerAliveCountMax=3 root@5.42.112.91 "cd /root/meeposite && git pull origin main && nohup docker compose up -d --build frontend backend > /tmp/build_chats.log 2>&1 &"
echo Deploy started. Check /tmp/build_chats.log on server after ~3 min.
