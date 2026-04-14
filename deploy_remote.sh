#!/bin/bash
set -e
echo "=== STEP 2: Running SQL migration ==="
cat /tmp/migrate_admin.sql | docker compose -f /root/meeposite/docker-compose.yml exec -T db psql -U postgres -d meepo 2>&1
echo ""
echo "=== STEP 3: Rebuilding backend and frontend ==="
cd /root/meeposite
nohup docker compose up -d --build backend frontend > /tmp/rebuild.log 2>&1 &
BUILD_PID=$!
echo "Build started in background (PID: $BUILD_PID)"
echo ""
echo "=== Waiting 30 seconds for build ==="
sleep 30
echo ""
echo "=== STEP 4: Container health ==="
docker ps --format 'table {{.Names}}\t{{.Status}}'
echo ""
echo "=== DEPLOY COMPLETE ==="
