"""
Multi-Version Temporal Knowledge Graph.
Maintains temporal validity intervals (valid_from / valid_to) for nodes and edges
across N document versions, generates chronological change timelines, and executes
cross-version queries ('what changed between vX and vY').
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from .diff_engine import SemanticDiffEngine
from .models import (
    DiffResult,
    ExtractionResult,
    ResolvedEntity,
    TemporalEdge,
    TemporalNode,
)
from .resolution import EntityResolver, normalize_name

logger = logging.getLogger(__name__)


class TimelineEvent(BaseModel):
    version_id: str = Field(..., description="Version identifier")
    timestamp: Optional[str] = Field(default=None)
    event_type: str = Field(default="version_update")
    description: str = Field(..., description="Summary of changes in this version")
    entities_added: List[str] = Field(default_factory=list)
    entities_removed: List[str] = Field(default_factory=list)
    entities_renamed: List[Dict[str, str]] = Field(default_factory=list)
    relations_added: int = 0
    relations_removed: int = 0
    critical_changes: int = 0
    high_changes: int = 0


class TemporalKnowledgeGraph:
    def __init__(self, diff_engine: Optional[SemanticDiffEngine] = None):
        self.diff_engine = diff_engine or SemanticDiffEngine()
        self.nodes: Dict[str, TemporalNode] = {}
        self.edges: Dict[Tuple[str, str, str], TemporalEdge] = {}
        self.version_order: List[str] = []
        self.version_extractions: Dict[str, ExtractionResult] = {}
        self.timeline: List[TimelineEvent] = []

    def add_version(self, extraction: ExtractionResult, timestamp: Optional[str] = None) -> TimelineEvent:
        """Add a document version snapshot and update temporal intervals."""
        v_id = extraction.version_id
        if v_id in self.version_order:
            logger.warning(f"Version {v_id} already exists in temporal graph. Overwriting.")
            self.version_order.remove(v_id)

        self.version_order.append(v_id)
        self.version_extractions[v_id] = extraction

        current_nodes = {e.name: e for e in extraction.entities}
        current_edges = {(r.subject, r.predicate, r.object): r for r in extraction.relations}

        # If this is the initial version (v1)
        if len(self.version_order) == 1:
            for name, ent in current_nodes.items():
                self.nodes[name] = TemporalNode(
                    id=name,
                    canonical_name=name,
                    entity_type=ent.type,
                    valid_from=v_id,
                    valid_to=None,
                    versions=[v_id],
                )

            for triple, rel in current_edges.items():
                self.edges[triple] = TemporalEdge(
                    source=rel.subject,
                    predicate=rel.predicate,
                    target=rel.object,
                    valid_from=v_id,
                    valid_to=None,
                    versions=[v_id],
                )

            event = TimelineEvent(
                version_id=v_id,
                timestamp=timestamp or extraction.timestamp,
                event_type="initial_baseline",
                description=f"Initial baseline established with {len(current_nodes)} entities and {len(current_edges)} relationships.",
                entities_added=list(current_nodes.keys()),
                relations_added=len(current_edges),
            )
            self.timeline.append(event)
            return event

        # Otherwise compare with immediate predecessor
        prev_v_id = self.version_order[-2]
        prev_extraction = self.version_extractions[prev_v_id]
        diff = self.diff_engine.compute_diff(prev_extraction, extraction)

        # 1. Update existing nodes that are retained
        for name in diff.unchanged_entities:
            if name in self.nodes:
                self.nodes[name].versions.append(v_id)

        # 2. Add brand new nodes
        for name in diff.added_entities:
            ent = current_nodes.get(name)
            self.nodes[name] = TemporalNode(
                id=name,
                canonical_name=name,
                entity_type=ent.type if ent else "Entity",
                valid_from=v_id,
                valid_to=None,
                versions=[v_id],
            )

        # 3. Mark removed nodes
        for name in diff.removed_entities:
            if name in self.nodes and self.nodes[name].valid_to is None:
                self.nodes[name].valid_to = v_id

        # 4. Handle renamed nodes
        for rp in diff.renamed_entities:
            old_name = rp["from"]
            new_name = rp["to"]
            if old_name in self.nodes and self.nodes[old_name].valid_to is None:
                self.nodes[old_name].valid_to = v_id

            ent = current_nodes.get(new_name)
            self.nodes[new_name] = TemporalNode(
                id=new_name,
                canonical_name=new_name,
                entity_type=ent.type if ent else "Entity",
                valid_from=v_id,
                valid_to=None,
                versions=[v_id],
            )

        # 5. Update edges
        for rel in diff.unchanged_relations:
            triple = tuple(rel)
            if triple in self.edges:
                self.edges[triple].versions.append(v_id)

        for rel in diff.added_relations:
            triple = tuple(rel)
            self.edges[triple] = TemporalEdge(
                source=rel[0],
                predicate=rel[1],
                target=rel[2],
                valid_from=v_id,
                valid_to=None,
                versions=[v_id],
            )

        for rel in diff.removed_relations:
            triple = tuple(rel)
            if triple in self.edges and self.edges[triple].valid_to is None:
                self.edges[triple].valid_to = v_id

        event = TimelineEvent(
            version_id=v_id,
            timestamp=timestamp or extraction.timestamp,
            event_type="version_update",
            description=(
                f"Updated from {prev_v_id}: +{len(diff.added_entities)} entities, "
                f"-{len(diff.removed_entities)} entities, {len(diff.renamed_entities)} renamed, "
                f"+{len(diff.added_relations)} / -{len(diff.removed_relations)} relations."
            ),
            entities_added=diff.added_entities,
            entities_removed=diff.removed_entities,
            entities_renamed=diff.renamed_entities,
            relations_added=len(diff.added_relations),
            relations_removed=len(diff.removed_relations),
            critical_changes=diff.severity_summary.get("CRITICAL", 0),
            high_changes=diff.severity_summary.get("HIGH", 0),
        )
        self.timeline.append(event)
        return event

    def build_from_versions(self, extractions: List[ExtractionResult]) -> None:
        """Sequentially construct the temporal knowledge graph from a list of version extractions."""
        self.nodes.clear()
        self.edges.clear()
        self.version_order.clear()
        self.version_extractions.clear()
        self.timeline.clear()
        for ext in extractions:
            self.add_version(ext)

    def get_timeline(self) -> List[TimelineEvent]:
        return self.timeline

    def get_snapshot(self, version_id: str) -> Dict[str, Any]:
        """Return all nodes and edges active at a specific version snapshot."""
        if version_id not in self.version_order:
            raise ValueError(f"Version '{version_id}' not found in temporal graph history.")

        active_nodes = [
            node.model_dump() for node in self.nodes.values()
            if version_id in node.versions
        ]
        active_edges = [
            edge.model_dump() for edge in self.edges.values()
            if version_id in edge.versions
        ]
        return {
            "version_id": version_id,
            "nodes": active_nodes,
            "edges": active_edges,
        }

    def diff_between(self, from_version: str, to_version: str) -> DiffResult:
        """Arbitrary cross-version query: what changed between vX and vY."""
        if from_version not in self.version_extractions:
            raise ValueError(f"Source version '{from_version}' not found.")
        if to_version not in self.version_extractions:
            raise ValueError(f"Target version '{to_version}' not found.")

        old_ext = self.version_extractions[from_version]
        new_ext = self.version_extractions[to_version]
        return self.diff_engine.compute_diff(old_ext, new_ext)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize complete temporal graph."""
        return {
            "versions": self.version_order,
            "nodes": [n.model_dump() for n in self.nodes.values()],
            "edges": [e.model_dump() for e in self.edges.values()],
            "timeline": [t.model_dump() for t in self.timeline],
        }
