"""Unit tests for LangGraph end-to-end pipeline."""
from unittest.mock import MagicMock

import pytest

from src.semantic_diff.extraction import ExtractionManager
from src.semantic_diff.models import ExtractedEntity, ExtractedRelation, ExtractionResult
from src.semantic_diff.workflow import KnowledgeGraphWorkflow


def test_workflow_execution(sample_v1_extraction, sample_v2_extraction):
    extractor_mock = MagicMock(spec=ExtractionManager)
    extractor_mock.extract_from_text.side_effect = [sample_v1_extraction, sample_v2_extraction]

    workflow = KnowledgeGraphWorkflow(extractor=extractor_mock)
    result = workflow.run("v1 text", "v2 text", v1_id="v1", v2_id="v2")

    assert result["diff_result"] is not None
    assert result["verification_passed"] is True
    assert len(result["logs"]) >= 6
    assert result["summary"] is not None
