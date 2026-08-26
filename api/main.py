"""
MIROR Social Automation — T01 Production Renderer FastAPI Application
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request, status
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
from api.models import HealthResponse, RenderResponse, SlideOutputInfo, CanvasInfo
from api.errors import RendererAPIException, renderer_exception_handler

app = FastAPI(
    title="MIROR Social Automation T01 Renderer API",
    description="Production-grade API for deterministic T01 Instagram Carousel Rendering",
    version="1.0.0"
)

app.add_exception_handler(RendererAPIException, renderer_exception_handler)

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

def get_master_integrity_manifest() -> Dict[str, str]:
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

    manifest = body.get("text_integrity") or get_master_integrity_manifest()

    # 1. Enforce Exact Text Lock Validation across all 3 slides BEFORE rendering
    for slide in normalized_slides:
        s_id = slide.get("id") or slide.get("slide")
        try:
            TextLockSystem.validate_slide_payload(slide, manifest)
        except TextLockError as tle:
            raise RendererAPIException("TEXT_LOCK_FAILURE", str(tle), field=f"{s_id}")

    # 2. Render all 3 slides using T01HtmlRenderer
    renderer = T01HtmlRenderer(REPO_ROOT)
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
            raise RendererAPIException("RENDER_FAILURE", f"Rendering failed for {s_key}: {str(re)}", status_code=500)
        finally:
            if temp_json_path.exists():
                os.remove(temp_json_path)

        if not out_png_path.exists():
            raise RendererAPIException("OUTPUT_FAILURE", f"Output file not generated at {out_png_path}", status_code=500)

        # Store relative file path
        rel_file_path = (Path("output") / "renders" / str(post_id) / f"{post_id}_T01_{s_key}.png").as_posix()
        slide_outputs.append(SlideOutputInfo(slide=s_key, file=rel_file_path))

    return RenderResponse(
        success=True,
        post_id=str(post_id),
        template="T01",
        backgroundVariant=bg_variant,
        canvas=CanvasInfo(width=1080, height=1350),
        slides=slide_outputs
    )
