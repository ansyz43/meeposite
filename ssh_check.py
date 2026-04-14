import subprocess
import sys

def run_ssh(cmd):
    result = subprocess.run(
        ["ssh", "root@5.42.112.91", cmd],
        capture_output=True, text=True, timeout=120
    )
    return result.stdout, result.stderr, result.returncode

# Check if migrate_output.txt exists
stdout, stderr, rc = run_ssh("ls -la /tmp/migrate_output.txt 2>&1; echo '---'; cat /tmp/migrate_output.txt 2>&1")
with open("c:\\Users\\Admin\\Downloads\\morphius\\ssh_capture.txt", "w", encoding="utf-8") as f:
    f.write(f"=== STDOUT (rc={rc}) ===\n")
    f.write(stdout)
    f.write(f"\n=== STDERR ===\n")
    f.write(stderr)
    
print(f"Return code: {rc}")
print(f"Stdout length: {len(stdout)}")
print(f"Stderr length: {len(stderr)}")
print("Saved to ssh_capture.txt")
