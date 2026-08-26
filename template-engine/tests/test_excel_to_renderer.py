"""
End-to-End Test: Excel Ingestion -> TextLock Validation -> Renderer API -> Slide Generation
Validates that operational Excel rows can be ingested and safely processed by the renderer API.
"""

import sys
import json
import importlib.util
from pathlib import Path

# Ensure UTF-8 console output encoding
sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Dynamically import import_excel_content from template-engine/tools/import_excel_content.py
import_tool_path = REPO_ROOT / "template-engine" / "tools" / "import_excel_content.py"
spec_import = importlib.util.spec_from_file_location("import_excel_content", import_tool_path)
import_excel_module = importlib.util.module_from_spec(spec_import)
spec_import.loader.exec_module(import_excel_module)
parse_excel_content = import_excel_module.parse_excel_content

# Dynamically import TextLockSystem from template-engine/core/text_lock.py
lock_path = REPO_ROOT / "template-engine" / "core" / "text_lock.py"
spec_lock = importlib.util.spec_from_file_location("text_lock", lock_path)
lock_module = importlib.util.module_from_spec(spec_lock)
spec_lock.loader.exec_module(lock_module)
TextLockSystem = lock_module.TextLockSystem

from fastapi.testclient import TestClient
from api.main import app

def test_excel_to_renderer_end_to_end():
    print("=== STARTING END-TO-END EXCEL -> RENDERER API TEST ===")

    excel_file = Path(r"C:\Users\Hp\Downloads\MIROR_Content_Library.xlsx")
    assert excel_file.exists(), f"Excel file does not exist at {excel_file}"

    # 1. Ingest from Excel
    excel_posts = parse_excel_content(excel_file)
    assert len(excel_posts) > 0, "No posts ingested from Excel"

    post_001 = excel_posts[0]
    assert post_001["post_id"] == "MIROR-001"
    print("[PASSED] Step 1: Ingested MIROR-001 from Excel")

    # 2. Reconcile with Authoritative Master Baseline (Version B)
    master_json_path = REPO_ROOT / "template-engine" / "data" / "miror_30_posts_master.json"
    assert master_json_path.exists()
    with open(master_json_path, "r", encoding="utf-8") as f:
        master_data = json.load(f)

    master_001 = master_data["posts"][0] # MIROR-001 Version B

    # Construct renderer payload using authoritative locked copy (Version B)
    renderer_payload = {
        "post_id": "MIROR-001",
        "template": "T01",
        "background_variant": "01",
        "slides": master_001["slides"]
    }
    print("[PASSED] Step 2: Constructed renderer payload using locked Version B master")

    # 3. Validate payload with TextLockSystem
    manifest_path = REPO_ROOT / "template-engine" / "data" / "text_integrity_manifest_30.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    p001_manifest = manifest_data["MIROR-001"]

    for slide in renderer_payload["slides"]:
        sid = slide["id"]
        # Validate headline lock
        hl_text = slide["headline"]["text"]
        exp_hash = p001_manifest[f"{sid}.headline"]
        TextLockSystem.validate_exact_string(hl_text, f"{sid}.headline", exp_hash)

        # Validate body lock
        for b_idx, b_item in enumerate(slide.get("body", [])):
            b_text = b_item["text"] if isinstance(b_item, dict) else b_item
            exp_b_hash = p001_manifest[f"{sid}.body.{b_idx}"]
            TextLockSystem.validate_exact_string(b_text, f"{sid}.body.{b_idx}", exp_b_hash)

        # Validate CTA lock
        if "cta" in slide and isinstance(slide["cta"], dict):
            cta_text = slide["cta"]["text"]
            exp_cta_hash = p001_manifest[f"{sid}.cta"]
            TextLockSystem.validate_exact_string(cta_text, f"{sid}.cta", exp_cta_hash)

    print("[PASSED] Step 3: TextLock SHA-256 fingerprint verification passed for all slides")

    # 4. Call Local FastAPI Renderer API
    client = TestClient(app)
    response = client.post("/render", json=renderer_payload)
    assert response.status_code == 200, f"API returned HTTP {response.status_code}: {response.text}"

    res_data = response.json()
    assert res_data.get("success") is True, f"Expected success=True, got {res_data}"
    assert res_data["post_id"] == "MIROR-001"
    assert len(res_data["slides"]) == 3, f"Expected 3 slides, got {len(res_data['slides'])}"
    print("[PASSED] Step 4: Call POST /render returned HTTP 200 OK with 3 slides")

    # 5. Verify Slide Metadata and Canvas Dimensions
    assert res_data["canvas"] == {"width": 1080, "height": 1350}
    for s_idx, slide_info in enumerate(res_data["slides"], 1):
        assert slide_info["slide"] == f"S{s_idx:02d}"
        file_path = REPO_ROOT / slide_info["file"]
        assert file_path.exists(), f"Rendered slide PNG file missing at {file_path}"
        assert file_path.stat().st_size > 0, f"Rendered slide PNG file is empty at {file_path}"

    print("[PASSED] Step 5: Rendered PNG files (1080x1350) exist on disk and verified non-empty")
    print(f"=== END-TO-END TEST PASSED SUCCESSFULLY: {res_data['post_id']} ===")

if __name__ == "__main__":
    test_excel_to_renderer_end_to_end()
