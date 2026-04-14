@echo off
ssh root@5.42.112.91 "tail -30 /tmp/deploy.log 2>&1; echo '---'; docker ps --format 'table {{.Names}}\t{{.Status}}' 2>&1" > c:\Users\Admin\Downloads\morphius\deploy_status.txt 2>&1
