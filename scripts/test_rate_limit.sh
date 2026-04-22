#!/bin/bash
# Test rate-limit under load
set -e
BASE=https://meepo.su
EMAIL="smoketest_rate_$(date +%s)@example.com"
PASS="TestPass123!"

echo "Creating test user..."
curl -sf -X POST "$BASE/api/auth/register" \
  -H 'Content-Type: application/json' \
  --data "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"name\":\"RateTest\"}" > /dev/null

TOKEN=$(curl -sf -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' \
  --data "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "Token OK, sending 25 rapid requests..."
CODES=""
for i in $(seq 1 25); do
  c=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/content/plans/generate" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    --data '{"platform":"telegram","period_days":7}')
  CODES="$CODES $c"
done
echo "All codes: $CODES"
echo "429 (rate-limited):  $(echo $CODES | tr ' ' '\n' | grep -c '^429$' || echo 0)"
echo "400 (no bot):        $(echo $CODES | tr ' ' '\n' | grep -c '^400$' || echo 0)"
echo "202 (accepted):      $(echo $CODES | tr ' ' '\n' | grep -c '^202$' || echo 0)"

# cleanup
cd /root/meeposite
docker compose exec -T db psql -U meepo -d meepo -c "DELETE FROM users WHERE email='$EMAIL';" > /dev/null
echo "Cleaned up $EMAIL"
