"""Unit tests for multi-version temporal knowledge graph."""
import pytest

from src.semantic_diff.models import ExtractedEntity, ExtractedRelation, ExtractionResult
from src.semantic_diff.temporal import TemporalKnowledgeGraph


def test_temporal_graph_build(sample_v1_extraction, sample_v2_extraction):
    t_graph = TemporalKnowledgeGraph()
    t_graph.add_version(sample_v1_extraction)
    assert len(t_graph.timeline) == 1

    t_graph.add_version(sample_v2_extraction)
    assert len(t_graph.timeline) == 2

    # Check temporal nodes
    acme_node = t_graph.nodes.get("Acme Corporation")
    assert acme_node is not None
    assert "v1" in acme_node.versions
    assert "v2" in acme_node.versions

    legacy_dept = t_graph.nodes.get("Legacy Systems Department")
    assert legacy_dept is not None
    assert legacy_dept.valid_to == "v2"

    # Cross version diff query
    diff = t_graph.diff_between("v1", "v2")
    assert "AI Research Division" in diff.added_entities
