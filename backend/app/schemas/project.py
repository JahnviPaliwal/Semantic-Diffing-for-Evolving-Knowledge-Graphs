"""Pydantic schemas for projects (document families)."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .version import VersionResponse


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Project document family name")
    description: Optional[str] = Field(default=None, description="Optional project description")


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    version_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    versions: List[VersionResponse] = []
