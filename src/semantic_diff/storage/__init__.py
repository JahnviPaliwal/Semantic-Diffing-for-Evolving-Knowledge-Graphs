"""
Storage adapters and factory function for knowledge graph backends.
"""
from typing import Optional

from ..config import config
from .base import GraphStore
from .neo4j_store import Neo4jGraphStore
from .networkx_store import NetworkXGraphStore


def get_graph_store(store_type: Optional[str] = None) -> GraphStore:
    """Factory creating appropriate GraphStore backend based on config or argument."""
    selected = (store_type or config.default_graph_store).lower()
    if selected == "neo4j":
        return Neo4jGraphStore()
    return NetworkXGraphStore()


__all__ = ["GraphStore", "NetworkXGraphStore", "Neo4jGraphStore", "get_graph_store"]
