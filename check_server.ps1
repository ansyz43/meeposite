$ErrorActionPreference = 'SilentlyContinue'
$output = & ssh root@5.42.112.91 "cat /tmp/migrate_output.txt" 2>&1
$output | Out-File -FilePath "c:\Users\Admin\Downloads\morphius\mig_result.txt" -Encoding utf8
Write-Host "DONE_WRITING_FILE"
