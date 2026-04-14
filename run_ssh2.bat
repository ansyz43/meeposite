@echo off
echo Starting > "%~dp0ssh_result2.txt"
ssh root@5.42.112.91 "echo CONNECTED_OK" >> "%~dp0ssh_result2.txt" 2>&1
echo SSHDone >> "%~dp0ssh_result2.txt"
