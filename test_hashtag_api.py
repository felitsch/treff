"""Test script for hashtag sets API endpoints."""
import json
import urllib.request
import urllib.error

BASE = "http://localhost:8000"

def api(method, path, body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()) if e.read() else {}

# Login
status, data = api("POST", "/api/auth/login", {"email": "hashtag194@treff.de", "password": "test1234"})
if status != 200:
    status, data = api("POST", "/api/auth/register", {"email": "hashtag194@treff.de", "password": "test1234", "display_name": "Hashtag Test"})
    status, data = api("POST", "/api/auth/login", {"email": "hashtag194@treff.de", "password": "test1234"})

token = data.get("access_token", "")
with open("/tmp/claude/test_results.txt", "w") as f:
    f.write(f"Login status: {status}\n")
    f.write(f"Token length: {len(token)}\n\n")

    # 1. List hashtag sets (should include seeded defaults)
    s, d = api("GET", "/api/hashtag-sets", token=token)
    f.write(f"=== List Hashtag Sets: status={s}, total={d.get('total', 0)} ===\n")
    for hs in d.get("hashtag_sets", [])[:5]:
        f.write(f"  [{hs['id']}] {hs['name']} ({hs.get('country') or 'allgemein'}) "
                f"- {len(hs['hashtags'])} tags - score: {hs['performance_score']} "
                f"- default: {hs['is_default']}\n")
    f.write(f"  ... and {d.get('total', 0) - 5} more\n\n")

    # 2. Filter by country
    s2, d2 = api("GET", "/api/hashtag-sets?country=usa", token=token)
    f.write(f"=== Filter by country=usa: {d2.get('total', 0)} sets ===\n")
    for hs in d2.get("hashtag_sets", []):
        f.write(f"  [{hs['id']}] {hs['name']} - tags: {hs['hashtags'][:3]}...\n")
    f.write("\n")

    # 3. Create custom set
    s3, d3 = api("POST", "/api/hashtag-sets", {
        "name": "Test Custom 194",
        "hashtags": ["#TestHashtag", "#CustomSet", "#TREFFSprachreisen"],
        "category": "allgemein",
        "country": "usa",
        "performance_score": 5.0
    }, token=token)
    f.write(f"=== Create Custom Set: status={s3} ===\n")
    f.write(f"  ID: {d3.get('id')}, Name: {d3.get('name')}, Tags: {d3.get('hashtags')}\n")
    f.write(f"  is_default: {d3.get('is_default')}\n\n")
    custom_id = d3.get("id")

    # 4. Update custom set
    s4, d4 = api("PUT", f"/api/hashtag-sets/{custom_id}", {
        "name": "Updated Custom 194",
        "hashtags": ["#Updated", "#Custom", "#TREFFSprachreisen", "#NewTag"]
    }, token=token)
    f.write(f"=== Update Custom Set: status={s4} ===\n")
    f.write(f"  Name: {d4.get('name')}, Tags: {d4.get('hashtags')}\n\n")

    # 5. Suggest hashtags
    s5, d5 = api("POST", "/api/ai/suggest-hashtags", {
        "topic": "Highschool USA Erfahrung",
        "country": "usa",
        "platform": "instagram_feed",
        "category": "erfahrungsberichte",
        "tone": "jugendlich"
    }, token=token)
    f.write(f"=== Suggest Hashtags: status={s5}, source={d5.get('source')} ===\n")
    f.write(f"  Count: {d5.get('count')}\n")
    f.write(f"  Hashtags: {d5.get('hashtag_string', '')}\n")
    emoji_sug = d5.get("emoji_suggestions", {})
    f.write(f"  Emoji suggestions: {emoji_sug.get('recommended_emojis', [])}\n")
    f.write(f"  Emoji style: {emoji_sug.get('style_description', '')}\n\n")

    # 6. Emoji rules (jugendlich + usa)
    s6, d6 = api("GET", "/api/ai/emoji-rules?tone=jugendlich&country=usa", token=token)
    rules = d6.get("emoji_rules", {})
    f.write(f"=== Emoji Rules (jugendlich, usa): status={s6} ===\n")
    f.write(f"  Recommended: {rules.get('recommended_emojis', [])}\n")
    f.write(f"  Count range: {rules.get('count_range', {})}\n")
    f.write(f"  Country emojis: {rules.get('country_emojis', [])}\n")
    f.write(f"  Style: {rules.get('style_description', '')}\n")
    f.write(f"  Available tones: {d6.get('available_tones', [])}\n\n")

    # 7. Emoji rules (serioess + canada)
    s7, d7 = api("GET", "/api/ai/emoji-rules?tone=serioess&country=canada", token=token)
    rules2 = d7.get("emoji_rules", {})
    f.write(f"=== Emoji Rules (serioess, canada): status={s7} ===\n")
    f.write(f"  Recommended: {rules2.get('recommended_emojis', [])}\n")
    f.write(f"  Count range: {rules2.get('count_range', {})}\n")
    f.write(f"  Style: {rules2.get('style_description', '')}\n\n")

    # 8. Delete custom set
    s8, d8 = api("DELETE", f"/api/hashtag-sets/{custom_id}", token=token)
    f.write(f"=== Delete Custom Set: status={s8} ===\n")
    f.write(f"  Response: {d8}\n\n")

    f.write("ALL TESTS COMPLETED\n")
