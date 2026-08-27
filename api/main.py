"""
MIROR Social Automation — T01 Production Renderer FastAPI Application
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, status, Query, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
core_dir = REPO_ROOT / "template-engine" / "core"
template_dir = REPO_ROOT / "template-engine" / "templates" / "T01-miror-text-carousel"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(core_dir) not in sys.path:
    sys.path.insert(0, str(core_dir))
if str(template_dir) not in sys.path:
    sys.path.insert(0, str(template_dir))

from text_lock import TextLockSystem, TextLockError
from renderer import T01HtmlRenderer
from api.models import (
    HealthResponse, RenderResponse, SlideOutputInfo, CanvasInfo,
    ContentNextResponse, PublishRequest, PublishResponse, PostStateResponse
)
from api.errors import RendererAPIException, renderer_exception_handler
from api.storage import get_storage_adapter
from api.state import StateStore, resolve_library_key, LIBRARY_CONFIG

logger = logging.getLogger("miror.api")

app = FastAPI(
    title="MIROR Social Automation T01 Renderer API",
    description="Production-grade API for deterministic T01 Instagram Carousel Rendering & Content Selection",
    version="1.1.0"
)

app.add_exception_handler(RendererAPIException, renderer_exception_handler)

# Initialize Post State Repository
state_store = StateStore()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "code": "SCHEMA_VALIDATION_ERROR",
                "message": "Malformed request payload or missing required fields.",
                "field": str(exc.errors()[0]["loc"][-1]) if exc.errors() else None
            }
        }
    )

def get_master_integrity_manifest(post_id: str = None) -> Dict[str, str]:
    if post_id:
        manifest_30_path = REPO_ROOT / "template-engine" / "data" / "text_integrity_manifest_30.json"
        if manifest_30_path.exists():
            with open(manifest_30_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
                if post_id in manifest_data:
                    return manifest_data[post_id]

        # Search all 3 production libraries for post_id's text_integrity manifest
        for lib_cfg in LIBRARY_CONFIG.values():
            if lib_cfg["file"].exists():
                with open(lib_cfg["file"], "r", encoding="utf-8") as f:
                    lib_data = json.load(f)
                    for p in lib_data.get("posts", []):
                        if p.get("content_id") == post_id and "text_integrity" in p:
                            return p["text_integrity"]

        return {}

    master_path = REPO_ROOT / "template-engine" / "tests" / "test_content_MIROR-T01-MASTER.json"
    if master_path.exists():
        with open(master_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("text_integrity", {})
    return {}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint. Returns service status without rendering."""
    return HealthResponse()

@app.get("/content/next", response_model=ContentNextResponse)
async def get_next_content(library: str = Query(..., description="Library name: master, symptoms_hormones, or supplements")):
    """
    Atomically selects the next unpublished/eligible post from the specified content library.
    Reserves the post for 30 minutes and returns the full render-ready payload with approved backgroundVariant.
    """
    canon_key = resolve_library_key(library)
    if not canon_key:
        raise RendererAPIException(
            code="INVALID_LIBRARY",
            message=f"Invalid library parameter '{library}'. Must be one of ['master', 'symptoms_hormones', 'supplements'].",
            field="library"
        )

    res = state_store.get_next_post(canon_key)
    if not res:
        raise RendererAPIException(
            code="LIBRARY_EXHAUSTED",
            message=f"No unpublished or eligible posts remaining in library '{canon_key}'.",
            status_code=404
        )

    content_id, canon_library, variant, post_payload = res

    return ContentNextResponse(
        success=True,
        library=canon_library,
        content_id=content_id,
        template_id=post_payload.get("template_id", "T01"),
        background_variant=variant,
        post=post_payload
    )

@app.post("/content/published", response_model=PublishResponse)
async def mark_content_published(request: PublishRequest):
    """
    Invoked by Make.com after successful Instagram publication.
    Updates the post state in the durable store to PUBLISHED.
    """
    try:
        res = state_store.mark_published(request.content_id, request.instagram_media_id)
        return PublishResponse(
            success=True,
            content_id=res["content_id"],
            status="PUBLISHED",
            published_at=res["published_at"],
            instagram_media_id=res["instagram_media_id"]
        )
    except KeyError as ke:
        raise RendererAPIException(
            code="INVALID_CONTENT_ID",
            message=str(ke),
            status_code=404,
            field="content_id"
        )

@app.get("/content/state/{content_id}", response_model=PostStateResponse)
async def get_content_state(content_id: str):
    """Returns the current durable state record for a given post ID."""
    st = state_store.get_post_state(content_id)
    if not st:
        raise RendererAPIException(
            code="CONTENT_ID_NOT_FOUND",
            message=f"Content ID '{content_id}' not found in state store.",
            status_code=404,
            field="content_id"
        )
    return PostStateResponse(
        success=True,
        content_id=st["content_id"],
        library=st["library"],
        status=st["status"],
        reserved_at=st["reserved_at"],
        rendered_at=st["rendered_at"],
        published_at=st["published_at"],
        instagram_media_id=st["instagram_media_id"],
        retry_count=st["retry_count"],
        last_error=st["last_error"]
    )

@app.post("/render", response_model=RenderResponse)
async def render_carousel(request: Request):
    """
    Accepts JSON payload for MIROR T01 carousel.
    Enforces Exact Text Lock & background variant validation before rendering 3 PNG slides.
    """
    try:
        body = await request.json()
    except Exception:
        raise RendererAPIException("SCHEMA_VALIDATION_ERROR", "Invalid or malformed JSON payload.")

    post_id = body.get("post_id") or body.get("content_id")
    if not post_id:
        raise RendererAPIException("VALIDATION_ERROR", "Missing required field 'post_id'.", field="post_id")

    template = body.get("template") or body.get("template_id")
    if not template:
        raise RendererAPIException("VALIDATION_ERROR", "Missing required field 'template'.", field="template")

    if template != "T01":
        raise RendererAPIException("UNSUPPORTED_TEMPLATE", "Only T01 is currently supported.", field="template")

    v_explicit = body.get("backgroundVariant") or body.get("variant")
    if v_explicit:
        v_str = str(v_explicit).zfill(2)
        if v_str not in ["01", "02", "03", "04", "05"]:
            raise RendererAPIException("BACKGROUND_VARIANT_ERROR", f"Invalid backgroundVariant '{v_explicit}'. Must be one of ['01', '02', '03', '04', '05'].", field="backgroundVariant")
        bg_variant = v_str
    else:
        bg_variant = "01"

    slides_raw = body.get("slides")
    if not slides_raw:
        raise RendererAPIException("VALIDATION_ERROR", "Missing required field 'slides'.", field="slides")

    # Normalize slides payload structure
    normalized_slides = []
    if isinstance(slides_raw, list):
        normalized_slides = slides_raw
    elif isinstance(slides_raw, dict):
        for s_id, s_data in slides_raw.items():
            s_dict = dict(s_data)
            s_dict["id"] = s_id
            normalized_slides.append(s_dict)
    else:
        raise RendererAPIException("SCHEMA_VALIDATION_ERROR", "'slides' must be a list or dictionary object.", field="slides")

    if len(normalized_slides) < 3:
        raise RendererAPIException("VALIDATION_ERROR", "T01 carousel requires 3 slides (S01, S02, S03).", field="slides")

    manifest = body.get("text_integrity") or get_master_integrity_manifest(str(post_id))

    # 1. Enforce Exact Text Lock Validation across all 3 slides BEFORE rendering
    for slide in normalized_slides:
        s_id = slide.get("id") or slide.get("slide")
        try:
            TextLockSystem.validate_slide_payload(slide, manifest)
        except TextLockError as tle:
            if state_store.get_post_state(str(post_id)):
                state_store.record_failure(str(post_id), f"TextLock error on {s_id}: {str(tle)}")
            raise RendererAPIException("TEXT_LOCK_FAILURE", str(tle), field=f"{s_id}")

    # 2. Render all 3 slides using T01HtmlRenderer
    renderer = T01HtmlRenderer(REPO_ROOT)
    storage = get_storage_adapter()
    output_dir = REPO_ROOT / "output" / "renders" / str(post_id)
    os.makedirs(output_dir, exist_ok=True)

    slide_outputs = []
    slide_keys = ["S01", "S02", "S03"]

    for idx, s_key in enumerate(slide_keys):
        target_slide = normalized_slides[idx]
        target_slide["backgroundVariant"] = bg_variant
        if "dayNumber" in body:
            target_slide["dayNumber"] = body["dayNumber"]

        temp_json_path = output_dir / f"temp_{post_id}_{s_key}.json"
        with open(temp_json_path, "w", encoding="utf-8") as f:
            json.dump(target_slide, f)

        out_png_path = output_dir / f"{post_id}_T01_{s_key}.png"

        try:
            renderer.render(str(temp_json_path), str(out_png_path), manifest)
        except Exception as re:
            if temp_json_path.exists():
                os.remove(temp_json_path)
            if state_store.get_post_state(str(post_id)):
                state_store.record_failure(str(post_id), f"Render failure on {s_key}: {str(re)}")
            raise RendererAPIException("RENDER_FAILURE", f"Rendering failed for {s_key}: {str(re)}", status_code=500)
        finally:
            if temp_json_path.exists():
                os.remove(temp_json_path)

        if not out_png_path.exists():
            if state_store.get_post_state(str(post_id)):
                state_store.record_failure(str(post_id), f"Output file missing: {out_png_path}")
            raise RendererAPIException("OUTPUT_FAILURE", f"Output file not generated at {out_png_path}", status_code=500)

        # Process through Storage Adapter (Local or Cloudinary)
        file_key, pub_url = storage.save_file(str(out_png_path), str(post_id), s_key)

        slide_outputs.append(SlideOutputInfo(slide=s_key, file=file_key, url=pub_url))

    # Safely update durable state store if post is tracked
    if state_store.get_post_state(str(post_id)):
        state_store.mark_rendered(str(post_id))

    return RenderResponse(
        success=True,
        post_id=str(post_id),
        template="T01",
        backgroundVariant=bg_variant,
        canvas=CanvasInfo(width=1080, height=1350),
        slides=slide_outputs
    )
