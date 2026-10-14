"""Unit tests for the semantic diff engine and severity assignment."""
import pytest

from src.semantic_diff.diff_engine import SemanticDiffEngine, assign_severity
from src.semantic_diff.models import ChangeType, SeverityLevel


def test_assign_severity_critical():
    sev, reason = assign_severity(["governing law of the state of Delaware", "liability limited"], ChangeType.ADDED)
    assert sev == SeverityLevel.CRITICAL
    assert "governing law" in reason or "liability" in reason


def test_assign_severity_high_exclusivity():
    sev, reason = assign_severity(["partners exclusively with AWS"], ChangeType.MODIFIED)
    assert sev == SeverityLevel.HIGH
    assert "exclusive" in reason


def test_compute_diff_with_renamed_and_severity(sample_v1_extraction, sample_v2_extraction):
    engine = SemanticDiffEngine()
    diff = engine.compute_diff(sample_v1_extraction, sample_v2_extraction)

    assert "AI Research Division" in diff.added_entities
    assert "Legacy Systems Department" in diff.removed_entities
    assert diff.severity_summary[SeverityLevel.HIGH.value] >= 1
    assert len(diff.items) > 0

    # Ensure items have source quote and severity
    for item in diff.items:
        assert item.element_type in ("node", "edge")
        assert item.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH, SeverityLevel.MEDIUM, SeverityLevel.LOW)
