"""
Entrypoint for Vercel Services Python / FastAPI backend runtime.
Exposes 'app' ASGI application instance from app.main.
"""
import os
import sys
from pathlib import Path

# Add repository root and backend to sys.path
BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent

for p in [str(REPO_ROOT), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("VERCEL", "1")
os.environ.setdefault("DISABLE_HEAVY_EMBEDDINGS", "1")

if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:////tmp/app.db"

if "UPLOAD_DIR" not in os.environ:
    os.environ["UPLOAD_DIR"] = "/tmp/uploads"

from app.main import app
