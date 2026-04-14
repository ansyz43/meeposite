@echo off
ssh root@5.42.112.91 "tail -30 /tmp/deploy.log 2>&1" > deploy_check_out.txt 2>&1
