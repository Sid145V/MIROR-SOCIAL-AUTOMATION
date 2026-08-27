"""
MIROR Social Automation — Durable Post State Store & Repository Layer
SQLite-backed thread-safe post lifecycle and selection management.
"""

import os
import sys
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple, List

REPO_ROOT = Path(__file__).resolve().parents[1]

logger = logging.getLogger("miror.state")

LIBRARY_CONFIG = {
    "master": {
        "file": REPO_ROOT / "template-engine" / "data" / "miror_30_posts_master.json",
        "variant": "01",
        "variant_name": "Light Pink",
        "variant_hex": "#F8E3E7",
        "aliases": ["master", "miror_30_posts_master", "master_library"]
    },
    "symptoms_hormones": {
        "file": REPO_ROOT / "template-engine" / "data" / "miror_symptoms_hormones_30_posts.json",
        "variant": "02",
        "variant_name": "Soft Purple",
        "variant_hex": "#E7DDF2",
        "aliases": ["symptoms_hormones", "sh", "symptoms", "miror_symptoms_hormones_30_posts"]
    },
    "supplements": {
        "file": REPO_ROOT / "template-engine" / "data" / "miror_supplements_30_posts.json",
        "variant": "03",
        "variant_name": "Warm Yellowish White",
        "variant_hex": "#F6F0D8",
        "aliases": ["supplements", "sup", "miror_supplements_30_posts"]
    }
}

def resolve_library_key(raw_key: str) -> Optional[str]:
    """Resolves arbitrary library name or alias to canonical library key."""
    if not raw_key:
        return None
    key_lower = str(raw_key).strip().lower()
    for canonical_key, cfg in LIBRARY_CONFIG.items():
        if key_lower == canonical_key or key_lower in cfg["aliases"]:
            return canonical_key
    return None

class StateStore:
    """Thread-safe and process-safe SQLite state repository for post lifecycle management."""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.environ.get("MIROR_STATE_DB_PATH", str(REPO_ROOT / "data" / "miror_state.db"))
        
        self.db_path = Path(db_path).resolve()
        os.makedirs(self.db_path.parent, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS post_progress (
                content_id TEXT PRIMARY KEY,
                library TEXT NOT NULL,
                status TEXT NOT NULL,
                reserved_at TEXT NULL,
                rendered_at TEXT NULL,
                published_at TEXT NULL,
                instagram_media_id TEXT NULL,
                retry_count INTEGER DEFAULT 0,
                last_error TEXT NULL
            );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_library_status ON post_progress (library, status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reserved_at ON post_progress (reserved_at);")
            conn.commit()
        
        self.sync_libraries()

    def sync_libraries(self):
        """Scans the three JSON libraries and populates missing state entries as UNPUBLISHED."""
        with self._get_connection() as conn:
            for canon_key, cfg in LIBRARY_CONFIG.items():
                json_path = cfg["file"]
                if not json_path.exists():
                    logger.warning(f"Library JSON file not found: {json_path}")
                    continue
                
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                posts = data.get("posts", [])
                for post in posts:
                    cid = post.get("content_id")
                    if not cid:
                        continue
                    
                    conn.execute("""
                    INSERT INTO post_progress (content_id, library, status)
                    VALUES (?, ?, 'UNPUBLISHED')
                    ON CONFLICT(content_id) DO NOTHING;
                    """, (cid, canon_key))
            conn.commit()

    def get_next_post(self, library_key: str, reservation_minutes: int = 30) -> Optional[Tuple[str, str, str, Dict[str, Any]]]:
        """
        Atomically selects the next eligible post from library and sets status to RESERVED.
        Returns tuple: (content_id, canonical_library_key, variant, full_post_dict)
        """
        canon_key = resolve_library_key(library_key)
        if not canon_key:
            raise ValueError(f"Invalid library parameter '{library_key}'. Must be one of ['master', 'symptoms_hormones', 'supplements'].")

        now_utc = datetime.now(timezone.utc)
        cutoff_utc = now_utc - timedelta(minutes=reservation_minutes)
        now_iso = now_utc.isoformat()
        cutoff_iso = cutoff_utc.isoformat()

        conn = self._get_connection()
        try:
            # Begin atomic write transaction
            conn.execute("BEGIN IMMEDIATE;")
            cursor = conn.cursor()
            cursor.execute("""
            SELECT content_id FROM post_progress
            WHERE library = ? AND (
                status = 'UNPUBLISHED' OR
                (status = 'RESERVED' AND reserved_at IS NOT NULL AND reserved_at < ?)
            )
            ORDER BY ROWID ASC
            LIMIT 1;
            """, (canon_key, cutoff_iso))
            
            row = cursor.fetchone()
            if not row:
                conn.commit()
                return None
            
            selected_id = row["content_id"]
            cursor.execute("""
            UPDATE post_progress
            SET status = 'RESERVED', reserved_at = ?
            WHERE content_id = ?;
            """, (now_iso, selected_id))
            conn.commit()
            
            logger.info(f"Post '{selected_id}' reserved for library '{canon_key}' at {now_iso}")
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        # Load post payload from library JSON file
        cfg = LIBRARY_CONFIG[canon_key]
        with open(cfg["file"], "r", encoding="utf-8") as f:
            data = json.load(f)

        for post in data.get("posts", []):
            if post.get("content_id") == selected_id:
                post_payload = dict(post)
                post_payload["backgroundVariant"] = cfg["variant"]
                return selected_id, canon_key, cfg["variant"], post_payload

        return None

    def mark_rendered(self, content_id: str):
        """Updates post status to RENDERED after successful renderer execution."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute("""
            UPDATE post_progress
            SET status = 'RENDERED', rendered_at = ?
            WHERE content_id = ? AND status != 'PUBLISHED';
            """, (now_iso, content_id))
            conn.commit()
        logger.info(f"Post '{content_id}' status updated to RENDERED")

    def mark_published(self, content_id: str, instagram_media_id: Optional[str] = None) -> Dict[str, Any]:
        """Updates post status to PUBLISHED after Instagram confirmation."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content_id, library, status FROM post_progress WHERE content_id = ?;", (content_id,))
            row = cursor.fetchone()
            if not row:
                raise KeyError(f"Content ID '{content_id}' not found in state store.")
            
            cursor.execute("""
            UPDATE post_progress
            SET status = 'PUBLISHED', published_at = ?, instagram_media_id = ?
            WHERE content_id = ?;
            """, (now_iso, instagram_media_id, content_id))
            conn.commit()
        
        logger.info(f"Post '{content_id}' status updated to PUBLISHED (Instagram Media ID: {instagram_media_id})")
        return {
            "content_id": content_id,
            "status": "PUBLISHED",
            "published_at": now_iso,
            "instagram_media_id": instagram_media_id
        }

    def record_failure(self, content_id: str, error_message: str):
        """Increments retry count and records error for a post."""
        with self._get_connection() as conn:
            conn.execute("""
            UPDATE post_progress
            SET retry_count = retry_count + 1, last_error = ?
            WHERE content_id = ?;
            """, (str(error_message)[:500], content_id))
            conn.commit()
        logger.warning(f"Post '{content_id}' failure recorded: {error_message}")

    def get_post_state(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Returns the current state dictionary for a given post."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM post_progress WHERE content_id = ?;", (content_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def reset_state_for_testing(self):
        """Resets all state tables to UNPUBLISHED for testing environments."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM post_progress;")
            conn.commit()
        self.sync_libraries()
