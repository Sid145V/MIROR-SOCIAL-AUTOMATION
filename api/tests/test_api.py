"""
Comprehensive Automated Test Suite for MIROR T01 Renderer FastAPI Application
Tests all 14 mandatory API test points including Text Lock enforcement, variant rules, and image output assertions.
"""

import os
import sys
import json
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api.main import app

client = TestClient(app)

def run_api_tests():
    print("=== STARTING MIROR T01 RENDERER API AUTOMATED TEST SUITE ===\n")
    
    passed_count = 0
    failed_count = 0

    def log_test(num, name, passed, details=""):
        nonlocal passed_count, failed_count
        status_str = "PASSED" if passed else "FAILED"
        if passed:
            passed_count += 1
        else:
            failed_count += 1
        print(f"[{status_str}] Test #{num:02d} - {name}: {details}")

    # 1-2. GET /health
    res_health = client.get("/health")
    log_test(1, "GET /health Endpoint Status 200", res_health.status_code == 200, f"HTTP {res_health.status_code}")
    
    health_data = res_health.json()
    log_test(2, "GET /health Response Schema", health_data.get("status") == "ok" and health_data.get("service") == "miror-renderer", f"Response: {health_data}")

    # Load master valid content payload
    master_json_path = REPO_ROOT / "template-engine" / "tests" / "test_content_MIROR-T01-MASTER.json"
    with open(master_json_path, "r", encoding="utf-8") as f:
        master_payload = json.load(f)

    # 3-4. POST /render Valid Master Payload
    res_render = client.post("/render", json=master_payload)
    log_test(3, "POST /render Master Payload Status 200", res_render.status_code == 200, f"HTTP {res_render.status_code}")

    render_data = res_render.json()
    log_test(4, "POST /render Response success=True", render_data.get("success") is True, f"post_id={render_data.get('post_id')}")

    # 5-8. Output files existence, format, resolution (1080x1350), and slide keys
    slides = render_data.get("slides", [])
    log_test(5, "Response Contains 3 Slides (S01, S02, S03)", len(slides) == 3 and [s["slide"] for s in slides] == ["S01", "S02", "S03"], f"Slide keys: {[s['slide'] for s in slides]}")

    files_exist = True
    valid_format = True
    valid_dims = True

    for s in slides:
        file_rel = s["file"]
        abs_p = REPO_ROOT / file_rel
        if not abs_p.exists():
            files_exist = False
            print(f"  -> File missing: {abs_p}")
        else:
            with Image.open(abs_p) as img:
                if img.format != "PNG":
                    valid_format = False
                if img.size != (1080, 1350):
                    valid_dims = False

    log_test(6, "3 Output PNG Files Created on Disk", files_exist, "All 3 files exist in output/renders/")
    log_test(7, "Output Files Image Format = PNG", valid_format, "100% PNG image format")
    log_test(8, "Output Files Resolution = 1080x1350", valid_dims, "Exact 1080x1350 canvas resolution")

    # 9-10. Mutated Text Payload Rejection (Exact Text Lock)
    mutated_payload = json.loads(json.dumps(master_payload))
    mutated_payload["slides"][0]["headline"]["text"] = "YOU ARE TIRED."  # Mutated from "YOU'RE TIRED."
    
    res_mutated = client.post("/render", json=mutated_payload)
    log_test(9, "Mutated Text Payload Rejected Status 400", res_mutated.status_code == 400, f"HTTP {res_mutated.status_code}")
    
    mutated_err = res_mutated.json().get("error", {})
    log_test(10, "Text Lock Failure Error Code", mutated_err.get("code") == "TEXT_LOCK_FAILURE", f"Code: {mutated_err.get('code')}, Message: {mutated_err.get('message')}")

    # 11-12. Invalid Background Variant Rejection
    invalid_bg_payload = json.loads(json.dumps(master_payload))
    invalid_bg_payload["backgroundVariant"] = "99"
    
    res_bg = client.post("/render", json=invalid_bg_payload)
    log_test(11, "Invalid Background Variant Rejected Status 400", res_bg.status_code == 400, f"HTTP {res_bg.status_code}")
    
    bg_err = res_bg.json().get("error", {})
    log_test(12, "Background Variant Error Code", bg_err.get("code") == "BACKGROUND_VARIANT_ERROR", f"Code: {bg_err.get('code')}")

    # 13-14. Unsupported Template Rejection (T02)
    t02_payload = json.loads(json.dumps(master_payload))
    t02_payload["template"] = "T02"
    
    res_t02 = client.post("/render", json=t02_payload)
    log_test(13, "Unsupported Template T02 Rejected Status 400", res_t02.status_code == 400, f"HTTP {res_t02.status_code}")
    
    t02_err = res_t02.json().get("error", {})
    log_test(14, "Unsupported Template Error Code", t02_err.get("code") == "UNSUPPORTED_TEMPLATE", f"Code: {t02_err.get('code')}")

    print(f"\n=== API QA SUMMARY: {passed_count}/{passed_count + failed_count} TESTS PASSED ===")
    return failed_count == 0

if __name__ == "__main__":
    success = run_api_tests()
    sys.exit(0 if success else 1)
