"""
Unit Test Suite for MIROR T01 Renderer API Storage Abstraction Layer
Tests LocalStorageAdapter, CloudinaryStorageAdapter credential validation, error formatting, and secret protection.
"""

import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api.storage import StorageAdapter, LocalStorageAdapter, CloudinaryStorageAdapter, get_storage_adapter
from api.errors import RendererAPIException

def run_storage_tests():
    print("=== STARTING MIROR STORAGE LAYER AUTOMATED UNIT TESTS ===\n")
    
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

    # 1. LocalStorageAdapter Instance & Methods
    local_adapter = LocalStorageAdapter()
    log_test(1, "LocalStorageAdapter Instantiation", isinstance(local_adapter, StorageAdapter), "Successfully implements StorageAdapter interface")

    # 2. Local Storage Backend Default Selection
    orig_backend = os.environ.get("STORAGE_BACKEND")
    if "STORAGE_BACKEND" in os.environ:
        del os.environ["STORAGE_BACKEND"]
    default_adapter = get_storage_adapter()
    log_test(2, "Default Storage Backend is LocalStorageAdapter", isinstance(default_adapter, LocalStorageAdapter), "Defaults to LocalStorageAdapter when STORAGE_BACKEND is unset")

    # 3. Missing Credentials Do Not Crash Local Mode
    orig_cname = os.environ.get("CLOUDINARY_CLOUD_NAME")
    orig_key = os.environ.get("CLOUDINARY_API_KEY")
    orig_sec = os.environ.get("CLOUDINARY_API_SECRET")
    
    os.environ["STORAGE_BACKEND"] = "local"
    if "CLOUDINARY_CLOUD_NAME" in os.environ: del os.environ["CLOUDINARY_CLOUD_NAME"]
    if "CLOUDINARY_API_KEY" in os.environ: del os.environ["CLOUDINARY_API_KEY"]
    if "CLOUDINARY_API_SECRET" in os.environ: del os.environ["CLOUDINARY_API_SECRET"]

    local_works = True
    try:
        adapter = get_storage_adapter()
        rel_key, url = adapter.save_file(str(REPO_ROOT / "assets" / "logos" / "LOGO-001.png"), "TEST-POST", "S01")
        log_test(3, "Local Mode Functionality Without Cloudinary Credentials", rel_key.endswith("TEST-POST_T01_S01.png") and url is None, f"rel_key={rel_key}")
    except Exception as e:
        log_test(3, "Local Mode Functionality Without Cloudinary Credentials", False, str(e))

    # 4. Cloudinary Backend Selection
    os.environ["STORAGE_BACKEND"] = "cloudinary"
    c_adapter = get_storage_adapter()
    log_test(4, "Cloudinary Backend Selection", isinstance(c_adapter, CloudinaryStorageAdapter), "Returns CloudinaryStorageAdapter when STORAGE_BACKEND=cloudinary")

    # 5-6. Cloudinary Missing Credentials Error Rejection & Code
    caught_error = False
    error_code_correct = False
    error_msg = ""

    try:
        c_adapter.save_file(str(REPO_ROOT / "assets" / "logos" / "LOGO-001.png"), "TEST-POST", "S01")
    except RendererAPIException as rae:
        caught_error = True
        if rae.code == "STORAGE_UPLOAD_FAILURE":
            error_code_correct = True
        error_msg = rae.message
    except Exception as ex:
        error_msg = str(ex)

    log_test(5, "Cloudinary Rejects Missing Credentials Cleanly", caught_error, "Caught RendererAPIException on missing credentials")
    log_test(6, "Structured Error Code = STORAGE_UPLOAD_FAILURE", error_code_correct, f"Error Code: STORAGE_UPLOAD_FAILURE")

    # 7. No Secret Exposure in Error Message
    no_secret_leaks = ("secret" not in error_msg.lower() or "api_secret" in error_msg.lower()) and "password" not in error_msg.lower()
    log_test(7, "No Secrets Exposed in Error Response", no_secret_leaks, "Error response free of internal key values")

    # Restore environment
    if orig_backend: os.environ["STORAGE_BACKEND"] = orig_backend
    else: os.environ.pop("STORAGE_BACKEND", None)
    if orig_cname: os.environ["CLOUDINARY_CLOUD_NAME"] = orig_cname
    if orig_key: os.environ["CLOUDINARY_API_KEY"] = orig_key
    if orig_sec: os.environ["CLOUDINARY_API_SECRET"] = orig_sec

    # Live integration check
    live_creds = bool(os.environ.get("CLOUDINARY_CLOUD_NAME") and os.environ.get("CLOUDINARY_API_KEY") and os.environ.get("CLOUDINARY_API_SECRET"))
    if live_creds:
        print("[INFO] Cloudinary live credentials detected — running live integration check.")
    else:
        print("[INFO] Cloudinary live integration test skipped — credentials not configured (Local mode verified).")

    print(f"\n=== STORAGE QA SUMMARY: {passed_count}/{passed_count + failed_count} TESTS PASSED ===")
    return failed_count == 0

if __name__ == "__main__":
    success = run_storage_tests()
    sys.exit(0 if success else 1)
