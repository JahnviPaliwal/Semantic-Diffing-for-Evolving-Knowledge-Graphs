"""
Abstract GraphStore interface for knowledge graph storage and version diffing.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import networkx as nx

from ..models import DiffResult, ExtractionResult
from ..temporal import TemporalKnowledgeGraph


class GraphStore(ABC):
    @abstractmethod
    def save_version(self, version_id: str, extraction: ExtractionResult) -> None:
        """Persist a version's extraction results."""
        pass

    @abstractmethod
    def get_version(self, version_id: str) -> Optional[ExtractionResult]:
        """Retrieve an extraction result for a given version ID."""
        pass

    @abstractmethod
    def get_all_version_ids(self) -> List[str]:
        """List all version IDs currently stored."""
        pass

    @abstractmethod
    def compute_diff(self, from_version: str, to_version: str) -> DiffResult:
        """Compute semantic diff between two stored versions."""
        pass

    @abstractmethod
    def get_temporal_graph(self) -> TemporalKnowledgeGraph:
        """Retrieve the multi-version temporal graph."""
        pass

    @abstractmethod
    def to_networkx(self, version_id: str) -> nx.DiGraph:
        """Export a version snapshot as a NetworkX DiGraph."""
        pass
