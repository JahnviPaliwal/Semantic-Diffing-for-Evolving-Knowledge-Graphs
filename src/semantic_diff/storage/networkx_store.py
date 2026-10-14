"""
NetworkX Graph Store: in-memory default storage backend for temporal graphs.
Runs with zero external database dependencies.
"""
import logging
from typing import Dict, List, Optional

import networkx as nx

from ..diff_engine import SemanticDiffEngine
from ..models import DiffResult, ExtractionResult
from ..temporal import TemporalKnowledgeGraph
from .base import GraphStore

logger = logging.getLogger(__name__)


class NetworkXGraphStore(GraphStore):
    def __init__(self, diff_engine: Optional[SemanticDiffEngine] = None):
        self.diff_engine = diff_engine or SemanticDiffEngine()
        self.versions: Dict[str, ExtractionResult] = {}
        self.graphs: Dict[str, nx.DiGraph] = {}
        self.temporal_graph = TemporalKnowledgeGraph(diff_engine=self.diff_engine)

    def save_version(self, version_id: str, extraction: ExtractionResult) -> None:
        self.versions[version_id] = extraction

        # Build NetworkX DiGraph
        G = nx.DiGraph(version_id=version_id)
        for ent in extraction.entities:
            G.add_node(ent.name, type=ent.type, quote=ent.source_quote)

        for rel in extraction.relations:
            G.add_edge(rel.subject, rel.object, label=rel.predicate, quote=rel.source_quote)

        self.graphs[version_id] = G
        self.temporal_graph.add_version(extraction)
        logger.info(f"Stored version '{version_id}' in NetworkX Graph Store ({len(G.nodes)} nodes, {len(G.edges)} edges).")

    def get_version(self, version_id: str) -> Optional[ExtractionResult]:
        return self.versions.get(version_id)

    def get_all_version_ids(self) -> List[str]:
        return list(self.versions.keys())

    def compute_diff(self, from_version: str, to_version: str) -> DiffResult:
        if from_version not in self.versions:
            raise KeyError(f"Version '{from_version}' not found in store.")
        if to_version not in self.versions:
            raise KeyError(f"Version '{to_version}' not found in store.")
        return self.diff_engine.compute_diff(self.versions[from_version], self.versions[to_version])

    def get_temporal_graph(self) -> TemporalKnowledgeGraph:
        return self.temporal_graph

    def to_networkx(self, version_id: str) -> nx.DiGraph:
        if version_id not in self.graphs:
            raise KeyError(f"Graph for version '{version_id}' not found.")
        return self.graphs[version_id]
