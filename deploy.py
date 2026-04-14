import subprocess
import time
import sys

def run_ssh(desc, cmd, timeout=60):
    print(f"\n{'='*60}")
    print(f"=== {desc} ===")
    print(f"{'='*60}")
    print(f"CMD: {cmd}")
    print()
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        print(f"EXIT CODE: {result.returncode}")
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT after {timeout}s")
        return -1
    except Exception as e:
        print(f"ERROR: {e}")
        return -1

# Step 1: SCP migrate_admin.sql to server
rc = run_ssh(
    "STEP 1: SCP migrate_admin.sql to server",
    r'scp c:\Users\Admin\Downloads\morphius\migrate_admin.sql root@5.42.112.91:/tmp/migrate_admin.sql',
    timeout=30
)
if rc != 0:
    print("Step 1 failed!")

# Step 2: Run SQL migration
rc = run_ssh(
    "STEP 2: Run SQL migration",
    'ssh root@5.42.112.91 "cat /tmp/migrate_admin.sql | docker compose -f /root/meeposite/docker-compose.yml exec -T db psql -U postgres -d meepo"',
    timeout=30
)
if rc != 0:
    print("Step 2 failed!")

# Step 3: Rebuild containers (background on server)
rc = run_ssh(
    "STEP 3: Rebuild backend and frontend",
    'ssh root@5.42.112.91 "cd /root/meeposite; nohup docker compose up -d --build backend frontend > /tmp/rebuild.log 2>&1 &"',
    timeout=30
)
if rc != 0:
    print("Step 3 failed!")

# Wait 30 seconds
print("\n>>> Waiting 30 seconds for containers to rebuild...")
sys.stdout.flush()
time.sleep(30)
print(">>> Wait complete.")

# Step 4: Check container health
rc = run_ssh(
    "STEP 4: Container health check",
    """ssh root@5.42.112.91 "docker ps --format 'table {{.Names}}\t{{.Status}}'" """,
    timeout=15
)
if rc != 0:
    print("Step 4 failed!")

print("\n" + "="*60)
print("=== DEPLOYMENT COMPLETE ===")
print("="*60)
