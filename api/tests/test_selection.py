"""
MIROR Social Automation — Content Selection & Durable State Unit Tests
"""

import os
import sys
import json
import pytest
import threading
from pathlib import Path
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Use isolated temp database for tests
os.environ["MIROR_STATE_DB_PATH"] = str(REPO_ROOT / "data" / "test_miror_state.db")

from api.main import app, state_store
from api.state import StateStore, LIBRARY_CONFIG

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db_before_test():
    """Resets test database before every test."""
    state_store.reset_state_for_testing()
    yield

def test_01_health_check():
    """Existing GET /health endpoint still works."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "miror-renderer", "version": "1.0.0"}

def test_02_library_validation():
    """Validates library parameter rejection for invalid inputs."""
    resp = client.get("/content/next?library=invalid_lib")
    assert resp.status_code == 400
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_LIBRARY"

def test_03_first_post_selection():
    """Verifies first post selection for all three libraries."""
    resp_master = client.get("/content/next?library=master")
    assert resp_master.status_code == 200
    data_m = resp_master.json()
    assert data_m["content_id"] == "MIROR-001"
    assert data_m["background_variant"] == "01"

    resp_sh = client.get("/content/next?library=symptoms_hormones")
    assert resp_sh.status_code == 200
    data_sh = resp_sh.json()
    assert data_sh["content_id"] == "MIROR-SH-001"
    assert data_sh["background_variant"] == "02"

    resp_sup = client.get("/content/next?library=supplements")
    assert resp_sup.status_code == 200
    data_sup = resp_sup.json()
    assert data_sup["content_id"] == "MIROR-SUP-001"
    assert data_sup["background_variant"] == "03"

def test_04_sequential_selection():
    """Verifies sequential selection within a single library."""
    p1 = client.get("/content/next?library=master").json()["content_id"]
    p2 = client.get("/content/next?library=master").json()["content_id"]
    p3 = client.get("/content/next?library=master").json()["content_id"]
    
    assert p1 == "MIROR-001"
    assert p2 == "MIROR-002"
    assert p3 == "MIROR-003"

def test_05_independent_progress():
    """Verifies that all three libraries progress independently."""
    m1 = client.get("/content/next?library=master").json()["content_id"]
    sh1 = client.get("/content/next?library=sh").json()["content_id"]
    m2 = client.get("/content/next?library=master").json()["content_id"]
    sup1 = client.get("/content/next?library=sup").json()["content_id"]
    sh2 = client.get("/content/next?library=sh").json()["content_id"]

    assert m1 == "MIROR-001"
    assert m2 == "MIROR-002"
    assert sh1 == "MIROR-SH-001"
    assert sh2 == "MIROR-SH-002"
    assert sup1 == "MIROR-SUP-001"

def test_06_reservation_creation():
    """Verifies that selecting a post sets status to RESERVED."""
    res = client.get("/content/next?library=master").json()
    cid = res["content_id"]
    
    st = state_store.get_post_state(cid)
    assert st["status"] == "RESERVED"
    assert st["reserved_at"] is not None

def test_07_reservation_expiry():
    """Verifies that expired RESERVED posts become eligible again."""
    res = client.get("/content/next?library=master").json()
    cid = res["content_id"]
    assert cid == "MIROR-001"

    # Artificially set reserved_at to 40 minutes ago
    from datetime import datetime, timezone, timedelta
    past_time = (datetime.now(timezone.utc) - timedelta(minutes=40)).isoformat()
    
    with state_store._get_connection() as conn:
        conn.execute("UPDATE post_progress SET reserved_at = ? WHERE content_id = ?;", (past_time, cid))
        conn.commit()

    # Next request should re-select MIROR-001 because reservation expired
    res_retry = client.get("/content/next?library=master").json()
    assert res_retry["content_id"] == "MIROR-001"

def test_08_concurrent_selection():
    """Verifies thread-safety and atomic reservation under simultaneous requests."""
    selected_ids = []
    errors = []

    def fetch_next():
        try:
            r = client.get("/content/next?library=master")
            if r.status_code == 200:
                selected_ids.append(r.json()["content_id"])
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=fetch_next) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(selected_ids) == 5
    # Every returned post ID must be unique!
    assert len(set(selected_ids)) == 5

def test_09_published_state_transition():
    """Verifies state transition to PUBLISHED upon calling POST /content/published."""
    res = client.get("/content/next?library=symptoms_hormones").json()
    cid = res["content_id"]

    pub_res = client.post("/content/published", json={
        "content_id": cid,
        "instagram_media_id": "IG_MEDIA_123456"
    })
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert pub_data["success"] is True
    assert pub_data["status"] == "PUBLISHED"
    assert pub_data["instagram_media_id"] == "IG_MEDIA_123456"

    st = state_store.get_post_state(cid)
    assert st["status"] == "PUBLISHED"
    assert st["published_at"] is not None

def test_10_invalid_content_id():
    """Verifies 404 response when attempting to publish unknown content ID."""
    pub_res = client.post("/content/published", json={
        "content_id": "MIROR-INVALID-999",
        "instagram_media_id": "123"
    })
    assert pub_res.status_code == 404
    assert pub_res.json()["error"]["code"] == "INVALID_CONTENT_ID"

def test_11_render_failure_recovery():
    """Verifies failure recording when rendering fails."""
    res = client.get("/content/next?library=supplements").json()
    cid = res["content_id"]

    state_store.record_failure(cid, "Test renderer timeout")
    st = state_store.get_post_state(cid)
    assert st["retry_count"] == 1
    assert "Test renderer timeout" in st["last_error"]
    # Post remains in recoverable state
    assert st["status"] in ["RESERVED", "UNPUBLISHED"]

def test_12_json_content_integrity():
    """Verifies exact copy and structure preservation when returning post payload."""
    res = client.get("/content/next?library=master").json()
    post = res["post"]
    
    assert post["content_id"] == "MIROR-001"
    assert post["template_id"] == "T01"
    assert "slides" in post
    assert len(post["slides"]) == 3
    assert post["backgroundVariant"] == "01"

def test_13_full_post_lifecycle():
    """Tests complete lifecycle: UNPUBLISHED -> RESERVED -> RENDERED -> PUBLISHED."""
    # 1. Get next post (UNPUBLISHED -> RESERVED)
    next_res = client.get("/content/next?library=symptoms_hormones").json()
    cid = next_res["content_id"]
    post_payload = next_res["post"]

    assert state_store.get_post_state(cid)["status"] == "RESERVED"

    # 2. Render post (RESERVED -> RENDERED)
    # Pass text_integrity along with post_payload
    render_req = {
        "post_id": cid,
        "template": "T01",
        "backgroundVariant": "02",
        "slides": post_payload["slides"]
    }
    if "text_integrity" in post_payload:
        render_req["text_integrity"] = post_payload["text_integrity"]

    render_res = client.post("/render", json=render_req)
    assert render_res.status_code == 200
    assert render_res.json()["success"] is True

    assert state_store.get_post_state(cid)["status"] == "RENDERED"
    assert state_store.get_post_state(cid)["rendered_at"] is not None

    # 3. Publish post (RENDERED -> PUBLISHED)
    pub_res = client.post("/content/published", json={
        "content_id": cid,
        "instagram_media_id": "INSTA_987654321"
    })
    assert pub_res.status_code == 200

    assert state_store.get_post_state(cid)["status"] == "PUBLISHED"
    assert state_store.get_post_state(cid)["published_at"] is not None

if __name__ == "__main__":
    pytest.main(["-v", __file__])
