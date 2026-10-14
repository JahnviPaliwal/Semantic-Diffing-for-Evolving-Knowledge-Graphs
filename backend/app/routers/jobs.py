"""Background jobs status and SSE progress streaming endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.exceptions import UnauthorizedException
from ..core.security import decode_token
from ..models.entities import User
from ..schemas.job import JobResponse
from ..services.auth_service import get_current_user
from ..services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Poll the status and progress of a background extraction or analysis job."""
    return JobService.get_job_with_ownership(db, job_id, current_user)


@router.get("/{job_id}/events")
@router.get("/{job_id}/stream")
async def stream_job_progress(
    job_id: str,
    token: Optional[str] = Query(None, description="Optional bearer token for EventSource compatibility"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Subscribe to real-time Server-Sent Events (SSE) progress updates for a background job.
    Survives page refreshes and emits updates until job completion.
    """
    # Authenticate via header or query token
    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split(" ")[1]
    elif token:
        auth_token = token

    if not auth_token:
        raise UnauthorizedException("Authentication token required for SSE stream.")

    payload = decode_token(auth_token)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedException("Invalid or expired token.")

    user_id = int(payload.get("sub", 0))

    return StreamingResponse(
        JobService.stream_job_progress(job_id, user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
