"""
MIROR T01 Renderer API — Storage Abstraction Layer
Provides clean interface for local file persistence and Cloudinary persistent image storage.
"""

import os
import sys
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]

# Add core module directory to sys.path for custom error handling
core_dir = REPO_ROOT / "template-engine" / "core"
if str(core_dir) not in sys.path:
    sys.path.insert(0, str(core_dir))

from api.errors import RendererAPIException

class StorageAdapter(ABC):
    @abstractmethod
    def save_file(self, local_src_path: str, post_id: str, slide_id: str) -> Tuple[str, Optional[str]]:
        """
        Saves rendered slide output file.
        Returns a tuple: (file_key_or_path, public_https_url_or_none)
        """
        pass


class LocalStorageAdapter(StorageAdapter):
    """Local filesystem storage implementation for local development and container temporary workspace."""
    def __init__(self, base_output_dir: Optional[Path] = None):
        if base_output_dir is None:
            self.base_output_dir = REPO_ROOT / "output" / "renders"
        else:
            self.base_output_dir = Path(base_output_dir).resolve()

    def save_file(self, local_src_path: str, post_id: str, slide_id: str) -> Tuple[str, Optional[str]]:
        src = Path(local_src_path).resolve()
        target_dir = self.base_output_dir / str(post_id)
        os.makedirs(target_dir, exist_ok=True)
        
        dest_filename = f"{post_id}_T01_{slide_id}.png"
        dest_path = target_dir / dest_filename
        
        if src != dest_path and src.exists():
            shutil.copy2(src, dest_path)
            
        rel_key = (Path("output") / "renders" / str(post_id) / dest_filename).as_posix()
        return rel_key, None


class CloudinaryStorageAdapter(StorageAdapter):
    """Cloudinary persistent image storage implementation for production CDN delivery."""
    def __init__(self):
        self.cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME")
        self.api_key = os.environ.get("CLOUDINARY_API_KEY")
        self.api_secret = os.environ.get("CLOUDINARY_API_SECRET")
        self.cloudinary_url = os.environ.get("CLOUDINARY_URL")

    def _ensure_configured(self):
        if not (self.cloud_name and self.api_key and self.api_secret) and self.cloudinary_url:
            from urllib.parse import urlparse
            parsed = urlparse(self.cloudinary_url)
            if parsed.hostname:
                self.cloud_name = parsed.hostname
            if parsed.username:
                self.api_key = parsed.username
            if parsed.password:
                self.api_secret = parsed.password

        if not (self.cloud_name and self.api_key and self.api_secret):
            raise RendererAPIException(
                code="STORAGE_UPLOAD_FAILURE",
                message="Cloudinary storage backend selected but required credentials (CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET or CLOUDINARY_URL) are missing."
            )
        try:
            import cloudinary
            cloudinary.config(
                cloud_name=self.cloud_name,
                api_key=self.api_key,
                api_secret=self.api_secret,
                secure=True
            )
        except Exception:
            raise RendererAPIException(
                code="STORAGE_UPLOAD_FAILURE",
                message="Failed to initialize Cloudinary SDK configuration."
            )

    def save_file(self, local_src_path: str, post_id: str, slide_id: str) -> Tuple[str, Optional[str]]:
        self._ensure_configured()

        src = Path(local_src_path).resolve()
        if not src.exists():
            raise RendererAPIException(
                code="STORAGE_UPLOAD_FAILURE",
                message=f"Local rendered file not found for upload: {src.name}"
            )

        # First save to local output directory for local record
        local_adapter = LocalStorageAdapter()
        rel_key, _ = local_adapter.save_file(local_src_path, post_id, slide_id)

        try:
            import cloudinary.uploader
            folder_path = f"MIROR/social-automation/{post_id}"
            public_id = f"{post_id}_T01_{slide_id}"

            upload_result = cloudinary.uploader.upload(
                str(src),
                folder=folder_path,
                public_id=public_id,
                overwrite=True,
                resource_type="image",
                format="png"
            )

            secure_url = upload_result.get("secure_url") or upload_result.get("url")
            if not secure_url:
                raise ValueError("Cloudinary upload did not return a valid secure URL.")

            return rel_key, secure_url

        except RendererAPIException:
            raise
        except Exception as e:
            # Log error server-side without exposing API keys
            print(f"[ERROR] Cloudinary upload failure for {post_id} {slide_id}: {str(e)}")
            raise RendererAPIException(
                code="STORAGE_UPLOAD_FAILURE",
                message="Unable to persist rendered asset to Cloudinary CDN storage."
            )


def get_storage_adapter() -> StorageAdapter:
    """Factory function returning configured storage adapter based on STORAGE_BACKEND env var."""
    backend = os.environ.get("STORAGE_BACKEND", os.environ.get("MIROR_STORAGE_TYPE", "local")).lower()
    if backend == "cloudinary":
        return CloudinaryStorageAdapter()
    return LocalStorageAdapter()
