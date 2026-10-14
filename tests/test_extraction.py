"""Unit tests for text chunking, hashing, and extraction logic."""
from unittest.mock import MagicMock

import pytest

from src.semantic_diff.extraction import ExtractionManager
from src.semantic_diff.utils.hashing import compute_text_hash
from src.semantic_diff.utils.text_chunker import chunk_text


def test_chunking_short_document():
    text = "Short policy document with one sentence."
    chunks = chunk_text(text, chunk_size=200, chunk_overlap=20)
    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].start_char == 0
    assert chunks[0].end_char == len(text)


def test_chunking_long_document_with_overlap():
    text = "Sentence one. " * 30 + "Sentence two. " * 30
    chunks = chunk_text(text, chunk_size=150, chunk_overlap=30)
    assert len(chunks) > 1
    assert chunks[0].chunk_id == 0
    assert chunks[1].chunk_id == 1
    # Verify continuous character progression
    assert chunks[1].start_char < chunks[0].end_char


def test_hashing_determinism():
    t1 = "  Acme  Corporation is based in   SF. \n"
    t2 = "Acme Corporation is based in SF."
    assert compute_text_hash(t1) == compute_text_hash(t2)


def test_extraction_with_mocked_client(mock_groq_client, tmp_path):
    mgr = ExtractionManager(api_key="fake-key", cache_dir=str(tmp_path), enable_cache=True)
    mgr._client = mock_groq_client

    result = mgr.extract_from_text("Acme Corp is a leader.", version_id="v1")
    assert result.version_id == "v1"
    assert len(result.entities) >= 1
    assert result.entities[0].name == "Acme Corp"


def test_extraction_model_fallback(tmp_path):
    mgr = ExtractionManager(api_key="fake-key", cache_dir=str(tmp_path), enable_cache=False)
    client_mock = MagicMock()
    # First call fails, second succeeds
    success_resp = MagicMock()
    choice = MagicMock()
    choice.message.content = '{"entities": [{"name": "Fallback Entity"}], "relations": []}'
    success_resp.choices = [choice]
    client_mock.chat.completions.create.side_effect = [Exception("Rate limit"), success_resp]
    mgr._client = client_mock

    result = mgr.extract_from_text("Test fallback", version_id="v1")
    assert len(result.entities) == 1
    assert result.entities[0].name == "Fallback Entity"
