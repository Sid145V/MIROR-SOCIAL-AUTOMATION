"""
MIROR T01 Renderer API — Request & Response Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "miror-renderer"
    version: str = "1.0.0"

class CanvasInfo(BaseModel):
    width: int = 1080
    height: int = 1350

class SlideOutputInfo(BaseModel):
    slide: str
    file: str

class RenderResponse(BaseModel):
    success: bool = True
    post_id: str
    template: str
    backgroundVariant: str
    canvas: CanvasInfo = Field(default_factory=CanvasInfo)
    slides: List[SlideOutputInfo]
