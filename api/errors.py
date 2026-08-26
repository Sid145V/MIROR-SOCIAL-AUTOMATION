"""
MIROR T01 Renderer API — Structured Error Definitions & Handlers
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

class APIErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None

class APIErrorResponse(BaseModel):
    success: bool = False
    error: APIErrorDetail

class RendererAPIException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, field: Optional[str] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.field = field

async def renderer_exception_handler(request: Request, exc: RendererAPIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "field": exc.field
            }
        }
    )
