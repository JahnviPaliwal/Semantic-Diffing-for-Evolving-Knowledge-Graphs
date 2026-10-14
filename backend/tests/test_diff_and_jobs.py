"""Tests for document upload, background extraction jobs, and diff computation."""
import io
from unittest.mock import MagicMock

import pytest

from backend.app.models.entities import Version
from src.semantic_diff.models import ExtractedEntity, ExtractedRelation, ExtractionResult


def test_version_upload_enqueues_job(client, auth_headers):
    # 1. Create project
    p_resp = client.post("/api/projects", json={"name": "Upload Project"}, headers=auth_headers)
    proj_id = p_resp.json()["id"]

    # 2. Upload file
    file_content = b"Acme Corporation is led by CEO John Smith in San Francisco."
    files = {"file": ("doc_v1.txt", io.BytesIO(file_content), "text/plain")}
    up_resp = client.post(f"/api/projects/{proj_id}/versions", files=files, headers=auth_headers)

    assert up_resp.status_code == 202
    data = up_resp.json()
    assert "job_id" in data
    job_id = data["job_id"]

    # 3. Poll job status
    job_resp = client.get(f"/api/jobs/{job_id}", headers=auth_headers)
    assert job_resp.status_code == 200
    assert job_resp.json()["id"] == job_id
    assert job_resp.json()["status"] in ("queued", "processing", "completed")


def test_diff_computation_and_export(client, auth_headers):
    # Setup project with two pre-populated version records
    p_resp = client.post("/api/projects", json={"name": "Diff Test Project"}, headers=auth_headers)
    proj_id = p_resp.json()["id"]

    v1_ext = ExtractionResult(
        version_id="v1",
        doc_hash="hash_1",
        entities=[
            ExtractedEntity(name="Acme Corp", type="Organization", source_quote="Acme Corp operates"),
            ExtractedEntity(name="DataSync Platform", type="Product", source_quote="DataSync Platform"),
            ExtractedEntity(name="California", type="Location", source_quote="laws of California"),
        ],
        relations=[
            ExtractedRelation(subject="Acme Corp", predicate="develops", object="DataSync Platform", source_quote="Acme Corp develops DataSync"),
        ],
    )

    v2_ext = ExtractionResult(
        version_id="v2",
        doc_hash="hash_2",
        entities=[
            ExtractedEntity(name="Acme Corp", type="Organization", source_quote="Acme Corp"),
            ExtractedEntity(name="AcmeSync", type="Product", source_quote="DataSync Platform was rebranded as AcmeSync"),
            ExtractedEntity(name="Delaware", type="Location", source_quote="laws of Delaware"),
            ExtractedEntity(name="AI Lab", type="Department", source_quote="launched AI Lab"),
        ],
        relations=[
            ExtractedRelation(subject="Acme Corp", predicate="develops", object="AcmeSync", source_quote="develops AcmeSync"),
        ],
    )

    # Insert versions directly into test DB session
    from backend.tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    v1 = Version(
        project_id=proj_id,
        version_num=1,
        version_label="v1",
        filename="v1.txt",
        doc_hash="hash_1",
        extracted_graph=v1_ext.model_dump(),
        status="completed",
    )
    v2 = Version(
        project_id=proj_id,
        version_num=2,
        version_label="v2",
        filename="v2.txt",
        doc_hash="hash_2",
        extracted_graph=v2_ext.model_dump(),
        status="completed",
    )
    db.add(v1)
    db.add(v2)
    db.commit()
    v1_id = v1.id
    v2_id = v2.id
    db.close()

    # Compute Diff
    diff_resp = client.post(
        f"/api/projects/{proj_id}/diff",
        json={"from_version_id": v1_id, "to_version_id": v2_id},
        headers=auth_headers,
    )
    assert diff_resp.status_code == 200
    diff_data = diff_resp.json()
    assert diff_data["from_version_label"] == "v1"
    assert diff_data["to_version_label"] == "v2"
    assert "AI Lab" in diff_data["changes"]["added_entities"]
    diff_id = diff_data["id"]

    # Export Diff as JSON
    exp_json = client.get(f"/api/projects/{proj_id}/diff/{diff_id}/export?format=json", headers=auth_headers)
    assert exp_json.status_code == 200
    assert exp_json.json()["format"] == "json"
    assert "diff_v1_to_v2.json" in exp_json.json()["filename"]

    # Export Diff as CSV
    exp_csv = client.get(f"/api/projects/{proj_id}/diff/{diff_id}/export?format=csv", headers=auth_headers)
    assert exp_csv.status_code == 200
    assert exp_csv.json()["format"] == "csv"
    assert "Element Type,Change Type,Canonical Name" in exp_csv.json()["content"]


def test_ephemeral_groq_api_key_header_and_zero_db_persistence(client, auth_headers):
    """Verify that user-supplied Groq API keys via X-Groq-Api-Key header are never written to the DB."""
    from backend.app.models.entities import DiffResultModel, Job, Version
    from backend.tests.conftest import TestingSessionLocal

    ephemeral_key = "gsk_user_ephemeral_secret_999888777"
    custom_headers = {**auth_headers, "X-Groq-Api-Key": ephemeral_key}

    # 1. Create project
    p_resp = client.post("/api/projects", json={"name": "Ephemeral Key Test Project"}, headers=auth_headers)
    assert p_resp.status_code == 201
    proj_id = p_resp.json()["id"]

    # 2. Upload file with ephemeral key header
    file_bytes = b"NovaTech Inc. is based in Delaware and develops CloudSync Platform."
    files = {"file": ("doc_v1.txt", io.BytesIO(file_bytes), "text/plain")}
    up_resp = client.post(
        f"/api/projects/{proj_id}/versions",
        files=files,
        headers=custom_headers,
    )
    assert up_resp.status_code == 202
    job_id = up_resp.json()["job_id"]

    # 3. Verify Database: Ensure ephemeral key was NEVER written to the database
    db = TestingSessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        assert job is not None
        # String representation or json dump must never contain the secret key
        job_dump = str(job.__dict__)
        assert ephemeral_key not in job_dump

        # 4. Insert versions to test diff with ephemeral key
        v1 = Version(
            project_id=proj_id,
            version_num=1,
            version_label="v1",
            filename="v1.txt",
            doc_hash="hash_alpha",
            extracted_graph={"version_id": "v1", "doc_hash": "hash_alpha", "entities": [{"name": "NovaTech", "type": "Organization", "source_quote": "NovaTech"}], "relations": []},
            status="completed",
        )
        v2 = Version(
            project_id=proj_id,
            version_num=2,
            version_label="v2",
            filename="v2.txt",
            doc_hash="hash_beta",
            extracted_graph={"version_id": "v2", "doc_hash": "hash_beta", "entities": [{"name": "NovaTech", "type": "Organization", "source_quote": "NovaTech"}, {"name": "CloudSync", "type": "Product", "source_quote": "CloudSync"}], "relations": []},
            status="completed",
        )
        db.add(v1)
        db.add(v2)
        db.commit()
        v1_id, v2_id = v1.id, v2.id

        # 5. Compute diff with ephemeral key
        diff_resp = client.post(
            f"/api/projects/{proj_id}/diff",
            json={"from_version_id": v1_id, "to_version_id": v2_id},
            headers=custom_headers,
        )
        assert diff_resp.status_code == 200
        diff_id = diff_resp.json()["id"]

        # 6. Verify Diff record in DB never stored the key
        diff_row = db.query(DiffResultModel).filter(DiffResultModel.id == diff_id).first()
        assert diff_row is not None
        diff_dump = str(diff_row.__dict__)
        assert ephemeral_key not in diff_dump
    finally:
        db.close()

