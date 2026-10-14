"""
Shared pytest fixtures and mock test doubles.
Mocking LLM and embedding calls per COMMON STANDARDS.
"""
from unittest.mock import MagicMock

import numpy as np
import pytest

from src.semantic_diff.models import ExtractedEntity, ExtractedRelation, ExtractionResult


class MockEmbeddingModel:
    def encode(self, texts, normalize_embeddings=True):
        vecs = []
        for t in texts:
            # Deterministic pseudo-embedding based on character tokens
            seed = sum(ord(c) for c in t.lower()) % 1000
            np.random.seed(seed)
            v = np.random.randn(64).astype(np.float32)
            if normalize_embeddings:
                norm = np.linalg.norm(v)
                if norm > 0:
                    v = v / norm
            vecs.append(v)
        return np.array(vecs)


@pytest.fixture(autouse=True)
def mock_embeddings(monkeypatch):
    """Ensure tests run offline and fast without downloading huggingface models."""
    mock_model = MockEmbeddingModel()
    monkeypatch.setattr("src.semantic_diff.resolution.get_embedding_model", lambda: mock_model)
    return mock_model


@pytest.fixture
def sample_v1_extraction():
    return ExtractionResult(
        version_id="v1",
        doc_hash="hash_v1_test",
        raw_text="Acme Corporation is led by CEO John Smith. It operates a Cloud Division. The DataSync Platform is the main product.",
        entities=[
            ExtractedEntity(name="Acme Corporation", type="Organization", source_quote="Acme Corporation is led by CEO John Smith"),
            ExtractedEntity(name="John Smith", type="Person", source_quote="CEO John Smith"),
            ExtractedEntity(name="Cloud Division", type="Department", source_quote="operates a Cloud Division"),
            ExtractedEntity(name="Legacy Systems Department", type="Department", source_quote="Legacy Systems Department"),
            ExtractedEntity(name="DataSync Platform", type="Product", source_quote="DataSync Platform is the main product"),
            ExtractedEntity(name="AWS", type="Organization", source_quote="partnerships with AWS"),
        ],
        relations=[
            ExtractedRelation(subject="Acme Corporation", predicate="led by", object="John Smith", source_quote="led by CEO John Smith"),
            ExtractedRelation(subject="Acme Corporation", predicate="operates", object="Cloud Division", source_quote="operates a Cloud Division"),
            ExtractedRelation(subject="Acme Corporation", predicate="operates", object="Legacy Systems Department", source_quote="operates a Legacy Systems Department"),
            ExtractedRelation(subject="Cloud Division", predicate="partners with", object="AWS", source_quote="Cloud Division partners with AWS"),
        ],
    )


@pytest.fixture
def sample_v2_extraction():
    return ExtractionResult(
        version_id="v2",
        doc_hash="hash_v2_test",
        raw_text="Acme Corporation is led by CEO Jane Doe. It launched an AI Research Division. The Cloud Division now partners exclusively with AWS. DataSync was rebranded as AcmeSync.",
        entities=[
            ExtractedEntity(name="Acme Corporation", type="Organization", source_quote="Acme Corporation is led by CEO Jane Doe"),
            ExtractedEntity(name="Jane Doe", type="Person", source_quote="CEO Jane Doe"),
            ExtractedEntity(name="Cloud Division", type="Department", source_quote="Cloud Division"),
            ExtractedEntity(name="AI Research Division", type="Department", source_quote="launched an AI Research Division"),
            ExtractedEntity(name="AcmeSync", type="Product", source_quote="rebranded as AcmeSync"),
            ExtractedEntity(name="AWS", type="Organization", source_quote="partners exclusively with AWS"),
        ],
        relations=[
            ExtractedRelation(subject="Acme Corporation", predicate="led by", object="Jane Doe", source_quote="led by CEO Jane Doe"),
            ExtractedRelation(subject="Acme Corporation", predicate="launched", object="AI Research Division", source_quote="launched an AI Research Division"),
            ExtractedRelation(subject="Cloud Division", predicate="partners exclusively with", object="AWS", source_quote="partners exclusively with AWS"),
        ],
    )


@pytest.fixture
def mock_groq_client():
    mock = MagicMock()
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '{"entities": [{"name": "Acme Corp", "type": "Organization"}], "relations": []}'
    mock_resp.choices = [mock_choice]
    mock.chat.completions.create.return_value = mock_resp
    return mock
