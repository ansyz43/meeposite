#!/bin/bash
cd /root/meeposite
echo "=== recent plans ==="
docker compose exec -T db psql -U meepo -d meepo -c "SELECT id, user_id, platform, period_days, status, created_at FROM content_plans ORDER BY id DESC LIMIT 8;"

echo
echo "=== clear stuck generating ==="
docker compose exec -T db psql -U meepo -d meepo -c "UPDATE content_plans SET status='error', error_message='cancelled before fix' WHERE status='generating';"

echo
echo "=== tail last 30m for content_ai ==="
docker logs meeposite-backend-1 --since=30m 2>&1 | grep -iE "content_ai|Batched posts|Robust JSON" | tail -20
