"""Project and version management API endpoints."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Header, UploadFile
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.entities import User
from ..schemas.project import ProjectCreate, ProjectDetailResponse, ProjectResponse, ProjectUpdate
from ..schemas.version import VersionUploadResponse
from ..services.auth_service import get_current_user
from ..services.project_service import ProjectService
from ..services.version_service import VersionService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new project (document family)."""
    p = ProjectService.create_project(db, current_user, project_in)
    return {
        "id": p.id,
        "user_id": p.user_id,
        "name": p.name,
        "description": p.description,
        "version_count": 0,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
    }


@router.get("", response_model=List[ProjectResponse])
def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all projects owned by the authenticated user."""
    return ProjectService.list_projects(db, current_user)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get project details including all uploaded versions."""
    return ProjectService.get_project_detail(db, current_user, project_id)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update project name or description."""
    p = ProjectService.update_project(db, current_user, project_id, project_in)
    return {
        "id": p.id,
        "user_id": p.user_id,
        "name": p.name,
        "description": p.description,
        "version_count": len(p.versions),
        "created_at": p.created_at,
        "updated_at": p.updated_at,
    }


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a project and its associated versions and diffs."""
    ProjectService.delete_project(db, current_user, project_id)
    return {"ok": True, "message": f"Project {project_id} deleted successfully."}


@router.get("/{project_id}/timeline")
def get_project_timeline(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve the multi-version temporal knowledge graph and chronological change timeline."""
    return ProjectService.get_timeline(db, current_user, project_id)


@router.post("/{project_id}/versions", response_model=VersionUploadResponse, status_code=202)
def upload_version(
    project_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    x_groq_api_key: Optional[str] = Header(None, alias="X-Groq-Api-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a new document version (.txt, .pdf, .docx) to trigger asynchronous extraction."""
    return VersionService.handle_version_upload(
        db, current_user, project_id, file, background_tasks, groq_api_key=x_groq_api_key
    )
