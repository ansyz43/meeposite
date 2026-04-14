ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite && git pull origin main && nohup docker compose up -d --build bot_worker > /tmp/build_prices.log 2>&1 &"
