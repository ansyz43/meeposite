@echo off
echo TRYING_VERBOSE > "%~dp0ssh_verbose.txt"
ssh -v -o ConnectTimeout=20 root@5.42.112.91 "echo OK" >> "%~dp0ssh_verbose.txt" 2>&1
echo EXIT_CODE=%ERRORLEVEL% >> "%~dp0ssh_verbose.txt"
