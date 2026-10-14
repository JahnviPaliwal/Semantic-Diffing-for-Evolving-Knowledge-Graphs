"""Pydantic schemas for document versions."""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class VersionResponse(BaseModel):
    id: int
    project_id: int
    version_num: int
    version_label: str
    filename: str
    doc_hash: str
    status: str
    node_count: int = 0
    edge_count: int = 0
    created_at: datetime
    extracted_graph: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class VersionUploadResponse(BaseModel):
    job_id: str
    version_id: Optional[int] = None
    message: str
