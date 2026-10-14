"""Unit tests for GraphStore storage adapters."""
import pytest

from src.semantic_diff.storage import Neo4jGraphStore, NetworkXGraphStore, get_graph_store


def test_networkx_graph_store(sample_v1_extraction, sample_v2_extraction):
    store = NetworkXGraphStore()
    store.save_version("v1", sample_v1_extraction)
    store.save_version("v2", sample_v2_extraction)

    assert "v1" in store.get_all_version_ids()
    assert "v2" in store.get_all_version_ids()

    g1 = store.to_networkx("v1")
    assert g1.has_node("Acme Corporation")

    diff = store.compute_diff("v1", "v2")
    assert "AI Research Division" in diff.added_entities


def test_neo4j_offline_fallback(sample_v1_extraction):
    # Tests that Neo4jGraphStore falls back gracefully to in-memory store when offline
    store = Neo4jGraphStore(uri="bolt://localhost:9999")
    assert store.is_connected is False
    store.save_version("v1", sample_v1_extraction)
    assert "v1" in store.get_all_version_ids()
