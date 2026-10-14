"""Health and readiness probe API endpoints."""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """Liveness probe: verifies that the FastAPI process is running."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe: validates connectivity to the underlying database."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "database": "connected",
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
            },
        )
