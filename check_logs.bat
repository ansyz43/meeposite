ssh -o ConnectTimeout=10 root@5.42.112.91 "docker ps -a && echo '---LOGS---' && docker logs --tail 50 meeposite-bot_worker-1 2>&1"
