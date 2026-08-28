"""
MIROR Social Automation — PostgreSQL State Repository & Selection Test Suite
Comprehensive testing for PostgreSQL-backed post lifecycle state and atomic content selection.
"""

import os
import sys
import pytest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

REPO_ROOT = Path(__file__).resolve().parents[2]
core_dir = REPO_ROOT / "template-engine" / "core"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(core_dir) not in sys.path:
    sys.path.insert(0, str(core_dir))

from api.state import PostgresStateStore, resolve_library_key
from text_lock import TextLockSystem

@pytest.fixture(scope="module")
def pg_store():
    """Module fixture providing a PostgresStateStore instance and cleaning up test state afterward."""
    os.environ["STATE_BACKEND"] = "postgres"
    store = PostgresStateStore()
    store.reset_state_for_testing()
    yield store
    # Non-destructive cleanup: reset statuses back to UNPUBLISHED for clean production state
    store.reset_state_for_testing()


def test_01_postgres_connection(pg_store):
    """Verifies successful connection to PostgreSQL RDS."""
    assert pg_store is not None

def test_02_library_key_resolution():
    """Verifies canonical library key resolution from aliases."""
    assert resolve_library_key("master") == "master"
    assert resolve_library_key("symptoms_hormones") == "symptoms_hormones"
    assert resolve_library_key("sh") == "symptoms_hormones"
    assert resolve_library_key("supplements") == "supplements"
    assert resolve_library_key("sup") == "supplements"
    assert resolve_library_key("invalid_lib") is None

def test_03_first_post_selection_master(pg_store):
    """Verifies GET /content/next for master library returns MIROR-001 and variant 01."""
    res = pg_store.get_next_post("master")
    assert res is not None
    cid, lib, variant, payload = res
    assert cid == "MIROR-001"
    assert lib == "master"
    assert variant == "01"
    assert payload["template_id"] == "T01"
    assert len(payload["slides"]) == 3
    assert [s["id"] for s in payload["slides"]] == ["S01", "S02", "S03"]

def test_04_first_post_selection_symptoms(pg_store):
    """Verifies GET /content/next for symptoms_hormones returns MIROR-SH-001 and variant 02."""
    res = pg_store.get_next_post("symptoms_hormones")
    assert res is not None
    cid, lib, variant, payload = res
    assert cid == "MIROR-SH-001"
    assert lib == "symptoms_hormones"
    assert variant == "02"
    assert len(payload["slides"]) == 3

def test_05_first_post_selection_supplements(pg_store):
    """Verifies GET /content/next for supplements returns MIROR-SUP-001 and variant 03."""
    res = pg_store.get_next_post("supplements")
    assert res is not None
    cid, lib, variant, payload = res
    assert cid == "MIROR-SUP-001"
    assert lib == "supplements"
    assert variant == "03"
    assert len(payload["slides"]) == 3

def test_06_content_reconstruction_textlock(pg_store):
    """Verifies reconstructed PostgreSQL slide payloads validate 100% against TextLockSystem."""
    res = pg_store.get_next_post("master")
    assert res is not None
    cid, lib, variant, payload = res

    manifest = payload.get("text_integrity", {})
    for slide in payload["slides"]:
        s_id = slide["id"]
        # Validate exact text hashes
        TextLockSystem.validate_slide_payload(slide, manifest)

def test_07_reservation_and_sequential_order(pg_store):
    """Verifies sequential order selection and state status transitions to RESERVED."""
    res2 = pg_store.get_next_post("master")
    assert res2 is not None
    cid2, _, _, _ = res2
    assert cid2.startswith("MIROR-")

    st = pg_store.get_post_state(cid2)
    assert st["status"] == "RESERVED"


def test_08_concurrent_selection_safety(pg_store):
    """Verifies concurrent multi-threaded requests never receive duplicate post IDs."""
    results = []
    def worker():
        return pg_store.get_next_post("master")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker) for _ in range(5)]
        for f in futures:
            res = f.result()
            if res:
                results.append(res[0])

    assert len(results) == len(set(results)), f"Duplicate content IDs detected in concurrent selection: {results}"

def test_09_mark_rendered_and_published_lifecycle(pg_store):
    """Verifies post state transitions from RESERVED -> RENDERED -> PUBLISHED with idempotency."""
    cid = "MIROR-001"
    
    # 1. Mark Rendered
    pg_store.mark_rendered(cid, run_id="TEST-RUN-01", s01_url="http://s01.png", s02_url="http://s02.png", s03_url="http://s03.png")
    st1 = pg_store.get_post_state(cid)
    assert st1["status"] == "RENDERED"

    # 2. Mark Published
    res_pub = pg_store.mark_published(cid, instagram_media_id="17900123456789")
    assert res_pub["status"] == "PUBLISHED"

    st2 = pg_store.get_post_state(cid)
    assert st2["status"] == "PUBLISHED"
    assert st2["instagram_media_id"] == "17900123456789"

    # 3. Idempotency test (publishing second time updates record cleanly without error)
    res_pub2 = pg_store.mark_published(cid, instagram_media_id="17900123456789")
    assert res_pub2["status"] == "PUBLISHED"

def test_10_invalid_content_id_error(pg_store):
    """Verifies KeyError raises for unknown content ID."""
    with pytest.raises(KeyError):
        pg_store.mark_published("MIROR-INVALID-999")

if __name__ == "__main__":
    pytest.main(["-v", __file__])
