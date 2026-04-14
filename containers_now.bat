@echo off
ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no root@5.42.112.91 "docker ps --format 'table {{.Names}} {{.Status}}'" > containers_now.txt 2>&1
echo DONE >> containers_now.txt
