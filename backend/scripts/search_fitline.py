"""Search Instagram for FitLine-related accounts and print results."""
import os, sys, time, json

sys.path.insert(0, "/app")
from instagrapi import Client

cl = Client()
session_file = "/tmp/ig_session.json"
sid = os.environ.get("INSTAGRAM_SESSION_ID", "")

if os.path.exists(session_file):
    cl.load_settings(session_file)
    cl.login_by_sessionid(sid)
else:
    cl.login_by_sessionid(sid)
    cl.dump_settings(session_file)

queries = ["fitline", "фитлайн", "pm international", "fitline russia", "fitline health",
           "fitline germany", "fitline partner", "fitline wellness", "pminternational"]
seen = set()
results = []

for q in queries:
    try:
        users = cl.search_users_v1(q, count=30)
        for u in users:
            if u.username not in seen and not u.is_private:
                seen.add(u.username)
                results.append({
                    "username": u.username,
                    "full_name": u.full_name or "",
                    "pk": str(u.pk),
                })
        time.sleep(3)
    except Exception as e:
        print(f"ERR [{q}]: {e}", file=sys.stderr)
        time.sleep(5)

# Just print usernames — skip user_info to avoid 429
print(f"TOTAL: {len(results)} accounts found")
for r in results:
    print(f"{r['username']}|{r['full_name']}|{r['pk']}")
