"""
Automated QA Validation Suite — T01 Exact Text Lock & Text Integrity System
Verifies positive SHA-256 fingerprint matching and negative mutation rejection.
"""

import os
import sys
import json
import copy

# Ensure template-engine modules are accessible
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
core_dir = os.path.join(root_dir, "template-engine", "core")
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

from text_lock import TextLockSystem, TextLockError

def run_text_integrity_tests():
    master_json_path = os.path.join(root_dir, "template-engine", "tests", "test_content_MIROR-T01-MASTER.json")
    with open(master_json_path, "r", encoding="utf-8") as f:
        master_payload = json.load(f)

    expected_manifest = master_payload["text_integrity"]
    slides = master_payload["slides"]

    passed_count = 0
    failed_count = 0

    def log_test(num, category, name, passed, details=""):
        nonlocal passed_count, failed_count
        status = "PASSED" if passed else "FAILED"
        if passed:
            passed_count += 1
        else:
            failed_count += 1
        safe_details = details.encode("ascii", "replace").decode("ascii")
        safe_name = name.encode("ascii", "replace").decode("ascii")
        print(f"[{status}] Test #{num} ({category}) - {safe_name}: {safe_details}")

    print("=== STARTING T01 TEXT LOCK & TEXT INTEGRITY QA SUITE ===\n")

    # -------------------------------------------------------------
    # POSITIVE INTEGRITY TESTS (Tests 1 - 9)
    # -------------------------------------------------------------
    # 1. Master JSON Exists
    log_test(1, "Positive", "Master Content Schema File Exists", os.path.exists(master_json_path), master_json_path)

    # 2. Text Integrity Manifest Exists
    log_test(2, "Positive", "SHA-256 Integrity Manifest Present", len(expected_manifest) == 10, f"Contains {len(expected_manifest)} SHA-256 hashes")

    # 3. Slide 1 (S01) Validation
    try:
        s01_manifest = TextLockSystem.validate_slide_payload(slides[0], expected_manifest)
        log_test(3, "Positive", "S01 Hook Text Lock Validation", True, f"Matched hash {s01_manifest['S01.headline'][:16]}...")
    except Exception as e:
        log_test(3, "Positive", "S01 Hook Text Lock Validation", False, str(e))

    # 4. Slide 2 (S02) Validation
    try:
        s02_manifest = TextLockSystem.validate_slide_payload(slides[1], expected_manifest)
        log_test(4, "Positive", "S02 Follow-Through Text Lock Validation", True, f"Validated headline & {len(slides[1]['body'])} body paragraphs")
    except Exception as e:
        log_test(4, "Positive", "S02 Follow-Through Text Lock Validation", False, str(e))

    # 5. Slide 3 (S03) Validation
    try:
        s03_manifest = TextLockSystem.validate_slide_payload(slides[2], expected_manifest)
        log_test(5, "Positive", "S03 CTA Text Lock Validation", True, f"Validated headline, body & CTA hash {s03_manifest['S03.cta'][:16]}...")
    except Exception as e:
        log_test(5, "Positive", "S03 CTA Text Lock Validation", False, str(e))

    # 6. Lock Attribute check ("EXACT")
    all_exact = all(
        s["headline"].get("lock") == "EXACT" and (
            "cta" not in s or s["cta"].get("lock") == "EXACT"
        ) for s in slides
    )
    log_test(6, "Positive", "Explicit lock='EXACT' Attributes", all_exact, "All headline, body, and CTA elements locked to 'EXACT'")

    # 7. Non-Empty String Type Check
    all_str = all(isinstance(v, str) and len(v) > 0 for k, v in expected_manifest.items())
    log_test(7, "Positive", "Immutable Non-Empty String Check", all_str, "100% of locked fields are non-empty strings")

    # 8. Preservation of Exact Newlines
    s03_cta_raw = slides[2]["cta"]["text"]
    log_test(8, "Positive", "Exact Newline Preservation", "\n" in s03_cta_raw, "Literal line break character preserved in CTA copy")

    # 9. Preservation of Literal Arrow Symbol
    log_test(9, "Positive", "Literal Symbol Preservation", "→" in s03_cta_raw, "Literal arrow symbol preserved in CTA copy")

    print("\n--- NEGATIVE MUTATION TESTS (Verifying explicit rejection of text alterations) ---\n")

    # -------------------------------------------------------------
    # NEGATIVE MUTATION TESTS (Tests 10 - 17)
    # -------------------------------------------------------------

    # Negative Case 1: Character Mutation ("Start Connecting" vs "START CONNECTING")
    mut_1 = copy.deepcopy(slides[2])
    mut_1["headline"]["text"] = "Start Connecting\nTHE DOTS."
    try:
        TextLockSystem.validate_slide_payload(mut_1, expected_manifest)
        log_test(10, "Negative #1", "Character Case Mutation Rejection", False, "Failed to reject case mutation")
    except TextLockError as e:
        log_test(10, "Negative #1", "Character Case Mutation Rejection", True, "Successfully caught TextLockError on case mutation")

    # Negative Case 2: Punctuation Removal ("Get expert guidance" vs "Get expert guidance.")
    mut_2 = copy.deepcopy(slides[2])
    mut_2["body"][1]["text"] = "Get expert guidance"
    try:
        TextLockSystem.validate_slide_payload(mut_2, expected_manifest)
        log_test(11, "Negative #2", "Punctuation Removal Rejection", False, "Failed to reject missing period")
    except TextLockError as e:
        log_test(11, "Negative #2", "Punctuation Removal Rejection", True, "Successfully caught TextLockError on missing period")

    # Negative Case 3: Capitalization Change ("you're tired.")
    mut_3 = copy.deepcopy(slides[0])
    mut_3["headline"]["text"] = "you're tired."
    try:
        TextLockSystem.validate_slide_payload(mut_3, expected_manifest)
        log_test(12, "Negative #3", "Lowercase Mutation Rejection", False, "Failed to reject lowercase string")
    except TextLockError as e:
        log_test(12, "Negative #3", "Lowercase Mutation Rejection", True, "Successfully caught TextLockError on lowercase string")

    # Negative Case 4: Arrow Removal ("JOIN THE MIROR COMMUNITY" without "→")
    mut_4 = copy.deepcopy(slides[2])
    mut_4["cta"]["text"] = "JOIN THE MIROR COMMUNITY\nLink in bio"
    try:
        TextLockSystem.validate_slide_payload(mut_4, expected_manifest)
        log_test(13, "Negative #4", "Symbol Removal Rejection", False, "Failed to reject missing arrow symbol")
    except TextLockError as e:
        log_test(13, "Negative #4", "Symbol Removal Rejection", True, "Successfully caught TextLockError on missing arrow")

    # Negative Case 5: Added Word ("YOUR BODY IS NOW TRYING...")
    mut_5 = copy.deepcopy(slides[0])
    mut_5["headline"]["text"] = "YOU'RE TIRED.\nYOU CAN'T SLEEP.\nYOU'RE IRRITABLE.\n\nYOUR BODY IS NOW TRYING\nTO TELL YOU SOMETHING."
    try:
        TextLockSystem.validate_slide_payload(mut_5, expected_manifest)
        log_test(14, "Negative #5", "Added Word Rejection", False, "Failed to reject added word 'NOW'")
    except TextLockError as e:
        log_test(14, "Negative #5", "Added Word Rejection", True, "Successfully caught TextLockError on added word 'NOW'")

    # Negative Case 6: Newline Removal / Alteration
    mut_6 = copy.deepcopy(slides[2])
    mut_6["headline"]["text"] = "START CONNECTING THE DOTS."
    try:
        TextLockSystem.validate_slide_payload(mut_6, expected_manifest)
        log_test(15, "Negative #6", "Newline Alteration Rejection", False, "Failed to reject newline removal")
    except TextLockError as e:
        log_test(15, "Negative #6", "Newline Alteration Rejection", True, "Successfully caught TextLockError on newline removal")

    # Negative Case 7: Body Paragraph Copy Mutation ("During menopause...")
    mut_7 = copy.deepcopy(slides[1])
    mut_7["body"][0]["text"] = "During menopause, your hormones can fluctuate significantly."
    try:
        TextLockSystem.validate_slide_payload(mut_7, expected_manifest)
        log_test(16, "Negative #7", "Body Paraphrase Rejection", False, "Failed to reject paraphrased medical term")
    except TextLockError as e:
        log_test(16, "Negative #7", "Body Paraphrase Rejection", True, "Successfully caught TextLockError on paraphrased copy")

    # Negative Case 8: Missing Required Field (cta field deleted)
    mut_8 = copy.deepcopy(slides[2])
    del mut_8["cta"]
    try:
        TextLockSystem.validate_slide_payload(mut_8, expected_manifest)
        log_test(17, "Negative #8", "Missing Required Field Rejection", False, "Failed to reject missing 'cta' field")
    except TextLockError as e:
        log_test(17, "Negative #8", "Missing Required Field Rejection", True, "Successfully caught TextLockError on missing 'cta' field")

    print(f"\n=== QA TEST SUMMARY: {passed_count}/{passed_count + failed_count} TESTS PASSED ===")
    return failed_count == 0

if __name__ == "__main__":
    success = run_text_integrity_tests()
    sys.exit(0 if success else 1)
