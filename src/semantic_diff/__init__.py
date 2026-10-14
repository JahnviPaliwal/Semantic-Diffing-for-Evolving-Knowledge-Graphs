"""
Semantic Diffing for Evolving Knowledge Graphs.
A system for tracking structural and semantic changes across document versions.
"""

__version__ = "2.0.0"

from .config import SeverityConfig, SystemConfig, config
from .diff_engine import SemanticDiffEngine
from .extraction import ExtractionManager
from .models import (
    ChangeType,
    DiffItem,
    DiffResult,
    ExtractedEntity,
    ExtractedRelation,
    ExtractionResult,
    ResolvedEntity,
    ResolvedRelation,
    SeverityLevel,
    TemporalEdge,
    TemporalNode,
)
from .resolution import EntityResolver, normalize_name
from .summary import SummaryGenerator
from .temporal import TemporalKnowledgeGraph

__all__ = [
    "ChangeType",
    "SeverityLevel",
    "ExtractedEntity",
    "ExtractedRelation",
    "ExtractionResult",
    "ResolvedEntity",
    "ResolvedRelation",
    "DiffItem",
    "DiffResult",
    "TemporalNode",
    "TemporalEdge",
    "SystemConfig",
    "SeverityConfig",
    "config",
    "ExtractionManager",
    "EntityResolver",
    "normalize_name",
    "SemanticDiffEngine",
    "TemporalKnowledgeGraph",
    "SummaryGenerator",
]
