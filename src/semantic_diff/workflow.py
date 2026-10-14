"""
LangGraph pipeline orchestrator for end-to-end semantic knowledge graph diffing:
(extract -> resolve -> build -> diff -> summarize -> verify)
with typed state and per-node logging.
"""
import logging
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from .diff_engine import SemanticDiffEngine
from .extraction import ExtractionManager
from .models import DiffResult, ExtractionResult
from .resolution import EntityResolver
from .summary import SummaryGenerator
from .temporal import TemporalKnowledgeGraph

logger = logging.getLogger(__name__)


class DiffWorkflowState(TypedDict):
    v1_text: str
    v2_text: str
    v1_id: str
    v2_id: str
    v1_extraction: Optional[ExtractionResult]
    v2_extraction: Optional[ExtractionResult]
    canonical_map: Dict[str, str]
    renamed_pairs: List[Dict[str, str]]
    temporal_graph: Optional[Dict[str, Any]]
    diff_result: Optional[DiffResult]
    summary: Optional[str]
    verification_passed: bool
    logs: List[str]


class KnowledgeGraphWorkflow:
    def __init__(
        self,
        extractor: Optional[ExtractionManager] = None,
        resolver: Optional[EntityResolver] = None,
        diff_engine: Optional[SemanticDiffEngine] = None,
        summarizer: Optional[SummaryGenerator] = None,
    ):
        self.extractor = extractor or ExtractionManager()
        self.resolver = resolver or EntityResolver()
        self.diff_engine = diff_engine or SemanticDiffEngine(resolver=self.resolver)
        self.summarizer = summarizer or SummaryGenerator()
        self.graph = self._build_graph()

    def _log(self, logs: List[str], msg: str) -> List[str]:
        entry = f"[{logging.getLevelName(logging.INFO)}] {msg}"
        logger.info(msg)
        return logs + [entry]

    def node_extract(self, state: DiffWorkflowState) -> Dict[str, Any]:
        """Node 1: Extract entities and relations from both document versions."""
        logs = self._log(state.get("logs", []), "Workflow node: EXTRACT started")
        v1_ext = self.extractor.extract_from_text(state["v1_text"], version_id=state.get("v1_id", "v1"))
        v2_ext = self.extractor.extract_from_text(state["v2_text"], version_id=state.get("v2_id", "v2"))
        logs = self._log(
            logs,
            f"Extracted v1 ({len(v1_ext.entities)} ents, {len(v1_ext.relations)} rels) and "
            f"v2 ({len(v2_ext.entities)} ents, {len(v2_ext.relations)} rels)"
        )
        return {
            "v1_extraction": v1_ext,
            "v2_extraction": v2_ext,
            "logs": logs,
        }

    def node_resolve(self, state: DiffWorkflowState) -> Dict[str, Any]:
        """Node 2: Resolve near-duplicates, renames, and aliases across versions."""
        logs = self._log(state.get("logs", []), "Workflow node: RESOLVE started")
        v1_ext: ExtractionResult = state["v1_extraction"]
        v2_ext: ExtractionResult = state["v2_extraction"]

        old_names = [e.name for e in v1_ext.entities]
        new_names = [e.name for e in v2_ext.entities]

        canonical_map, renamed_pairs = self.resolver.resolve_entities(old_names, new_names)
        logs = self._log(
            logs,
            f"Resolved entities: {len(canonical_map)} mapped canonical, {len(renamed_pairs)} identified as renames"
        )
        return {
            "canonical_map": canonical_map,
            "renamed_pairs": renamed_pairs,
            "logs": logs,
        }

    def node_build(self, state: DiffWorkflowState) -> Dict[str, Any]:
        """Node 3: Construct temporal knowledge graph spanning both versions."""
        logs = self._log(state.get("logs", []), "Workflow node: BUILD temporal graph started")
        t_graph = TemporalKnowledgeGraph(diff_engine=self.diff_engine)
        t_graph.add_version(state["v1_extraction"])
        t_graph.add_version(state["v2_extraction"])
        logs = self._log(
            logs,
            f"Constructed temporal graph with {len(t_graph.nodes)} temporal nodes and {len(t_graph.edges)} edges"
        )
        return {
            "temporal_graph": t_graph.to_dict(),
            "logs": logs,
        }

    def node_diff(self, state: DiffWorkflowState) -> Dict[str, Any]:
        """Node 4: Compute rich semantic diff with severity scoring and source grounding."""
        logs = self._log(state.get("logs", []), "Workflow node: DIFF started")
        diff = self.diff_engine.compute_diff(state["v1_extraction"], state["v2_extraction"])
        logs = self._log(
            logs,
            f"Diff computed: {len(diff.added_entities)} added, {len(diff.removed_entities)} removed, "
            f"severity breakdown: {diff.severity_summary}"
        )
        return {
            "diff_result": diff,
            "logs": logs,
        }

    def node_summarize(self, state: DiffWorkflowState) -> Dict[str, Any]:
        """Node 5: Generate natural-language executive summary."""
        logs = self._log(state.get("logs", []), "Workflow node: SUMMARIZE started")
        diff: DiffResult = state["diff_result"]
        summary = self.summarizer.generate_summary(diff)
        diff.narrative = summary
        logs = self._log(logs, "Generated natural-language narrative")
        return {
            "summary": summary,
            "diff_result": diff,
            "logs": logs,
        }

    def node_verify(self, state: DiffWorkflowState) -> Dict[str, Any]:
        """Node 6: Verify invariants and schema validity."""
        logs = self._log(state.get("logs", []), "Workflow node: VERIFY started")
        diff: DiffResult = state["diff_result"]

        # Verification Invariant: total items match added + removed + renamed + modified elements
        expected_items = (
            len(diff.added_entities)
            + len(diff.removed_entities)
            + len(diff.renamed_entities)
            + len(diff.added_relations)
            + len(diff.removed_relations)
            + len(diff.modified_relations)
        )
        actual_items = len(diff.items)
        passed = (actual_items == expected_items)

        logs = self._log(
            logs,
            f"Verification {'PASSED' if passed else 'WARNING'}: items count {actual_items} vs expected {expected_items}"
        )
        return {
            "verification_passed": passed,
            "logs": logs,
        }

    def _build_graph(self):
        builder = StateGraph(DiffWorkflowState)
        builder.add_node("extract", self.node_extract)
        builder.add_node("resolve", self.node_resolve)
        builder.add_node("build", self.node_build)
        builder.add_node("diff", self.node_diff)
        builder.add_node("summarize", self.node_summarize)
        builder.add_node("verify", self.node_verify)

        builder.add_edge(START, "extract")
        builder.add_edge("extract", "resolve")
        builder.add_edge("resolve", "build")
        builder.add_edge("build", "diff")
        builder.add_edge("diff", "summarize")
        builder.add_edge("summarize", "verify")
        builder.add_edge("verify", END)

        return builder.compile()

    def run(
        self,
        v1_text: str,
        v2_text: str,
        v1_id: str = "v1",
        v2_id: str = "v2",
    ) -> DiffWorkflowState:
        """Execute end-to-end LangGraph pipeline."""
        initial_state: DiffWorkflowState = {
            "v1_text": v1_text,
            "v2_text": v2_text,
            "v1_id": v1_id,
            "v2_id": v2_id,
            "v1_extraction": None,
            "v2_extraction": None,
            "canonical_map": {},
            "renamed_pairs": [],
            "temporal_graph": None,
            "diff_result": None,
            "summary": None,
            "verification_passed": False,
            "logs": [],
        }
        final_state = self.graph.invoke(initial_state)
        return final_state
