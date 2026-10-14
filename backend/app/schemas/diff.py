"""Pydantic schemas for diffing and export."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DiffRequest(BaseModel):
    from_version_id: int = Field(..., description="Source baseline version ID")
    to_version_id: int = Field(..., description="Target updated version ID")


class DiffItemSchema(BaseModel):
    element_type: str
    change_type: str
    canonical_name: str
    previous_name: Optional[str] = None
    source_quote: Optional[str] = ""
    chunk_reference: Optional[str] = ""
    confidence: float = 1.0
    severity: str = "LOW"
    rationale: Optional[str] = ""


class DiffResponse(BaseModel):
    id: int
    project_id: int
    from_version_id: int
    to_version_id: int
    from_version_label: str = ""
    to_version_label: str = ""
    changes: Dict[str, Any]
    severity_summary: Dict[str, int]
    narrative: Optional[str] = ""
    created_at: datetime

    class Config:
        from_attributes = True


class DiffExportResponse(BaseModel):
    format: str
    filename: str
    content: str
