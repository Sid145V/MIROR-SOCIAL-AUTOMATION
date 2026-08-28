"""
MIROR Social Automation — Durable Post State Store & Repository Layer
Dual-backend post lifecycle & content selection state store (PostgreSQL & SQLite).
"""

import os
import sys
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple, List

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

REPO_ROOT = Path(__file__).resolve().parents[1]
core_dir = REPO_ROOT / "template-engine" / "core"
if str(core_dir) not in sys.path:
    sys.path.insert(0, str(core_dir))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

from text_lock import TextLockSystem

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

class SQLiteStateStore:
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
        canon_key = resolve_library_key(library_key)
        if not canon_key:
            raise ValueError(f"Invalid library parameter '{library_key}'. Must be one of ['master', 'symptoms_hormones', 'supplements'].")

        now_utc = datetime.now(timezone.utc)
        cutoff_utc = now_utc - timedelta(minutes=reservation_minutes)
        now_iso = now_utc.isoformat()
        cutoff_iso = cutoff_utc.isoformat()

        conn = self._get_connection()
        try:
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

        cfg = LIBRARY_CONFIG[canon_key]
        with open(cfg["file"], "r", encoding="utf-8") as f:
            data = json.load(f)

        for post in data.get("posts", []):
            if post.get("content_id") == selected_id:
                post_payload = dict(post)
                post_payload["backgroundVariant"] = cfg["variant"]
                return selected_id, canon_key, cfg["variant"], post_payload

        return None

    def mark_rendered(self, content_id: str, run_id: Optional[str] = None, s01_url: Optional[str] = None, s02_url: Optional[str] = None, s03_url: Optional[str] = None, template: str = "T01", background_variant: str = "01"):
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute("""
            UPDATE post_progress
            SET status = 'RENDERED', rendered_at = ?
            WHERE content_id = ? AND status != 'PUBLISHED';
            """, (now_iso, content_id))
            conn.commit()
        logger.info(f"Post '{content_id}' status updated to RENDERED")

    def mark_published(self, content_id: str, instagram_media_id: Optional[str] = None, instagram_post_url: Optional[str] = None, run_id: Optional[str] = None, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
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

    def record_failure(self, content_id: str, error_message: str, stage: str = "RENDER", run_id: Optional[str] = None):
        with self._get_connection() as conn:
            conn.execute("""
            UPDATE post_progress
            SET retry_count = retry_count + 1, last_error = ?
            WHERE content_id = ?;
            """, (str(error_message)[:500], content_id))
            conn.commit()
        logger.warning(f"Post '{content_id}' failure recorded: {error_message}")

    def get_post_state(self, content_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM post_progress WHERE content_id = ?;", (content_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def reset_state_for_testing(self):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM post_progress;")
            conn.commit()
        self.sync_libraries()


class PostgresStateStore:
    """Production PostgreSQL-backed state repository for post lifecycle management."""

    def __init__(self):
        if not PSYCOPG2_AVAILABLE:
            raise RuntimeError("psycopg2 is required for PostgresStateStore but is not installed.")

        self.db_host = os.getenv("DB_HOST", "").strip()
        self.db_port = os.getenv("DB_PORT", "5432").strip()
        self.db_name = os.getenv("DB_NAME", "").strip()
        self.db_user = os.getenv("DB_USER", "").strip()
        self.db_pass = os.getenv("DB_PASSWORD", "").strip()
        self.db_ssl = os.getenv("DB_SSLMODE", "require").strip()

        if not self.db_host or not self.db_name or not self.db_user or not self.db_pass:
            raise ValueError("PostgreSQL environment variables (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD) are not fully configured.")

        # Test connection
        conn = self._get_connection()
        conn.close()

    def _get_connection(self):
        conn = psycopg2.connect(
            host=self.db_host,
            port=self.db_port,
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_pass,
            sslmode=self.db_ssl,
            connect_timeout=15
        )
        return conn

    def get_next_post(self, library_key: str, reservation_minutes: int = 30) -> Optional[Tuple[str, str, str, Dict[str, Any]]]:
        canon_key = resolve_library_key(library_key)
        if not canon_key:
            raise ValueError(f"Invalid library parameter '{library_key}'. Must be one of ['master', 'symptoms_hormones', 'supplements'].")

        conn = self._get_connection()
        conn.autocommit = True
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT out_content_id, out_library_key, out_template_id, out_background_variant FROM reserve_next_content(%s, %s);", (canon_key, reservation_minutes))
            row = cur.fetchone()
            if not row or not row.get("out_content_id"):
                return None

            selected_id = row["out_content_id"]
            variant = row["out_background_variant"]
            template_id = row["out_template_id"]

            # Reconstruct render-ready post payload from content_posts & content_slides
            cur.execute("""
                SELECT cp.content_id, cp.template_id, cp.content_title, cp.objective, cp.content_type, cp.source,
                       cs.slide_id, cs.slide_type, cs.headline_text, cs.headline_lock, cs.body_json, cs.cta_text, cs.cta_lock
                FROM content_posts cp
                JOIN content_slides cs ON cp.content_id = cs.content_id
                WHERE cp.content_id = %s
                ORDER BY cs.slide_id ASC;
            """, (selected_id,))

            slide_rows = cur.fetchall()
            if not slide_rows:
                return None

            first = slide_rows[0]
            slides_payload = []
            manifest = {}

            for s_row in slide_rows:
                s_id = s_row["slide_id"]
                s_type = s_row["slide_type"]
                
                s_dict = {
                    "id": s_id,
                    "type": s_type,
                    "headline": {
                        "text": s_row["headline_text"],
                        "lock": s_row["headline_lock"] or "EXACT"
                    }
                }
                manifest[f"{s_id}.headline"] = TextLockSystem.compute_sha256(s_row["headline_text"])

                if s_row["body_json"]:
                    b_list = s_row["body_json"] if isinstance(s_row["body_json"], list) else json.loads(s_row["body_json"])
                    s_dict["body"] = b_list
                    for b_idx, b_item in enumerate(b_list):
                        b_txt = b_item.get("text", b_item) if isinstance(b_item, dict) else b_item
                        manifest[f"{s_id}.body.{b_idx}"] = TextLockSystem.compute_sha256(b_txt)

                if s_row["cta_text"]:
                    s_dict["cta"] = {
                        "text": s_row["cta_text"],
                        "lock": s_row["cta_lock"] or "EXACT"
                    }
                    manifest[f"{s_id}.cta"] = TextLockSystem.compute_sha256(s_row["cta_text"])

                slides_payload.append(s_dict)

            post_payload = {
                "content_id": selected_id,
                "template_id": template_id,
                "content_title": first["content_title"],
                "objective": first["objective"],
                "type": first["content_type"],
                "source": first["source"],
                "backgroundVariant": variant,
                "slides": slides_payload,
                "text_integrity": manifest
            }

            return selected_id, canon_key, variant, post_payload
        finally:
            conn.close()

    def _ensure_automation_run(self, cur, run_id: str):
        if not run_id:
            return
        cur.execute("""
            INSERT INTO automation_runs (run_id, execution_date, overall_status)
            VALUES (%s, CURRENT_DATE, 'IN_PROGRESS')
            ON CONFLICT (run_id) DO NOTHING;
        """, (run_id,))

    def mark_rendered(self, content_id: str, run_id: Optional[str] = None, s01_url: Optional[str] = None, s02_url: Optional[str] = None, s03_url: Optional[str] = None, template: str = "T01", background_variant: str = "01"):
        conn = self._get_connection()
        conn.autocommit = True
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE content_posts
                SET status = 'RENDERED', updated_at = clock_timestamp()
                WHERE content_id = %s AND status != 'PUBLISHED';
            """, (content_id,))

            if s01_url and s02_url and s03_url:
                r_id = run_id or f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
                self._ensure_automation_run(cur, r_id)
                cur.execute("""
                    INSERT INTO render_outputs (content_id, run_id, render_status, template_id, background_variant, s01_render_url, s02_render_url, s03_render_url)
                    VALUES (%s, %s, 'SUCCESS', %s, %s, %s, %s, %s)
                    ON CONFLICT (content_id, run_id) DO UPDATE SET
                        s01_render_url = EXCLUDED.s01_render_url,
                        s02_render_url = EXCLUDED.s02_render_url,
                        s03_render_url = EXCLUDED.s03_render_url,
                        rendered_at = clock_timestamp();
                """, (content_id, r_id, template, background_variant, s01_url, s02_url, s03_url))
            logger.info(f"PostgresStateStore: Post '{content_id}' status updated to RENDERED")
        finally:
            conn.close()

    def mark_published(self, content_id: str, instagram_media_id: Optional[str] = None, instagram_post_url: Optional[str] = None, run_id: Optional[str] = None, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        conn = self._get_connection()
        conn.autocommit = True
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT content_id, library_key, status FROM content_posts WHERE content_id = %s;", (content_id,))
            row = cur.fetchone()
            if not row:
                raise KeyError(f"Content ID '{content_id}' not found in PostgreSQL state store.")

            cur.execute("""
                UPDATE content_posts
                SET status = 'PUBLISHED', updated_at = clock_timestamp()
                WHERE content_id = %s;
            """, (content_id,))

            now_iso = datetime.now(timezone.utc).isoformat()
            ik_value = idempotency_key or f"PUB-{content_id}"
            media_id_value = instagram_media_id or f"MEDIA-{content_id}"
            r_id = run_id or f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d')}"

            self._ensure_automation_run(cur, r_id)

            cur.execute("""
                INSERT INTO instagram_publications (content_id, run_id, instagram_media_id, instagram_post_url, publication_status, idempotency_key)
                VALUES (%s, %s, %s, %s, 'PUBLISHED', %s)
                ON CONFLICT (content_id, run_id) DO UPDATE SET
                    instagram_media_id = EXCLUDED.instagram_media_id,
                    instagram_post_url = EXCLUDED.instagram_post_url,
                    publication_status = 'PUBLISHED',
                    published_at = clock_timestamp();
            """, (content_id, r_id, media_id_value, instagram_post_url, ik_value))


            logger.info(f"PostgresStateStore: Post '{content_id}' status updated to PUBLISHED")
            return {
                "content_id": content_id,
                "status": "PUBLISHED",
                "published_at": now_iso,
                "instagram_media_id": media_id_value
            }
        finally:
            conn.close()

    def record_failure(self, content_id: str, error_message: str, stage: str = "RENDER", run_id: Optional[str] = None):
        conn = self._get_connection()
        conn.autocommit = True
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE content_posts
                SET retry_count = retry_count + 1, last_error = %s, updated_at = clock_timestamp()
                WHERE content_id = %s;
            """, (str(error_message)[:500], content_id))

            if run_id:
                self._ensure_automation_run(cur, run_id)

            cur.execute("""
                INSERT INTO error_events (run_id, content_id, stage, error_code, error_message, retry_count)
                VALUES (%s, %s, %s, 'EXECUTION_ERROR', %s, 1);
            """, (run_id, content_id, stage, str(error_message)[:500]))

            logger.warning(f"PostgresStateStore: Post '{content_id}' failure recorded: {error_message}")
        finally:
            conn.close()

    def get_post_state(self, content_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT cp.content_id, cp.library_key AS library, cp.status, cp.retry_count, cp.last_error,
                       cp.updated_at AS reserved_at, cp.updated_at AS rendered_at, ip.published_at, ip.instagram_media_id
                FROM content_posts cp
                LEFT JOIN instagram_publications ip ON cp.content_id = ip.content_id
                WHERE cp.content_id = %s;
            """, (content_id,))
            row = cur.fetchone()
            if row:
                st_dict = dict(row)
                st_dict["reserved_at"] = st_dict["reserved_at"].isoformat() if st_dict.get("reserved_at") else None
                st_dict["rendered_at"] = st_dict["rendered_at"].isoformat() if st_dict.get("rendered_at") and st_dict["status"] in ["RENDERED", "PUBLISHED"] else None
                st_dict["published_at"] = st_dict["published_at"].isoformat() if st_dict.get("published_at") else None
                return st_dict
            return None
        finally:
            conn.close()

    def reset_state_for_testing(self):
        """Resets post statuses to UNPUBLISHED for non-destructive test isolation."""
        conn = self._get_connection()
        conn.autocommit = True
        try:
            cur = conn.cursor()
            cur.execute("UPDATE content_posts SET status = 'UNPUBLISHED', retry_count = 0, last_error = NULL;")
            cur.execute("DELETE FROM instagram_publications;")
            cur.execute("DELETE FROM render_outputs;")
            cur.execute("DELETE FROM generated_metadata;")
            cur.execute("DELETE FROM post_runs;")
            cur.execute("DELETE FROM automation_runs;")
            cur.execute("DELETE FROM error_events;")
        finally:
            conn.close()


def get_state_store() -> Any:
    """
    State repository factory.
    Returns PostgresStateStore if STATE_BACKEND='postgres' or DB_HOST is set.
    Otherwise defaults to SQLiteStateStore as fallback.
    """
    backend = os.getenv("STATE_BACKEND", "").strip().lower()
    has_postgres_env = bool(os.getenv("DB_HOST", "").strip() and os.getenv("DB_PASSWORD", "").strip())

    if backend == "sqlite":
        logger.info("Using SQLiteStateStore backend (explicit STATE_BACKEND=sqlite).")
        return SQLiteStateStore()

    if backend == "postgres" or has_postgres_env:
        try:
            logger.info("Initializing PostgresStateStore backend...")
            return PostgresStateStore()
        except Exception as pe:
            logger.warning(f"Failed to initialize PostgresStateStore ({pe}). Falling back to SQLiteStateStore.")
            return SQLiteStateStore()

    logger.info("Using default SQLiteStateStore backend.")
    return SQLiteStateStore()


class StateStore:
    """Unified proxy class delegating to current state backend (Postgres or SQLite)."""
    
    def __init__(self, db_path: Optional[str] = None):
        backend = os.getenv("STATE_BACKEND", "").strip().lower()
        has_postgres_env = bool(os.getenv("DB_HOST", "").strip() and os.getenv("DB_PASSWORD", "").strip())

        if backend == "sqlite":
            self.impl = SQLiteStateStore(db_path)
        elif backend == "postgres" or has_postgres_env:
            try:
                self.impl = PostgresStateStore()
            except Exception:
                self.impl = SQLiteStateStore(db_path)
        else:
            self.impl = SQLiteStateStore(db_path)

    def get_next_post(self, *args, **kwargs):
        return self.impl.get_next_post(*args, **kwargs)

    def mark_rendered(self, *args, **kwargs):
        return self.impl.mark_rendered(*args, **kwargs)

    def mark_published(self, *args, **kwargs):
        return self.impl.mark_published(*args, **kwargs)

    def record_failure(self, *args, **kwargs):
        return self.impl.record_failure(*args, **kwargs)

    def get_post_state(self, *args, **kwargs):
        return self.impl.get_post_state(*args, **kwargs)

    def _get_connection(self, *args, **kwargs):
        if hasattr(self.impl, "_get_connection"):
            return self.impl._get_connection(*args, **kwargs)
        raise AttributeError("Current state backend does not expose _get_connection")

    def reset_state_for_testing(self, *args, **kwargs):
        return self.impl.reset_state_for_testing(*args, **kwargs)

