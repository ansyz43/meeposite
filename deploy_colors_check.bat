@echo off
ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no root@5.42.112.91 "cat /tmp/build.log 2>/dev/null | tail -8; echo '---'; docker ps --format 'table {{.Names}} {{.Status}}'" > deploy_colors_check.txt 2>&1
echo DONE >> deploy_colors_check.txt
