"""
Pytest configuration for backend API tests.
Uses an in-memory SQLite database and mocked LLM/embedding clients.
"""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-runs-2026"
os.environ["DISABLE_HEAVY_EMBEDDINGS"] = "1"

from backend.app.core.database import Base, get_db
from backend.app.main import app
from backend.app.models.entities import DiffResultModel, Job, Project, User, Version

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "test.db")
os.makedirs(os.path.dirname(os.path.abspath(TEST_DB_PATH)), exist_ok=True)
TEST_DB_URL = f"sqlite:///{os.path.abspath(TEST_DB_PATH)}"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Register and login a test user, returning authorization headers."""
    client.post("/api/auth/register", json={"email": "tester@example.com", "password": "password123"})
    resp = client.post("/api/auth/login", json={"email": "tester@example.com", "password": "password123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_user_headers(client):
    """Register and login a secondary test user for ownership validation."""
    client.post("/api/auth/register", json={"email": "other@example.com", "password": "password123"})
    resp = client.post("/api/auth/login", json={"email": "other@example.com", "password": "password123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
