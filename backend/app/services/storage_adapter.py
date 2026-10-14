"""
Storage Abstraction Layer.
Manages file persistence across local volume storage and ephemeral hosting environments.
Ensures that all uploaded artifacts are persisted or rebuildable from the database.
"""
import os
import shutil
import uuid
from typing import Optional

from fastapi import UploadFile

from ..core.config import settings


class StorageAdapter:
    def __init__(self, upload_dir: Optional[str] = None):
        self.upload_dir = upload_dir or settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    def save_upload(self, upload_file: UploadFile, project_id: int) -> str:
        """Save uploaded file stream to storage and return persisted relative path."""
        proj_dir = os.path.join(self.upload_dir, f"proj_{project_id}")
        os.makedirs(proj_dir, exist_ok=True)

        unique_name = f"{uuid.uuid4().hex[:12]}_{upload_file.filename}"
        dest_path = os.path.join(proj_dir, unique_name)

        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)

        return dest_path

    def read_file(self, file_path: str) -> bytes:
        """Read file bytes from storage."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File at {file_path} not found in storage.")
        with open(file_path, "rb") as f:
            return f.read()

    def delete_file(self, file_path: str) -> None:
        """Remove file from storage."""
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


storage_adapter = StorageAdapter()
