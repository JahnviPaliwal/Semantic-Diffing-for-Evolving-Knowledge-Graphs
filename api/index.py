"""
Vercel Serverless Function Entrypoint for FastAPI Backend.
Exposes 'app' for ASGI execution on Vercel's Python runtime.
Ensures repository root and backend package are in sys.path,
configures serverless-compatible writable /tmp paths, and includes
path-correction middleware for Vercel edge proxy routing.
"""
import os
import sys
from pathlib import Path

# 1. Resolve directory paths and inject into sys.path
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent
BACKEND_DIR = REPO_ROOT / "backend"

for path in [str(REPO_ROOT), str(BACKEND_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

# 2. Flag Vercel serverless environment before importing application modules
os.environ["VERCEL"] = "1"
os.environ["DISABLE_HEAVY_EMBEDDINGS"] = "1"

if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:////tmp/app.db"

if "UPLOAD_DIR" not in os.environ:
    os.environ["UPLOAD_DIR"] = "/tmp/uploads"

# 3. Import FastAPI application
from backend.app.main import app as fastapi_app


# 4. Pure ASGI Middleware to normalize Vercel proxy rewrite paths
class VercelPathCorrectionMiddleware:
    """
    Normalizes ASGI scope['path'] when Vercel rewrites requests to /api/index.py.
    Reads 'x-matched-path' or 'x-forwarded-uri' headers so FastAPI router
    matches the original client requested endpoint seamlessly.
    """
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            current_path = scope.get("path", "")
            # Check if Vercel passed the rewrite target instead of the original request path
            if current_path in ("/api/index.py", "/api/index", "/api", "") or not current_path.startswith("/api"):
                raw_headers = dict(scope.get("headers", []))
                # Check headers injected by Vercel edge proxy
                matched = raw_headers.get(b"x-matched-path", b"").decode("latin-1")
                if not matched:
                    matched = raw_headers.get(b"x-forwarded-uri", b"").decode("latin-1")

                if matched and matched not in ("/api/index.py", "/api/index"):
                    # Strip query parameters if present in the matched header
                    scope["path"] = matched.split("?")[0]

        await self.asgi_app(scope, receive, send)


app = VercelPathCorrectionMiddleware(fastapi_app)
