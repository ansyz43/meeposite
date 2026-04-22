#!/bin/bash
set -e
cd /root/meeposite

echo "=== DB state ==="
docker compose exec -T db psql -U meepo -d meepo -t -c "
SELECT 'users=' || count(*) FROM users
UNION ALL SELECT 'bots=' || count(*) FROM bots
UNION ALL SELECT 'contacts=' || count(*) FROM contacts
UNION ALL SELECT 'messages=' || count(*) FROM messages
UNION ALL SELECT 'plans=' || count(*) FROM content_plans
UNION ALL SELECT 'plans_generating=' || count(*) FROM content_plans WHERE status='generating'
UNION ALL SELECT 'plans_error=' || count(*) FROM content_plans WHERE status='error'
UNION ALL SELECT 'plans_ready=' || count(*) FROM content_plans WHERE status='ready';
"

echo
echo "=== Watchdog alive? ==="
docker logs meeposite-backend-1 --since=10m 2>&1 | grep -c "Plan watchdog" || true

echo
echo "=== Bot worker status ==="
docker compose ps bot_worker
docker logs meeposite-bot_worker-1 --tail=10 2>&1 | grep -iE "startup|error|started" | tail -5

echo
echo "=== /api/health via nginx ==="
curl -sf http://localhost/api/health -o - -w '\nHTTP %{http_code}\n' || echo "FAIL"

echo
echo "=== test rate-limit on /api/content/plans/generate (expect 401 for unauth) ==="
for i in 1 2 3 4; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost/api/content/plans/generate -H "Content-Type: application/json" -d '{"bot_id":1,"days":30}')
  echo "req $i: HTTP $code"
done

echo
echo "=== CF real-IP in nginx log (last 3 lines) ==="
docker logs meeposite-nginx-1 --tail=3 2>&1 || true
