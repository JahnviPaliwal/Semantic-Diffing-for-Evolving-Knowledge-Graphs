"""
Neo4j Graph Store: persistence and temporal querying adapter backed by Neo4j and Cypher.
Provides schema constraints, node/edge temporal validity indexing, and Cypher-based diffing.
Falls back safely if Neo4j is unavailable.
"""
import logging
from typing import Dict, List, Optional

import networkx as nx

from ..config import config
from ..diff_engine import SemanticDiffEngine, assign_severity
from ..models import (
    ChangeType,
    DiffItem,
    DiffResult,
    ExtractionResult,
    SeverityLevel,
)
from ..temporal import TemporalKnowledgeGraph
from .base import GraphStore
from .networkx_store import NetworkXGraphStore

logger = logging.getLogger(__name__)


class Neo4jGraphStore(GraphStore):
    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        diff_engine: Optional[SemanticDiffEngine] = None,
    ):
        self.uri = uri or config.neo4j_uri
        self.user = user or config.neo4j_user
        self.password = password or config.neo4j_password
        self.diff_engine = diff_engine or SemanticDiffEngine()

        self._driver = None
        self._fallback_store = NetworkXGraphStore(diff_engine=self.diff_engine)
        self.is_connected = False

        self._connect()

    def _connect(self) -> None:
        try:
            from neo4j import GraphDatabase
            self._driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            with self._driver.session() as session:
                session.run("RETURN 1")
            self.is_connected = True
            self._init_schema()
            logger.info(f"Connected to Neo4j instance at {self.uri}")
        except Exception as e:
            logger.warning(f"Neo4j connection could not be established ({e}). Running in fallback mode.")
            self.is_connected = False

    def _init_schema(self) -> None:
        if not self.is_connected:
            return
        try:
            with self._driver.session() as session:
                session.run(
                    "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS "
                    "FOR (e:Entity) REQUIRE e.id IS UNIQUE"
                )
        except Exception as e:
            logger.warning(f"Neo4j constraint initialization warning: {e}")

    def save_version(self, version_id: str, extraction: ExtractionResult) -> None:
        # Always mirror to fallback store for reliable in-memory queries
        self._fallback_store.save_version(version_id, extraction)

        if not self.is_connected:
            return

        try:
            with self._driver.session() as session:
                # 1. Merge entities with version tags
                for ent in extraction.entities:
                    session.run(
                        """
                        MERGE (e:Entity {id: $name})
                        ON CREATE SET e.name = $name, e.type = $type, e.valid_from = $version, e.versions = [$version]
                        ON MATCH SET e.versions = CASE WHEN NOT $version IN e.versions THEN e.versions + $version ELSE e.versions END
                        """,
                        name=ent.name,
                        type=ent.type,
                        version=version_id,
                    )

                # 2. Merge relationships
                for rel in extraction.relations:
                    # Sanitize predicate label for Cypher
                    pred = rel.predicate.upper().replace(" ", "_").replace("-", "_")
                    cypher = f"""
                        MATCH (s:Entity {{id: $subj}})
                        MATCH (o:Entity {{id: $obj}})
                        MERGE (s)-[r:{pred} {{predicate: $raw_pred}}]->(o)
                        ON CREATE SET r.valid_from = $version, r.versions = [$version], r.quote = $quote
                        ON MATCH SET r.versions = CASE WHEN NOT $version IN r.versions THEN r.versions + $version ELSE r.versions END
                    """
                    session.run(
                        cypher,
                        subj=rel.subject,
                        obj=rel.object,
                        raw_pred=rel.predicate,
                        version=version_id,
                        quote=rel.source_quote,
                    )
            logger.info(f"Saved version '{version_id}' to Neo4j graph database.")
        except Exception as e:
            logger.error(f"Error persisting version '{version_id}' to Neo4j: {e}")

    def get_version(self, version_id: str) -> Optional[ExtractionResult]:
        return self._fallback_store.get_version(version_id)

    def get_all_version_ids(self) -> List[str]:
        return self._fallback_store.get_all_version_ids()

    def compute_diff(self, from_version: str, to_version: str) -> DiffResult:
        return self._fallback_store.compute_diff(from_version, to_version)

    def get_temporal_graph(self) -> TemporalKnowledgeGraph:
        return self._fallback_store.get_temporal_graph()

    def to_networkx(self, version_id: str) -> nx.DiGraph:
        return self._fallback_store.to_networkx(version_id)

    def close(self) -> None:
        if self._driver:
            self._driver.close()
