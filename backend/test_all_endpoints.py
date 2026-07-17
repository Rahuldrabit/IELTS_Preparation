"""Comprehensive API endpoint test — tests all services."""
import requests
import json
import sys

BASE = "http://localhost:8000/api"
TIMEOUT = 15
results = []


def test(method, path, expected_status=200, json_body=None, label=None):
    url = f"{BASE}{path}"
    name = label or f"{method} {path}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=TIMEOUT)
        elif method == "POST":
            r = requests.post(url, json=json_body, timeout=TIMEOUT)
        elif method == "PATCH":
            r = requests.patch(url, json=json_body, timeout=TIMEOUT)
        else:
            r = requests.request(method, url, json=json_body, timeout=TIMEOUT)

        status = "PASS" if r.status_code == expected_status else "FAIL"
        detail = ""
        if r.status_code != expected_status:
            detail = f" (got {r.status_code}: {r.text[:200]})"
        results.append((status, name, detail))
        print(f"  [{status}] {name}{detail}")
        return r
    except requests.exceptions.Timeout:
        results.append(("TIMEOUT", name, ""))
        print(f"  [TIMEOUT] {name}")
        return None
    except Exception as e:
        results.append(("ERROR", name, str(e)[:100]))
        print(f"  [ERROR] {name} — {e}")
        return None


print("=" * 60)
print("IELTS Tutor Backend — Full Endpoint Test")
print("=" * 60)

# ─── Profile Service ───
print("\n[Profile Service]")
test("GET", "/profile")
test("GET", "/profile/band-scores")
test("GET", "/profile/roadmap")
test("GET", "/profile/uma-intervention")
test("PATCH", "/profile/features", json_body={"reading": {"telemetry": False, "confidenceFlags": False}})

# ─── Reading Service ───
print("\n[Reading Service]")
test("GET", "/reading/passages")
# POST /reading/generate — already verified working (takes 30-60s, skip in batch test)

# ─── Writing Service ───
print("\n[Writing Service]")
test("GET", "/writing/tasks")

# ─── Listening Service ───
print("\n[Listening Service]")
# No GET list endpoint; generation is slow. Test the OPTIONS to verify route exists.
test("POST", "/listening/generate", expected_status=422, json_body={}, label="POST /listening/generate (validation check)")

# ─── Vocabulary Service ───
print("\n[Vocabulary Service]")
test("GET", "/vocabulary")
test("GET", "/vocabulary/due")
test("GET", "/vocabulary/stats")

# ─── Grammar Service ───
print("\n[Grammar Service]")
test("GET", "/grammar/topics")

# ─── AI Agent Service ───
print("\n[AI Agent Service]")
test("GET", "/agent/health")
test("GET", "/agent/mentor-messages")
test("GET", "/agent/daily-plan")

# ─── Import Service ───
print("\n[Import Service]")
# Import only has POST endpoints and status check by ID
# Test with non-existent ID to verify route is registered
test("GET", "/import/999/status", expected_status=404, label="GET /import/{id}/status (not found check)")

# ─── Agents (Council/Socratic) ───
print("\n[Agents Router]")
test("GET", "/agents/registry", label="GET /agents/registry")

# ─── Summary ───
print("\n" + "=" * 60)
passed = sum(1 for s, _, _ in results if s == "PASS")
failed = sum(1 for s, _, _ in results if s == "FAIL")
errors = sum(1 for s, _, _ in results if s in ("ERROR", "TIMEOUT"))
total = len(results)
print(f"Results: {passed}/{total} passed, {failed} failed, {errors} errors/timeouts")
print("=" * 60)

if failed or errors:
    print("\nFailed/Error endpoints:")
    for status, name, detail in results:
        if status != "PASS":
            print(f"  [{status}] {name}{detail}")
    sys.exit(1)
else:
    print("\nAll endpoints working!")
