import httpx, os
url = os.environ["OPENAI_BASE_URL"].rstrip("/") + "/chat/completions"
h = {
    "Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
    "Content-Type": "application/json",
    "cf-aig-authorization": "Bearer " + os.environ["CF_AIG_TOKEN"],
}
for m in ["gpt-5.4", "gpt-4o", "gpt-4o-mini"]:
    try:
        r = httpx.post(url, json={"model": m, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 3}, headers=h, timeout=30)
        print(m, r.status_code, r.text[:200])
    except Exception as e:
        print(m, "ERROR", e)
