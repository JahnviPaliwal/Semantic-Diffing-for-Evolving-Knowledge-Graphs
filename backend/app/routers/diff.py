"""Diff computation and export API endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.entities import User
from ..schemas.diff import DiffExportResponse, DiffRequest, DiffResponse
from ..services.auth_service import get_current_user
from ..services.diff_service import DiffService

router = APIRouter(prefix="/projects", tags=["Semantic Diffing"])


@router.post("/{project_id}/diff", response_model=DiffResponse)
def compute_diff(
    project_id: int,
    diff_in: DiffRequest,
    x_groq_api_key: Optional[str] = Header(None, alias="X-Groq-Api-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compute rich semantic diff between two document versions with severity scoring."""
    return DiffService.compute_diff(
        db=db,
        user=current_user,
        project_id=project_id,
        from_version_id=diff_in.from_version_id,
        to_version_id=diff_in.to_version_id,
        groq_api_key=x_groq_api_key,
    )


@router.get("/{project_id}/diff/{diff_id}", response_model=DiffResponse)
def get_diff(
    project_id: int,
    diff_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve an existing diff result by ID."""
    return DiffService.get_diff(db=db, user=current_user, project_id=project_id, diff_id=diff_id)


@router.get("/{project_id}/diff/{diff_id}/export", response_model=DiffExportResponse)
def export_diff(
    project_id: int,
    diff_id: int,
    format: str = Query("json", pattern="^(json|csv)$", description="Export format: json or csv"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export diff with verbatim source quotes as structured JSON or CSV."""
    return DiffService.export_diff(
        db=db,
        user=current_user,
        project_id=project_id,
        diff_id=diff_id,
        export_format=format,
    )
