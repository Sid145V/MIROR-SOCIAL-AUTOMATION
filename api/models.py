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
    file: Optional[str] = None
    url: Optional[str] = None

class RenderResponse(BaseModel):
    success: bool = True
    post_id: str
    template: str
    backgroundVariant: str
    canvas: CanvasInfo = Field(default_factory=CanvasInfo)
    slides: List[SlideOutputInfo]

class ContentNextResponse(BaseModel):
    success: bool = True
    library: str
    content_id: str
    template_id: str = "T01"
    background_variant: str
    post: Dict[str, Any]

class PublishRequest(BaseModel):
    content_id: str = Field(..., description="Unique Content ID to mark published")
    instagram_media_id: Optional[str] = Field(None, description="Optional Instagram Media ID returned by Meta API")

class PublishResponse(BaseModel):
    success: bool = True
    content_id: str
    status: str = "PUBLISHED"
    published_at: Optional[str] = None
    instagram_media_id: Optional[str] = None

class PostStateResponse(BaseModel):
    success: bool = True
    content_id: str
    library: str
    status: str
    reserved_at: Optional[str] = None
    rendered_at: Optional[str] = None
    published_at: Optional[str] = None
    instagram_media_id: Optional[str] = None
    retry_count: int = 0
    last_error: Optional[str] = None
