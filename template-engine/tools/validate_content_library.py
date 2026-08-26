"""
Deterministic Validator for MIROR 30-Post Content Library & SHA-256 Manifest
Verifies 100% exact text preservation, zero mutation, structural integrity, and Unicode preservation.
"""

import sys
import json
import hashlib
from pathlib import Path

# Ensure UTF-8 console output encoding
sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "template-engine" / "data"
MASTER_JSON_PATH = DATA_DIR / "miror_30_posts_master.json"
MANIFEST_JSON_PATH = DATA_DIR / "text_integrity_manifest_30.json"

def compute_sha256(text_str: str) -> str:
    if not isinstance(text_str, str):
        raise ValueError(f"Expected string for SHA-256 calculation, got {type(text_str).__name__}")
    return hashlib.sha256(text_str.encode("utf-8")).hexdigest()

def validate_content_library():
    print("=== STARTING DETERMINISTIC 30-POST CONTENT LIBRARY VALIDATION ===\n")
    
    passed_checks = 0
    failed_checks = 0

    def log_check(num, name, condition, details=""):
        nonlocal passed_checks, failed_checks
        status_str = "PASSED" if condition else "FAILED"
        if condition:
            passed_checks += 1
        else:
            failed_checks += 1
        print(f"[{status_str}] Check #{num:02d} - {name}: {details}")
        if not condition:
            raise ValueError(f"DETERMINISTIC VALIDATION FAILURE at Check #{num}: {name} - {details}")

    # 1. Master JSON File Exists
    log_check(1, "Master JSON File Exists", MASTER_JSON_PATH.exists(), str(MASTER_JSON_PATH))
    with open(MASTER_JSON_PATH, "r", encoding="utf-8") as f:
        master_data = json.load(f)

    # 2. Manifest JSON File Exists
    log_check(2, "Manifest JSON File Exists", MANIFEST_JSON_PATH.exists(), str(MANIFEST_JSON_PATH))
    with open(MANIFEST_JSON_PATH, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    posts = master_data.get("posts", [])
    
    # 3. Exactly 30 Posts Count
    log_check(3, "Exactly 30 Posts Count", len(posts) == 30, f"Found {len(posts)} posts")

    # 4. Sequential Post IDs MIROR-001 to MIROR-030 & No Duplicates
    post_ids = [p.get("content_id") for p in posts]
    expected_ids = [f"MIROR-{i:03d}" for i in range(1, 31)]
    log_check(4, "Sequential Post IDs MIROR-001 to MIROR-030", post_ids == expected_ids, f"Post IDs match exact sequence")
    log_check(5, "No Duplicate Post IDs", len(set(post_ids)) == 30, "30 unique post IDs")

    unicode_symbols_found = {"☐": 0, "→": 0, "—": 0, "“": 0, "”": 0, "'": 0}
    newlines_found = 0

    # Validate Each Post
    for idx, post in enumerate(posts, 1):
        pid = post.get("content_id")
        p_manifest = manifest_data.get(pid, {})
        slides = post.get("slides", [])

        # Slide ID Check
        slide_ids = [s.get("id") for s in slides]
        log_check(6, f"[{pid}] Slide Structure (S01, S02, S03)", slide_ids == ["S01", "S02", "S03"], f"Slide IDs: {slide_ids}")

        # S01 Validation
        s01 = slides[0]
        s01_hl = s01.get("headline", {}).get("text")
        log_check(7, f"[{pid}] S01 Headline Non-Empty String", isinstance(s01_hl, str) and len(s01_hl) > 0, f"S01 Headline len={len(s01_hl) if s01_hl else 0}")
        s01_hash = compute_sha256(s01_hl)
        log_check(8, f"[{pid}] S01 Headline SHA-256 Match", s01_hash == p_manifest.get("S01.headline"), f"Hash: {s01_hash[:12]}...")

        # S02 Validation
        s02 = slides[1]
        s02_hl = s02.get("headline", {}).get("text")
        log_check(9, f"[{pid}] S02 Headline Non-Empty String", isinstance(s02_hl, str) and len(s02_hl) > 0, f"S02 Headline len={len(s02_hl) if s02_hl else 0}")
        s02_hash = compute_sha256(s02_hl)
        log_check(10, f"[{pid}] S02 Headline SHA-256 Match", s02_hash == p_manifest.get("S02.headline"), f"Hash: {s02_hash[:12]}...")

        s02_body = s02.get("body", [])
        for b_idx, b_item in enumerate(s02_body):
            b_txt = b_item.get("text")
            log_check(11, f"[{pid}] S02 Body[{b_idx}] Non-Empty String", isinstance(b_txt, str) and len(b_txt) > 0, f"Body len={len(b_txt) if b_txt else 0}")
            b_hash = compute_sha256(b_txt)
            log_check(12, f"[{pid}] S02 Body[{b_idx}] SHA-256 Match", b_hash == p_manifest.get(f"S02.body.{b_idx}"), f"Hash: {b_hash[:12]}...")

        # S03 Validation
        s03 = slides[2]
        s03_hl = s03.get("headline", {}).get("text")
        log_check(13, f"[{pid}] S03 Headline Non-Empty String", isinstance(s03_hl, str) and len(s03_hl) > 0, f"S03 Headline len={len(s03_hl) if s03_hl else 0}")
        s03_hash = compute_sha256(s03_hl)
        log_check(14, f"[{pid}] S03 Headline SHA-256 Match", s03_hash == p_manifest.get("S03.headline"), f"Hash: {s03_hash[:12]}...")

        s03_body = s03.get("body", [])
        for b_idx, b_item in enumerate(s03_body):
            b_txt = b_item.get("text")
            log_check(15, f"[{pid}] S03 Body[{b_idx}] Non-Empty String", isinstance(b_txt, str) and len(b_txt) > 0, f"Body len={len(b_txt) if b_txt else 0}")
            b_hash = compute_sha256(b_txt)
            log_check(16, f"[{pid}] S03 Body[{b_idx}] SHA-256 Match", b_hash == p_manifest.get(f"S03.body.{b_idx}"), f"Hash: {b_hash[:12]}...")

        s03_cta = s03.get("cta", {}).get("text")
        log_check(17, f"[{pid}] S03 CTA Non-Empty String", isinstance(s03_cta, str) and len(s03_cta) > 0, f"CTA len={len(s03_cta) if s03_cta else 0}")
        cta_hash = compute_sha256(s03_cta)
        log_check(18, f"[{pid}] S03 CTA SHA-256 Match", cta_hash == p_manifest.get("S03.cta"), f"Hash: {cta_hash[:12]}...")

        # Count Unicode symbols and newlines
        full_post_str = json.dumps(post, ensure_ascii=False)
        for sym in unicode_symbols_found:
            unicode_symbols_found[sym] += full_post_str.count(sym)
        newlines_found += full_post_str.count("\\n")

    # Assert Unicode Symbol & Newline Preservation
    log_check(19, "Unicode Checkboxes Preserved (☐)", unicode_symbols_found["☐"] >= 6, f"Found {unicode_symbols_found['☐']} checkboxes in Post #20")
    log_check(20, "Unicode Arrows Preserved (→)", unicode_symbols_found["→"] >= 30, f"Found {unicode_symbols_found['→']} CTA arrows across posts")
    log_check(21, "Unicode Em Dashes Preserved (—)", unicode_symbols_found["—"] >= 3, f"Found {unicode_symbols_found['—']} em dashes")
    log_check(22, "Unicode Smart Quotes Preserved (“ ”)", unicode_symbols_found["“"] >= 2 and unicode_symbols_found["”"] >= 2, f"Found {unicode_symbols_found['“']} smart quote pairs")
    log_check(23, "Newlines Preserved (\\n)", newlines_found >= 50, f"Found {newlines_found} structural line breaks")

    print(f"\n=== CONTENT LIBRARY QA SUMMARY: {passed_checks} CHECKS PASSED WITH 0 ERRORS ===")
    return True

if __name__ == "__main__":
    try:
        success = validate_content_library()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[DETERMINISTIC FAILURE] {str(e)}")
        sys.exit(1)
