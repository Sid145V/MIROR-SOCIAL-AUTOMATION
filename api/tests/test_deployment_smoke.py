"""
Production Deployment Smoke Test Suite
Executes local API health, render, negative security, and 5-request reliability tests.
"""

import os
import sys
import json
import time
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure UTF-8 console output encoding
sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api.main import app

def run_deployment_smoke_tests():
    print("=== STARTING PRODUCTION DEPLOYMENT SMOKE TESTS ===")
    client = TestClient(app)

    # 1. Health Check Test
    res_health = client.get("/health")
    assert res_health.status_code == 200, f"Health endpoint returned HTTP {res_health.status_code}"
    health_data = res_health.json()
    assert health_data["status"] == "ok"
    assert health_data["service"] == "miror-renderer"
    print("[PASSED] Health Check (GET /health): HTTP 200 OK")

    # Load master payload for MIROR-001 Version B
    master_json_path = REPO_ROOT / "template-engine" / "data" / "miror_30_posts_master.json"
    with open(master_json_path, "r", encoding="utf-8") as f:
        master_data = json.load(f)

    post_001_master = master_data["posts"][0]

    valid_payload = {
        "post_id": "MIROR-001",
        "template": "T01",
        "backgroundVariant": "01",
        "slides": post_001_master["slides"]
    }

    # 2. Public Render Test (MIROR-001)
    res_render = client.post("/render", json=valid_payload)
    assert res_render.status_code == 200, f"Render API returned HTTP {res_render.status_code}: {res_render.text}"
    render_data = res_render.json()
    assert render_data["success"] is True
    assert render_data["post_id"] == "MIROR-001"
    assert len(render_data["slides"]) == 3
    assert render_data["canvas"] == {"width": 1080, "height": 1350}
    print("[PASSED] Render Endpoint (POST /render): HTTP 200 OK, 3 slides, 1080x1350 canvas")

    # 3. Negative Security Tests

    # 3.1 Mutated Headline
    mutated_payload = json.loads(json.dumps(valid_payload))
    mutated_payload["slides"][0]["headline"]["text"] = "MUTATED HEADLINE COPY"
    res_mutated = client.post("/render", json=mutated_payload)
    assert res_mutated.status_code == 400
    assert res_mutated.json()["error"]["code"] == "TEXT_LOCK_FAILURE"
    print("[PASSED] Negative Test #1: Mutated headline correctly rejected with TEXT_LOCK_FAILURE")

    # 3.2 Changed Punctuation
    punct_payload = json.loads(json.dumps(valid_payload))
    punct_payload["slides"][0]["headline"]["text"] = valid_payload["slides"][0]["headline"]["text"].replace(".", "!")
    res_punct = client.post("/render", json=punct_payload)
    assert res_punct.status_code == 400
    assert res_punct.json()["error"]["code"] == "TEXT_LOCK_FAILURE"
    print("[PASSED] Negative Test #2: Changed punctuation correctly rejected with TEXT_LOCK_FAILURE")

    # 3.3 Invalid Background Variant
    bad_bg_payload = json.loads(json.dumps(valid_payload))
    bad_bg_payload["backgroundVariant"] = "99"
    res_bad_bg = client.post("/render", json=bad_bg_payload)
    assert res_bad_bg.status_code == 400
    assert res_bad_bg.json()["error"]["code"] == "BACKGROUND_VARIANT_ERROR"
    print("[PASSED] Negative Test #3: Invalid background variant '99' correctly rejected with BACKGROUND_VARIANT_ERROR")

    # 3.4 Unsupported Template
    bad_tmpl_payload = json.loads(json.dumps(valid_payload))
    bad_tmpl_payload["template"] = "T99"
    res_bad_tmpl = client.post("/render", json=bad_tmpl_payload)
    assert res_bad_tmpl.status_code == 400
    assert res_bad_tmpl.json()["error"]["code"] == "UNSUPPORTED_TEMPLATE"
    print("[PASSED] Negative Test #4: Unsupported template 'T99' correctly rejected with UNSUPPORTED_TEMPLATE")

    # 4. Controlled 5-Request Sequential Reliability Check
    print("\n=== EXECUTING 5-REQUEST SEQUENTIAL RELIABILITY CHECK ===")
    times = []
    for i in range(1, 6):
        t0 = time.time()
        res_seq = client.post("/render", json=valid_payload)
        t1 = time.time()
        elapsed = t1 - t0
        times.append(elapsed)
        assert res_seq.status_code == 200, f"Request {i} failed with status {res_seq.status_code}"
        print(f"  Request #{i}: HTTP 200 OK | Render Time: {elapsed:.2f}s")

    avg_time = sum(times) / len(times)
    print(f"[PASSED] Reliability Check: 5/5 requests succeeded (Avg time: {avg_time:.2f}s)")
    print("\n=== ALL LOCAL SMOKE & SECURITY TESTS PASSED 100% ===")

if __name__ == "__main__":
    run_deployment_smoke_tests()
