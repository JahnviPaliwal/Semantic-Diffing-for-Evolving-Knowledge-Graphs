"""
Background job service providing state polling and real-time Server-Sent Events (SSE) streaming.
"""
import asyncio
import json
import logging
from typing import AsyncGenerator

from sqlalchemy.orm import Session

from ..core.database import SessionLocal
from ..core.exceptions import ForbiddenException, NotFoundException
from ..models.entities import Job, User
from ..schemas.job import JobResponse

logger = logging.getLogger(__name__)


class JobService:
    @staticmethod
    def get_job_with_ownership(db: Session, job_id: str, user: User) -> Job:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise NotFoundException(f"Job with ID '{job_id}' not found.")
        if job.user_id != user.id and not user.is_superuser:
            raise ForbiddenException("You do not have permission to view this job.")
        return job

    @staticmethod
    async def stream_job_progress(job_id: str, user_id: int) -> AsyncGenerator[str, None]:
        """SSE event generator emitting updates until job finishes or times out."""
        last_progress = -1
        last_stage = ""

        # Timeout after 5 minutes
        max_polls = 600
        for _ in range(max_polls):
            db: Session = SessionLocal()
            try:
                job = db.query(Job).filter(Job.id == job_id).first()
                if not job:
                    yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                    break

                if job.user_id != user_id:
                    yield f"data: {json.dumps({'error': 'Unauthorized'})}\n\n"
                    break

                # Emit if state changed
                if job.progress != last_progress or job.stage != last_stage or job.status in ("completed", "failed"):
                    last_progress = job.progress
                    last_stage = job.stage
                    payload = JobResponse.model_validate(job).model_dump(mode="json")
                    yield f"data: {json.dumps(payload)}\n\n"

                if job.status in ("completed", "failed"):
                    break
            finally:
                db.close()

            await asyncio.sleep(0.5)
