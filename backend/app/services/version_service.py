"""
Version service handling document upload, validation, and background extraction job dispatch.
"""
import logging
import os
import uuid
from typing import Any, Dict, Optional

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.orm import Session

from src.semantic_diff.extraction import ExtractionManager

from ..core.config import settings
from ..core.database import SessionLocal
from ..core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from ..models.entities import Job, Project, User, Version
from ..schemas.version import VersionResponse, VersionUploadResponse
from .project_service import ProjectService
from .storage_adapter import storage_adapter

logger = logging.getLogger(__name__)


def run_extraction_worker(
    job_id: str,
    project_id: int,
    file_path: str,
    filename: str,
    groq_api_key: Optional[str] = None,
) -> None:
    """Background worker executing text extraction and KG construction."""
    db: Session = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        # 1. Parsing text
        job.status = "processing"
        job.progress = 25
        job.stage = "Parsing document content"
        db.commit()

        # In-memory ephemeral key passed directly to extractor; NEVER saved to DB
        extractor = ExtractionManager(api_key=groq_api_key)
        text = extractor.extract_text_from_file(file_path)

        if not text or not text.strip():
            job.status = "failed"
            job.error_message = "Uploaded document contains no extractable text."
            job.stage = "Failed"
            db.commit()
            return

        # 2. Extracting KG
        job.progress = 55
        job.stage = "Extracting entities & relations via LLM"
        db.commit()

        # Determine version number & label
        existing_versions = db.query(Version).filter(Version.project_id == project_id).count()
        v_num = existing_versions + 1
        v_label = f"v{v_num}"

        extraction = extractor.extract_from_text(text, version_id=v_label)

        # 3. Persisting to Database
        job.progress = 85
        job.stage = "Persisting knowledge graph snapshot"
        db.commit()

        version_record = Version(
            project_id=project_id,
            version_num=v_num,
            version_label=v_label,
            filename=filename,
            file_path=file_path,
            doc_hash=extraction.doc_hash,
            extracted_graph=extraction.model_dump(),
            status="completed",
        )
        db.add(version_record)
        db.commit()
        db.refresh(version_record)

        # 4. Complete Job
        job.status = "completed"
        job.progress = 100
        job.stage = "Finished"
        job.result = {
            "version_id": version_record.id,
            "version_label": version_record.version_label,
            "entities_count": len(extraction.entities),
            "relations_count": len(extraction.relations),
            "doc_hash": extraction.doc_hash,
        }
        db.commit()
        logger.info(f"Job {job_id} completed successfully for version {v_label}.")

    except Exception as e:
        logger.error(f"Error in extraction worker for job {job_id}: {e}", exc_info=True)
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = "failed"
                job.progress = 100
                job.stage = "Failed"
                job.error_message = str(e)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


class VersionService:
    @classmethod
    def handle_version_upload(
        cls,
        db: Session,
        user: User,
        project_id: int,
        file: UploadFile,
        background_tasks: BackgroundTasks,
        groq_api_key: Optional[str] = None,
    ) -> VersionUploadResponse:
        # Validate project ownership
        ProjectService.get_project_with_ownership(db, project_id, user)

        filename = file.filename or "uploaded_document.txt"
        ext = os.path.splitext(filename)[1].lower()

        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            raise BadRequestException(
                f"Unsupported file format '{ext}'. Allowed extensions: {', '.join(settings.ALLOWED_UPLOAD_EXTENSIONS)}"
            )

        # Persist uploaded file to storage abstraction
        saved_path = storage_adapter.save_upload(file, project_id=project_id)

        # Create persistent Job row (Notice: API key is NEVER stored here or in DB)
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            user_id=user.id,
            project_id=project_id,
            type="extraction",
            status="queued",
            progress=0,
            stage="Queued for processing",
        )
        db.add(job)
        db.commit()

        # Enqueue background task with in-memory groq_api_key
        background_tasks.add_task(
            run_extraction_worker, job_id, project_id, saved_path, filename, groq_api_key=groq_api_key
        )

        return VersionUploadResponse(
            job_id=job_id,
            message="Version upload queued for processing. Subscribe to SSE or poll for status.",
        )
