"""
Configuration settings for semantic diffing, entity resolution, severity scoring, and graph stores.
"""
import os
from typing import List

from pydantic import BaseModel, Field


class SeverityConfig(BaseModel):
    critical_keywords: List[str] = Field(
        default_factory=lambda: [
            "governing law", "jurisdiction", "liability", "indemnification",
            "regulatory", "compliance", "penalty", "breach", "sanction", "gdpr"
        ]
    )
    high_keywords: List[str] = Field(
        default_factory=lambda: [
            "exclusive", "exclusively", "terminate", "termination", "ceo",
            "cto", "executive", "merger", "merged", "acquisition", "obligation",
            "warranty", "rebranded", "audit"
        ]
    )
    medium_keywords: List[str] = Field(
        default_factory=lambda: [
            "partner", "partnered", "launch", "launched", "operate", "operates",
            "manage", "manages", "expand", "expanded", "report", "reports"
        ]
    )
    low_keywords: List[str] = Field(
        default_factory=lambda: [
            "located_in", "headquartered", "maintains", "description", "feature"
        ]
    )


class SystemConfig(BaseModel):
    groq_model: str = Field(
        default_factory=lambda: os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    )
    fallback_models: List[str] = Field(
        default_factory=lambda: [
            "qwen/qwen3.8-27b",
        ]
    )
    temperature: float = 0.0
    max_retries: int = 3
    retry_backoff: float = 1.5
    groq_api_key: str = Field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))

    chunk_size: int = 2000
    chunk_overlap: int = 200

    cache_dir: str = ".cache/extractions"
    enable_cache: bool = True

    embedding_model_name: str = "all-MiniLM-L6-v2"
    embed_weight: float = 0.6
    fuzzy_weight: float = 0.4
    similarity_high_threshold: float = 0.88
    similarity_borderline_threshold: float = 0.70
    relation_similarity_threshold: float = 0.75

    severity_rules: SeverityConfig = Field(default_factory=SeverityConfig)

    default_graph_store: str = "networkx"
    neo4j_uri: str = Field(default_factory=lambda: os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    neo4j_user: str = Field(default_factory=lambda: os.getenv("NEO4J_USER", "neo4j"))
    neo4j_password: str = Field(default_factory=lambda: os.getenv("NEO4J_PASSWORD", "password123"))


config = SystemConfig()
