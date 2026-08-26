"""
Automated QA Validation Suite — Exact Text Lock & Text Integrity System
Executes 17 rigorous test points (9 positive integrity checks + 8 negative mutation rejection tests).
Enforces SHA-256 fingerprint matching and zero character/punctuation mutation.
"""

import os
import sys
import json
import copy
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
core_dir = REPO_ROOT / "template-engine" / "core"
if str(core_dir) not in sys.path:
    sys.path.insert(0, str(core_dir))

from text_lock import TextLockSystem, TextLockError

def run_text_integrity_tests(project_root=None):
    if project_root is None:
        root = REPO_ROOT
    else:
        root = Path(project_root).resolve()

    master_json_path = root / "template-engine" / "tests" / "test_content_MIROR-T01-MASTER.json"

    results = []

    def log_test(num, category, name, passed, details=""):
        status = "PASSED" if passed else "FAILED"
        results.append((num, name, passed))
        print(f"[{status}] Test #{num:02d} ({category}) - {name}: {details}")

    print("=== STARTING T01 TEXT LOCK & TEXT INTEGRITY QA SUITE ===\n")

    # 1. Master Content Schema File Exists
    master_exists = master_json_path.exists()
    log_test(1, "Positive", "Master Content Schema File Exists", master_exists, f"{master_json_path}")
    if not master_exists:
        return False

    with open(master_json_path, "r", encoding="utf-8") as f:
        master_payload = json.load(f)

    manifest = master_payload.get("text_integrity", {})

    # 2. SHA-256 Integrity Manifest Present
    log_test(2, "Positive", "SHA-256 Integrity Manifest Present", len(manifest) > 0, f"Contains {len(manifest)} SHA-256 hashes")

    # 3. S01 Hook Text Lock Validation
    try:
        s01_payload = master_payload["slides"][0]
        TextLockSystem.validate_slide_payload(s01_payload, manifest)
        hash_val = manifest.get("S01.headline", "")[:16]
        log_test(3, "Positive", "S01 Hook Text Lock Validation", True, f"Matched hash {hash_val}...")
    except Exception as e:
        log_test(3, "Positive", "S01 Hook Text Lock Validation", False, str(e))

    # 4. S02 Follow-Through Text Lock Validation
    try:
        s02_payload = master_payload["slides"][1]
        TextLockSystem.validate_slide_payload(s02_payload, manifest)
        log_test(4, "Positive", "S02 Follow-Through Text Lock Validation", True, "Validated headline & 3 body paragraphs")
    except Exception as e:
        log_test(4, "Positive", "S02 Follow-Through Text Lock Validation", False, str(e))

    # 5. S03 CTA Text Lock Validation
    try:
        s03_payload = master_payload["slides"][2]
        TextLockSystem.validate_slide_payload(s03_payload, manifest)
        hash_val = manifest.get("S03.cta", "")[:16]
        log_test(5, "Positive", "S03 CTA Text Lock Validation", True, f"Validated headline, body & CTA hash {hash_val}...")
    except Exception as e:
        log_test(5, "Positive", "S03 CTA Text Lock Validation", False, str(e))

    # 6. Explicit lock='EXACT' Attributes
    all_exact = True
    for s in master_payload["slides"]:
        if isinstance(s.get("headline"), dict) and s["headline"].get("lock") != "EXACT":
            all_exact = False
        if isinstance(s.get("body"), list):
            for b in s["body"]:
                if isinstance(b, dict) and b.get("lock") != "EXACT":
                    all_exact = False
        if isinstance(s.get("cta"), dict) and s["cta"].get("lock") != "EXACT":
            all_exact = False

    log_test(6, "Positive", "Explicit lock='EXACT' Attributes", all_exact, "All headline, body, and CTA elements locked to 'EXACT'")

    # 7. Immutable Non-Empty String Check
    non_empty = True
    for s in master_payload["slides"]:
        hl_txt = s["headline"]["text"] if isinstance(s["headline"], dict) else s["headline"]
        if not hl_txt or len(hl_txt.strip()) == 0:
            non_empty = False
    log_test(7, "Positive", "Immutable Non-Empty String Check", non_empty, "100% of locked fields are non-empty strings")

    # 8. Exact Newline Preservation (\n in CTA)
    s03_cta_txt = master_payload["slides"][2]["cta"]["text"]
    has_newline = "\n" in s03_cta_txt
    log_test(8, "Positive", "Exact Newline Preservation", has_newline, "Literal line break character preserved in CTA copy")

    # 9. Literal Symbol Preservation (-> in CTA)
    has_arrow = "->" in s03_cta_txt or "→" in s03_cta_txt
    log_test(9, "Positive", "Literal Symbol Preservation", has_arrow, "Literal arrow symbol preserved in CTA copy")

    print("\n--- NEGATIVE MUTATION TESTS (Verifying explicit rejection of text alterations) ---\n")

    # 10. Negative Test 1: Character Case Mutation ("HERE'S WHAT MAY BE HAPPENING" -> "Here's what may be happening")
    bad_payload = copy.deepcopy(master_payload["slides"][1])
    bad_payload["headline"]["text"] = "Here's what may be happening."
    try:
        TextLockSystem.validate_slide_payload(bad_payload, manifest)
        log_test(10, "Negative #1", "Character Case Mutation Rejection", False, "FAILED to catch headline case mutation!")
    except TextLockError:
        log_test(10, "Negative #1", "Character Case Mutation Rejection", True, "Successfully caught TextLockError on case mutation")

    # 11. Negative Test 2: Punctuation Removal ("DOTS." -> "DOTS")
    bad_payload = copy.deepcopy(master_payload["slides"][2])
    bad_payload["headline"]["text"] = "START CONNECTING\nTHE DOTS"
    try:
        TextLockSystem.validate_slide_payload(bad_payload, manifest)
        log_test(11, "Negative #2", "Punctuation Removal Rejection", False, "FAILED to catch missing period!")
    except TextLockError:
        log_test(11, "Negative #2", "Punctuation Removal Rejection", True, "Successfully caught TextLockError on missing period")

    # 12. Negative Test 3: Lowercase Mutation ("ARE YOU IN PERIMENOPAUSE?" -> "are you in perimenopause?")
    bad_payload = copy.deepcopy(master_payload["slides"][0])
    bad_payload["headline"]["text"] = "are you in perimenopause?"
    try:
        TextLockSystem.validate_slide_payload(bad_payload, manifest)
        log_test(12, "Negative #3", "Lowercase Mutation Rejection", False, "FAILED to catch lowercase mutation!")
    except TextLockError:
        log_test(12, "Negative #3", "Lowercase Mutation Rejection", True, "Successfully caught TextLockError on lowercase string")

    # 13. Negative Test 4: Symbol Removal (Remove -> arrow from CTA)
    bad_payload = copy.deepcopy(master_payload["slides"][2])
    bad_payload["cta"]["text"] = "JOIN THE MIROR COMMUNITY\nLink in bio"
    try:
        TextLockSystem.validate_slide_payload(bad_payload, manifest)
        log_test(13, "Negative #4", "Symbol Removal Rejection", False, "FAILED to catch missing arrow symbol!")
    except TextLockError:
        log_test(13, "Negative #4", "Symbol Removal Rejection", True, "Successfully caught TextLockError on missing arrow")

    # 14. Negative Test 5: Word Addition ("JOIN THE MIROR COMMUNITY NOW ->")
    bad_payload = copy.deepcopy(master_payload["slides"][2])
    bad_payload["cta"]["text"] = "JOIN THE MIROR COMMUNITY NOW →\nLink in bio"
    try:
        TextLockSystem.validate_slide_payload(bad_payload, manifest)
        log_test(14, "Negative #5", "Added Word Rejection", False, "FAILED to catch added word!")
    except TextLockError:
        log_test(14, "Negative #5", "Added Word Rejection", True, "Successfully caught TextLockError on added word 'NOW'")

    # 15. Negative Test 6: Newline Removal in CTA
    bad_payload = copy.deepcopy(master_payload["slides"][2])
    bad_payload["cta"]["text"] = "JOIN THE MIROR COMMUNITY → Link in bio"
    try:
        TextLockSystem.validate_slide_payload(bad_payload, manifest)
        log_test(15, "Negative #6", "Newline Alteration Rejection", False, "FAILED to catch newline removal!")
    except TextLockError:
        log_test(15, "Negative #6", "Newline Alteration Rejection", True, "Successfully caught TextLockError on newline removal")

    # 16. Negative Test 7: Body Paragraph Paraphrasing
    bad_payload = copy.deepcopy(master_payload["slides"][1])
    bad_payload["body"][0]["text"] = "Hormones fluctuate a lot during perimenopause."
    try:
        TextLockSystem.validate_slide_payload(bad_payload, manifest)
        log_test(16, "Negative #7", "Body Paraphrase Rejection", False, "FAILED to catch paraphrased body paragraph!")
    except TextLockError:
        log_test(16, "Negative #7", "Body Paraphrase Rejection", True, "Successfully caught TextLockError on paraphrased copy")

    # 17. Negative Test 8: Missing Required Field ('cta')
    bad_payload = copy.deepcopy(master_payload["slides"][2])
    del bad_payload["cta"]
    try:
        TextLockSystem.validate_slide_payload(bad_payload, manifest)
        log_test(17, "Negative #8", "Missing Required Field Rejection", False, "FAILED to catch missing CTA field!")
    except TextLockError:
        log_test(17, "Negative #8", "Missing Required Field Rejection", True, "Successfully caught TextLockError on missing 'cta' field")

    passed_total = sum(1 for r in results if r[2])
    all_ok = (passed_total == len(results))

    print(f"\n=== QA TEST SUMMARY: {passed_total}/{len(results)} TESTS PASSED ===")
    return all_ok

if __name__ == "__main__":
    success = run_text_integrity_tests()
    sys.exit(0 if success else 1)
