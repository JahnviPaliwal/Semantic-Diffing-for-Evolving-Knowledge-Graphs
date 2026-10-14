"""Pydantic schemas for background job status and progress tracking."""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class JobResponse(BaseModel):
    id: str
    type: str
    status: str
    progress: int
    stage: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
