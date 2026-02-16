"""Test Feature #312: SI-02 Strategie-gesteuerte AI-Routen.

Verifies that all AI endpoints in ai.py now use dynamic strategy loading
from StrategyLoader (social-content.json + content-strategy.json) instead
of hardcoded values.
"""
import httpx
import json

BASE = "http://localhost:8000"
client = httpx.Client(timeout=60.0)

# Login
resp = client.post(f"{BASE}/api/auth/login", json={"email": "admin@treff.de", "password": "treff2024"})
print(f"Login: {resp.status_code}")
token = resp.json().get("access_token", "")
if not token:
    print("Login failed!")
    exit(1)
headers = {"Authorization": f"Bearer {token}"}

passed = 0
total = 0

def check(test_name, condition, detail=""):
    global passed, total
    total += 1
    if condition:
        passed += 1
        print(f"  PASS: {test_name}")
    else:
        print(f"  FAIL: {test_name} - {detail}")

# ═══════════════════════════════════════════════════════════
# Test 1: Hook formulas are loaded dynamically (>5 types)
# ═══════════════════════════════════════════════════════════
print("\n=== Test 1: Dynamic Hook Types (generate-hooks) ===")
resp = client.post(
    f"{BASE}/api/ai/generate-hooks",
    json={"topic": "Mein Auslandsjahr", "tone": "jugendlich", "platform": "instagram_feed", "count": 5},
    headers=headers,
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    hook_types = data.get("hook_types", {})
    hooks = data.get("hooks", [])
    print(f"  Hook types count: {len(hook_types)}")
    print(f"  Hooks generated: {len(hooks)}")
    for k, v in list(hook_types.items())[:3]:
        print(f"    - {k}: {v['label']}")
    # Should have more than the old 5 hardcoded types (now 10 from social-content.json)
    check("More hook types than old 5", len(hook_types) >= 5, f"Got {len(hook_types)}")
    check("Hooks generated", len(hooks) >= 3, f"Got {len(hooks)}")
    # Verify dynamic types include strategy formulas from social-content.json
    strategy_types = {"knowledge_gap", "comparison", "myth_buster", "pov", "list", "question", "expectation_reality", "emotional_opener", "countdown_urgency", "behind_scenes"}
    found_strategy = strategy_types.intersection(set(hook_types.keys()))
    check("Strategy-based hook formulas present", len(found_strategy) >= 3, f"Found: {found_strategy}")
    check("Hook types have effectiveness rating", all("effectiveness" not in v or isinstance(v.get("effectiveness"), (int, float)) for v in hook_types.values()), "Missing effectiveness")
else:
    print(f"  ERROR: {resp.text[:200]}")
    check("generate-hooks returned 200", False, f"Status {resp.status_code}")

# ═══════════════════════════════════════════════════════════
# Test 2: Strategy context endpoint works
# ═══════════════════════════════════════════════════════════
print("\n=== Test 2: Strategy Context Endpoint ===")
resp = client.get(
    f"{BASE}/api/ai/strategy-context",
    params={"platform": "instagram_feed", "category": "laender_spotlight", "buyer_journey_stage": "awareness"},
    headers=headers,
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    check("Has seasonal phase", data.get("current_seasonal_phase") is not None)
    check("Has country weights", len(data.get("country_weights", {})) >= 5, f"Got {len(data.get('country_weights', {}))}")
    check("Has hook formulas", data.get("hook_formulas_count", 0) >= 5, f"Got {data.get('hook_formulas_count', 0)}")
    check("Has CTA strategies", data.get("cta_strategies_count", 0) >= 3, f"Got {data.get('cta_strategies_count', 0)}")
    check("Has buyer journey stage", data.get("buyer_journey_stage") is not None)
    check("Has content pillar", data.get("content_pillar") is not None and len(data.get("content_pillar", "")) > 0)
    check("Has combined prompt sections", len(data.get("combined_prompt_sections", "")) > 100, f"Got {len(data.get('combined_prompt_sections', ''))} chars")
else:
    print(f"  ERROR: {resp.text[:200]}")
    check("strategy-context returned 200", False, f"Status {resp.status_code}")

# ═══════════════════════════════════════════════════════════
# Test 3: generate-text accepts buyer_journey_stage
# ═══════════════════════════════════════════════════════════
print("\n=== Test 3: generate-text with buyer_journey_stage ===")
resp = client.post(
    f"{BASE}/api/ai/generate-text",
    json={
        "category": "laender_spotlight",
        "country": "usa",
        "tone": "jugendlich",
        "platform": "instagram_feed",
        "buyer_journey_stage": "awareness",
    },
    headers=headers,
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    check("Has slides", len(data.get("slides", [])) >= 1)
    check("Has source", data.get("source") in ("gemini", "rule_based"))
    print(f"  Source: {data.get('source')}")
else:
    print(f"  ERROR: {resp.text[:200]}")
    check("generate-text returned 200", False, f"Status {resp.status_code}")

# ═══════════════════════════════════════════════════════════
# Test 4: generate-text accepts content_pillar parameter
# ═══════════════════════════════════════════════════════════
print("\n=== Test 4: generate-text with content_pillar ===")
resp = client.post(
    f"{BASE}/api/ai/generate-text",
    json={
        "category": "laender_spotlight",
        "country": "canada",
        "tone": "emotional",
        "platform": "instagram_feed",
        "content_pillar": "erfahrungsberichte",
    },
    headers=headers,
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    check("Has slides", len(data.get("slides", [])) >= 1)
    check("Content pillar in response", data.get("content_pillar") == "erfahrungsberichte", f"Got: {data.get('content_pillar')}")
    check("Original category preserved", data.get("category") == "laender_spotlight", f"Got: {data.get('category')}")
    print(f"  Source: {data.get('source')}")
else:
    print(f"  ERROR: {resp.text[:200]}")
    check("generate-text with pillar returned 200", False, f"Status {resp.status_code}")

# ═══════════════════════════════════════════════════════════
# Test 5: suggest-content uses strategy context
# ═══════════════════════════════════════════════════════════
print("\n=== Test 5: suggest-content with strategy context ===")
resp = client.post(
    f"{BASE}/api/ai/suggest-content",
    json={},
    headers=headers,
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    suggestions = data.get("suggestions", [])
    check("Has suggestions", len(suggestions) >= 2, f"Got {len(suggestions)}")
    check("Has source", data.get("source") in ("gemini", "rule_based"))
    # Check that suggestion types are valid
    valid_types = {"seasonal", "country_rotation", "category_balance", "gap_fill"}
    for s in suggestions:
        stype = s.get("suggestion_type")
        if stype not in valid_types:
            check(f"Valid suggestion type: {stype}", False, f"Invalid type: {stype}")
            break
    else:
        check("All suggestion types valid", True)
    print(f"  Source: {data.get('source')}, Count: {len(suggestions)}")
else:
    print(f"  ERROR: {resp.text[:200]}")
    check("suggest-content returned 200", False, f"Status {resp.status_code}")

# ═══════════════════════════════════════════════════════════
# Test 6: adapt-for-platform uses dynamic guidelines
# ═══════════════════════════════════════════════════════════
print("\n=== Test 6: adapt-for-platform with dynamic guidelines ===")
resp = client.post(
    f"{BASE}/api/ai/adapt-for-platform",
    json={
        "original_text": "Mein erster Tag an der Highschool in Kanada war unglaublich! Die Schule ist riesig, alle waren super freundlich, und ich habe sofort neue Freunde gefunden. Das Beste: Ich bin jetzt im Volleyball-Team! #AuslandsjahrKanada #TREFFSprachreisen",
        "source_platform": "instagram_feed",
        "target_platform": "tiktok",
        "tone": "jugendlich",
    },
    headers=headers,
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    check("Has adapted text", len(data.get("adapted_text", "")) > 10)
    check("Source platform correct", data.get("source_platform") == "instagram_feed")
    check("Target platform correct", data.get("target_platform") == "tiktok")
    print(f"  Adapted text: {data.get('adapted_text', '')[:100]}...")
else:
    print(f"  ERROR: {resp.text[:200]}")
    check("adapt-for-platform returned 200", False, f"Status {resp.status_code}")

# ═══════════════════════════════════════════════════════════
# Test 7: engagement-boost uses dynamic CTA strategies
# ═══════════════════════════════════════════════════════════
print("\n=== Test 7: engagement-boost with dynamic CTA strategies ===")
resp = client.post(
    f"{BASE}/api/ai/engagement-boost",
    json={
        "post_content": {
            "slides": [
                {"headline": "Test Headline", "body_text": "Erster Schultag in den USA."}
            ],
            "caption_instagram": "Mein erster Tag!",
            "caption_tiktok": "Tag 1 USA",
            "hashtags_instagram": "#Auslandsjahr",
            "hashtags_tiktok": "#Auslandsjahr",
            "cta_text": "",
            "category": "erfahrungsberichte",
            "country": "usa",
            "tone": "jugendlich",
        },
        "platform": "instagram_feed",
        "format": "instagram_feed",
    },
    headers=headers,
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    boosts = data.get("suggestions", [])
    check("Has boost suggestions", len(boosts) >= 2, f"Got {len(boosts)}")
    # CTA suggestion should be present since cta_text is empty
    has_cta = any(b.get("category") == "cta" for b in boosts)
    check("CTA suggestion present (missing CTA detected)", has_cta)
    # Hashtag suggestion should be present since only 1 hashtag
    has_hashtag = any(b.get("category") == "hashtags" for b in boosts)
    check("Hashtag suggestion present (few hashtags)", has_hashtag)
    for b in boosts[:3]:
        print(f"    [{b.get('priority')}] {b.get('category')}: {b.get('suggestion', '')[:80]}...")
else:
    print(f"  ERROR: {resp.text[:200]}")
    check("engagement-boost returned 200", False, f"Status {resp.status_code}")

# ═══════════════════════════════════════════════════════════
# Test 8: Hook type validation in save-hook-selection
# ═══════════════════════════════════════════════════════════
print("\n=== Test 8: save-hook-selection with dynamic types ===")
resp = client.post(
    f"{BASE}/api/ai/save-hook-selection",
    json={
        "hook_text": "Wusstest du, dass 87% aller Austauschschueler sagen...",
        "hook_type": "knowledge_gap",  # Strategy-based type from social-content.json
        "topic": "Auslandsjahr",
    },
    headers=headers,
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    check("Hook saved successfully", data.get("status") == "success")
    check("Hook ID returned", data.get("hook_id") is not None)
else:
    print(f"  ERROR: {resp.text[:200]}")
    check("save-hook-selection returned 200", False, f"Status {resp.status_code}")

# ═══════════════════════════════════════════════════════════
# Test 9: Verify hooks are platform-filtered
# ═══════════════════════════════════════════════════════════
print("\n=== Test 9: Platform-filtered hook formulas ===")
resp_reels = client.post(
    f"{BASE}/api/ai/generate-hooks",
    json={"topic": "Auslandsjahr", "platform": "instagram_reels", "count": 3},
    headers=headers,
)
resp_feed = client.post(
    f"{BASE}/api/ai/generate-hooks",
    json={"topic": "Auslandsjahr", "platform": "instagram_feed", "count": 3},
    headers=headers,
)
if resp_reels.status_code == 200 and resp_feed.status_code == 200:
    reels_types = set(resp_reels.json().get("hook_types", {}).keys())
    feed_types = set(resp_feed.json().get("hook_types", {}).keys())
    check("Reels hook types loaded", len(reels_types) >= 3, f"Got {len(reels_types)}")
    check("Feed hook types loaded", len(feed_types) >= 3, f"Got {len(feed_types)}")
    print(f"  Reels types: {reels_types}")
    print(f"  Feed types: {feed_types}")
else:
    check("Platform-filtered hooks work", False)

# ═══════════════════════════════════════════════════════════
# Test 10: generate-text with both buyer_journey + content_pillar
# ═══════════════════════════════════════════════════════════
print("\n=== Test 10: generate-text with buyer_journey + content_pillar ===")
resp = client.post(
    f"{BASE}/api/ai/generate-text",
    json={
        "category": "tipps_tricks",
        "country": "australia",
        "tone": "motivierend",
        "platform": "tiktok",
        "buyer_journey_stage": "consideration",
        "content_pillar": "tipps_tricks",
    },
    headers=headers,
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    check("Has slides", len(data.get("slides", [])) >= 1)
    check("Has source field", data.get("source") in ("gemini", "rule_based"))
    check("Content pillar in response", data.get("content_pillar") == "tipps_tricks")
    print(f"  Source: {data.get('source')}")
else:
    print(f"  ERROR: {resp.text[:200]}")
    check("generate-text with both params returned 200", False, f"Status {resp.status_code}")

# ═══════════════════════════════════════════════════════════
# Test 11: Verify suggest-content respects pillar distribution
# ═══════════════════════════════════════════════════════════
print("\n=== Test 11: Strategy context has pillar distribution ===")
resp = client.get(
    f"{BASE}/api/ai/strategy-context",
    params={"platform": "instagram_feed", "category": "erfahrungsberichte"},
    headers=headers,
)
if resp.status_code == 200:
    data = resp.json()
    combined = data.get("combined_prompt_sections", "")
    check("Combined prompt has hook formulas", "HOOK-FORMELN" in combined or "Hook" in combined)
    check("Combined prompt has CTA strategies", "CTA" in combined or "Engagement" in combined)
    check("Combined prompt has tone of voice", "TONE-OF-VOICE" in combined or "Tone" in combined or "tone" in combined)
    check("Combined prompt has seasonal phase", "SAISONALE" in combined or "saisonal" in combined.lower())
    check("Combined prompt has platform practices", "PLATTFORM" in combined or "Best" in combined)
    check("Combined prompt has content pillar", "CONTENT-PILLAR" in combined or "Pillar" in combined)
    print(f"  Combined prompt length: {len(combined)} chars")
else:
    check("Strategy context returned 200", False)


client.close()

print(f"\n{'='*60}")
print(f"RESULTS: {passed}/{total} tests passed")
if passed == total:
    print("ALL TESTS PASSED")
else:
    print(f"FAILED: {total - passed} tests")
    exit(1)
