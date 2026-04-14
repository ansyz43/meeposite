@echo off
ssh -o ConnectTimeout=5 root@5.42.112.91 "docker ps --format 'table {{.Names}} {{.Status}}'" > c:\Users\Admin\Downloads\morphius\docker_ps.txt 2>&1
