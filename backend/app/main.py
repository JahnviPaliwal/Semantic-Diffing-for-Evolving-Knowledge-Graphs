"""
FastAPI application entrypoint for Semantic Knowledge Graph Diff API.
Configures CORS, middlewares, rate limiting, exception handling, and API routers.
"""
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure repository root is on sys.path so 'src' can always be imported regardless of cwd
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from .core.database import Base, engine
from .core.exceptions import register_exception_handlers
from .core.middleware import RequestContextMiddleware, limiter
from .routers import auth, diff, health, jobs, projects
from .routers import eval as eval_router

# Setup root logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"Initializing {settings.PROJECT_NAME} v{settings.VERSION}...")
    # Ensure database tables exist (SQLite or initial bootstrap)
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema validated.")
    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Knowledge graph extraction, hybrid entity resolution, temporal graphs, and semantic diffing.",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# 1. State & Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 2. Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time-Ms"],
)
app.add_middleware(RequestContextMiddleware)

# 3. Exception handlers
register_exception_handlers(app)

# 4. Routers (mount under both /api and /api/v1 for seamless compatibility)
app.include_router(health.router)
for prefix in ["/api", "/api/v1"]:
    app.include_router(health.router, prefix=prefix)
    app.include_router(auth.router, prefix=prefix)
    app.include_router(projects.router, prefix=prefix)
    app.include_router(diff.router, prefix=prefix)
    app.include_router(jobs.router, prefix=prefix)
    app.include_router(eval_router.router, prefix=prefix)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
