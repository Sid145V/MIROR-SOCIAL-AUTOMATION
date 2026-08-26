"""
MIROR T01 Renderer API — Storage Abstraction Layer
Provides clean interface for local file persistence and future cloud object storage adapters (S3, Cloud Storage).
"""

import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]

class StorageAdapter(ABC):
    @abstractmethod
    def save_file(self, local_src_path: str, post_id: str, slide_id: str) -> str:
        """Saves rendered slide output file and returns relative file key or storage path."""
        pass

    @abstractmethod
    def get_public_url(self, file_key: str) -> str:
        """Returns public URL or relative file path for access."""
        pass


class LocalStorageAdapter(StorageAdapter):
    """Local filesystem storage implementation for local development and container temporary workspace."""
    def __init__(self, base_output_dir: Optional[Path] = None):
        if base_output_dir is None:
            self.base_output_dir = REPO_ROOT / "output" / "renders"
        else:
            self.base_output_dir = Path(base_output_dir).resolve()

    def save_file(self, local_src_path: str, post_id: str, slide_id: str) -> str:
        src = Path(local_src_path).resolve()
        target_dir = self.base_output_dir / str(post_id)
        os.makedirs(target_dir, exist_ok=True)
        
        dest_filename = f"{post_id}_T01_{slide_id}.png"
        dest_path = target_dir / dest_filename
        
        if src != dest_path and src.exists():
            shutil.copy2(src, dest_path)
            
        rel_key = (Path("output") / "renders" / str(post_id) / dest_filename).as_posix()
        return rel_key

    def get_public_url(self, file_key: str) -> str:
        return file_key

def get_storage_adapter() -> StorageAdapter:
    """Factory function returning configured storage adapter based on environment."""
    storage_type = os.environ.get("MIROR_STORAGE_TYPE", "local").lower()
    if storage_type == "local":
        return LocalStorageAdapter()
    # Future production storage adapters (S3 / Cloud Storage) will be added here
    return LocalStorageAdapter()
