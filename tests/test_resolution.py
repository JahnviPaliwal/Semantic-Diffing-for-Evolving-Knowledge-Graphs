"""Unit tests for entity resolution and hybrid similarity."""
from unittest.mock import MagicMock

import pytest

from src.semantic_diff.resolution import (
    EntityResolver,
    compute_fuzzy_similarity,
    normalize_name,
)


def test_normalize_name():
    assert normalize_name("Acme Corporation, Inc.") == "acme"
    assert normalize_name("Google LLC") == "google"
    assert normalize_name("Cloud Division") == "cloud"
    assert normalize_name("John Smith") == "john smith"


def test_fuzzy_similarity():
    sim = compute_fuzzy_similarity("DataSync Platform", "DataSync Platform v2")
    assert sim > 0.8
    assert compute_fuzzy_similarity("Acme Corp", "Acme Corporation") == 1.0


def test_explicit_rename_detection():
    resolver = EntityResolver()
    old_ents = ["DataSync Platform", "Acme Corporation", "John Smith"]
    new_ents = ["DataSync Platform Inc", "Acme Corporation", "Jane Doe"]

    canonical_map, renames = resolver.resolve_entities(old_ents, new_ents)
    assert canonical_map.get("Acme Corporation") == "Acme Corporation"
    assert canonical_map.get("DataSync Platform Inc") == "DataSync Platform"


def test_borderline_llm_verification():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '{"is_same_or_renamed": true, "confidence": 0.95, "reason": "product rebranding"}'
    mock_resp.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_resp

    resolver = EntityResolver(groq_client=mock_client)
    is_same, conf = resolver._verify_borderline_llm("DataSync Platform", "AcmeSync")
    assert is_same is True
    assert conf >= 0.9


def test_resolve_predicates():
    resolver = EntityResolver()
    match, sim = resolver.resolve_predicates("manages", "managed")
    assert match is True
    assert sim > 0.8
