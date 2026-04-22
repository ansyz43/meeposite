#!/bin/bash
set -e

BASE=https://meepo.su

echo "=== 1. Health ==="
curl -sf "$BASE/api/health" -o - -w '\nHTTP %{http_code} in %{time_total}s\n'

echo
echo "=== 2. Landing (frontend) ==="
curl -sI "$BASE/" | head -3

echo
echo "=== 3. Invalid login (422 expected) ==="
curl -s -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' \
  --data '{"email":"bad@example.com","password":"wrong"}' \
  -w '\nHTTP %{http_code}\n'

echo
echo "=== 4. Register new test user ==="
EMAIL="smoketest_$(date +%s)@example.com"
PASS="TestPass123!"
REG_RES=$(curl -s -X POST "$BASE/api/auth/register" \
  -H 'Content-Type: application/json' \
  --data "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"name\":\"Smoke\"}")
echo "$REG_RES"

echo
echo "=== 5. Login as that user ==="
TOKEN=$(curl -s -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' \
  --data "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
if [ -z "$TOKEN" ]; then echo "LOGIN FAILED"; exit 1; fi
echo "Got token (len=${#TOKEN})"

echo
echo "=== 6. /api/bot (authorised, expect 200 + null/empty bot) ==="
curl -sf "$BASE/api/bot" -H "Authorization: Bearer $TOKEN" -w '\nHTTP %{http_code}\n'

echo
echo "=== 7. /api/profile (me) ==="
curl -sf "$BASE/api/profile" -H "Authorization: Bearer $TOKEN" -w '\nHTTP %{http_code}\n'

echo
echo "=== 8. Rate-limit /api/content/plans/generate (3/min, 4th должен быть 429) ==="
for i in 1 2 3 4; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/content/plans/generate" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    --data '{"platform":"telegram","period_days":7}')
  echo "req $i: HTTP $code"
done

echo
echo "=== 9. IG parser feature-flag (должно быть 503) ==="
curl -s -X POST "$BASE/api/content/profile/auto-detect" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"username":"nike"}' \
  -w '\nHTTP %{http_code}\n'

echo
echo "=== 10. Cleanup test user ==="
# Delete via DB
ssh_cmd="docker compose -f /root/meeposite/docker-compose.yml exec -T db psql -U meepo -d meepo -c \"DELETE FROM users WHERE email='$EMAIL';\""
eval "$ssh_cmd"
