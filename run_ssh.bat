@echo off
ssh root@5.42.112.91 "cat /tmp/migrate_output.txt 2>/dev/null; echo DONE_CHECK" > "%~dp0ssh_result.txt" 2>&1
echo FILE_SAVED
type "%~dp0ssh_result.txt"
