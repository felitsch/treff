"""Test the video scripts API endpoints."""
import httpx
import json
from collections import Counter

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

# Test 1: Get timing templates
print("\n=== Test 1: Timing Templates ===")
resp = client.get(f"{BASE}/api/video-scripts/timing-templates", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    templates = data.get("templates", {})
    for dur, tmpl in templates.items():
        print(f"  {dur}s: {tmpl['label']} ({tmpl['scene_count']} scenes)")
    assert len(templates) == 4, f"Expected 4 timing templates, got {len(templates)}"
else:
    print(f"Error: {resp.text}")
    exit(1)

# Test 2: Get hook formulas
print("\n=== Test 2: Hook Formulas ===")
resp = client.get(f"{BASE}/api/video-scripts/hook-formulas", params={"platform": "instagram_reels"}, headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"  Formulas count: {data.get('count')}")
    for f in data.get("formulas", [])[:3]:
        print(f"    - {f.get('name')} (eff: {f.get('effectiveness')})")
    assert data.get("count", 0) >= 5, "Expected at least 5 hook formulas"
else:
    print(f"Error: {resp.text}")
    exit(1)

# Test 3: Generate a video script (rule-based, no Gemini key)
print("\n=== Test 3: Generate Video Script (30s Reel) ===")
resp = client.post(
    f"{BASE}/api/video-scripts/generate",
    json={
        "topic": "Mein erster Schultag in den USA",
        "platform": "reels",
        "duration": 30,
        "country": "usa",
        "buyer_journey_stage": "awareness",
        "tone": "emotional",
    },
    headers=headers,
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"  Title: {data.get('title')}")
    print(f"  Platform: {data.get('platform')}")
    print(f"  Duration: {data.get('duration_seconds')}s")
    print(f"  Source: {data.get('source')}")
    print(f"  Scenes: {len(data.get('scenes', []))}")
    print(f"  Hook formula: {data.get('hook_formula')}")
    print(f"  CTA type: {data.get('cta_type')}")
    print(f"  Script ID: {data.get('id')}")
    scenes = data.get("scenes", [])
    assert len(scenes) == 5, f"Expected 5 scenes for 30s, got {len(scenes)}"
    # Verify timing
    last_end = scenes[-1].get("end_time", 0)
    assert last_end == 30, f"Expected total duration 30s, got {last_end}"
    # Check scene types
    scene_types = [s.get("scene_type") for s in scenes]
    assert scene_types[0] == "hook", f"First scene should be hook, got {scene_types[0]}"
    assert scene_types[-1] == "cta", f"Last scene should be cta, got {scene_types[-1]}"
    print(f"  Scene types: {scene_types}")
    print(f"  PASS: Timing and structure correct")
    script_id = data.get("id")
else:
    print(f"Error: {resp.text}")
    exit(1)

# Test 4: Generate a 60s TikTok script
print("\n=== Test 4: Generate 60s TikTok Script ===")
resp = client.post(
    f"{BASE}/api/video-scripts/generate",
    json={
        "topic": "5 Dinge die NIEMAND ueber Australien sagt",
        "platform": "tiktok",
        "duration": 60,
        "country": "australia",
        "hook_formula_id": "list",
        "buyer_journey_stage": "consideration",
    },
    headers=headers,
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"  Title: {data.get('title')}")
    print(f"  Scenes: {len(data.get('scenes', []))}")
    assert data.get("hook_formula") == "list", f"Expected hook formula 'list', got {data.get('hook_formula')}"
    print(f"  PASS: 60s script with 'list' hook formula")
else:
    print(f"Error: {resp.text}")
    exit(1)

# Test 5: List scripts
print("\n=== Test 5: List Video Scripts ===")
resp = client.get(f"{BASE}/api/video-scripts", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"  Scripts count: {data.get('count')}")
    assert data.get("count", 0) >= 2, "Expected at least 2 scripts"
else:
    print(f"Error: {resp.text}")
    exit(1)

# Test 6: Get single script
print("\n=== Test 6: Get Single Script ===")
resp = client.get(f"{BASE}/api/video-scripts/{script_id}", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    assert data.get("id") == script_id
    print(f"  PASS: Retrieved script {script_id}")
else:
    print(f"Error: {resp.text}")
    exit(1)

# Test 7: Update script
print("\n=== Test 7: Update Script ===")
resp = client.put(
    f"{BASE}/api/video-scripts/{script_id}",
    json={"title": "Updated: Mein erster Schultag"},
    headers=headers,
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    assert data.get("title") == "Updated: Mein erster Schultag"
    print(f"  PASS: Title updated")
else:
    print(f"Error: {resp.text}")
    exit(1)

# Test 8: Generate 15s and 90s scripts
print("\n=== Test 8: Generate 15s and 90s Scripts ===")
for dur in [15, 90]:
    resp = client.post(
        f"{BASE}/api/video-scripts/generate",
        json={
            "topic": f"Test {dur}s Script",
            "platform": "reels" if dur == 15 else "tiktok",
            "duration": dur,
        },
        headers=headers,
    )
    if resp.status_code == 200:
        data = resp.json()
        scenes = data.get("scenes", [])
        last_end = scenes[-1].get("end_time", 0)
        assert last_end == dur, f"Expected {dur}s total, got {last_end}"
        print(f"  {dur}s: {len(scenes)} scenes, timing correct")
    else:
        print(f"  {dur}s: ERROR {resp.status_code}")
        exit(1)
print(f"  PASS: All timing templates work")

# Test 9: Delete script
print("\n=== Test 9: Delete Script ===")
resp = client.delete(f"{BASE}/api/video-scripts/{script_id}", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    assert data.get("success") is True
    print(f"  PASS: Script deleted")
    # Verify it's gone
    resp = client.get(f"{BASE}/api/video-scripts/{script_id}", headers=headers)
    assert resp.status_code == 404, "Expected 404 after deletion"
    print(f"  PASS: Confirmed deleted (404)")
else:
    print(f"Error: {resp.text}")
    exit(1)

# Test 10: Invalid duration
print("\n=== Test 10: Invalid Duration ===")
resp = client.post(
    f"{BASE}/api/video-scripts/generate",
    json={"topic": "Test", "duration": 45},
    headers=headers,
)
assert resp.status_code == 400, f"Expected 400 for invalid duration, got {resp.status_code}"
print(f"  PASS: Invalid duration rejected (400)")

client.close()
print("\n=== ALL 10 TESTS PASSED ===")
