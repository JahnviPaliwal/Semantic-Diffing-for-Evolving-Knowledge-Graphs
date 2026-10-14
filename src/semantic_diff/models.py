"""
Pydantic data models for extraction, entity resolution, diffing, and temporal graphs.
"""
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    RENAMED = "RENAMED"
    MODIFIED = "MODIFIED"
    UNCHANGED = "UNCHANGED"


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ExtractedEntity(BaseModel):
    name: str = Field(..., description="Canonical extracted entity name")
    type: str = Field(default="Entity", description="Entity category: Organization, Person, Product, Role, Location, etc.")
    source_quote: Optional[str] = Field(default="", description="Verbatim quote from the source text grounding this entity")
    char_offset_start: Optional[int] = Field(default=None, description="Starting character offset in text/chunk")
    char_offset_end: Optional[int] = Field(default=None, description="Ending character offset in text/chunk")
    chunk_id: Optional[int] = Field(default=0, description="Index of document chunk where entity appeared")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score")


class ExtractedRelation(BaseModel):
    subject: str = Field(..., description="Subject entity name")
    predicate: str = Field(..., description="Relation predicate / interaction verb phrase")
    object: str = Field(..., description="Object entity name")
    source_quote: Optional[str] = Field(default="", description="Verbatim source quote grounding the relation")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score")


class ExtractionResult(BaseModel):
    version_id: str = Field(..., description="Document version identifier e.g. 'v1', 'v2'")
    doc_hash: str = Field(..., description="SHA-256 hash of raw document content")
    raw_text: str = Field(default="", description="Source text extracted")
    entities: List[ExtractedEntity] = Field(default_factory=list, description="Extracted entities")
    relations: List[ExtractedRelation] = Field(default_factory=list, description="Extracted relations")
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp of extraction")


class ResolvedEntity(BaseModel):
    canonical_name: str = Field(..., description="Normalized or unified entity identifier")
    raw_name: str = Field(..., description="Original raw surface form")
    entity_type: str = Field(default="Entity", description="Entity type")
    confidence: float = Field(default=1.0, description="Resolution confidence")
    is_renamed: bool = Field(default=False, description="Whether resolved as a rename of an earlier entity")
    previous_name: Optional[str] = Field(default=None, description="Previous surface form if renamed")


class ResolvedRelation(BaseModel):
    subject: str = Field(..., description="Resolved subject canonical name")
    predicate: str = Field(..., description="Normalized relation predicate")
    object: str = Field(..., description="Resolved object canonical name")
    confidence: float = Field(default=1.0, description="Resolution confidence")
    is_modified: bool = Field(default=False, description="Whether relation predicate modified")
    previous_predicate: Optional[str] = Field(default=None, description="Prior predicate if modified")


class DiffItem(BaseModel):
    element_type: str = Field(..., description="'node' or 'edge'")
    change_type: ChangeType = Field(..., description="Change classification")
    canonical_name: str = Field(..., description="Entity name or triple representation '(S)-[P]->(O)'")
    previous_name: Optional[str] = Field(default=None, description="Previous entity name or predicate if renamed/modified")
    source_quote: Optional[str] = Field(default="", description="Verbatim text quote from source document")
    chunk_reference: Optional[str] = Field(default="", description="Chunk or page reference")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Diff detection confidence")
    severity: SeverityLevel = Field(default=SeverityLevel.LOW, description="Configurable impact severity")
    rationale: Optional[str] = Field(default="", description="Domain explanation for change and severity assignment")


class DiffResult(BaseModel):
    from_version: str = Field(..., description="Source snapshot version")
    to_version: str = Field(..., description="Target snapshot version")
    added_entities: List[str] = Field(default_factory=list)
    removed_entities: List[str] = Field(default_factory=list)
    renamed_entities: List[Dict[str, Any]] = Field(default_factory=list, description="[{'from': 'Old', 'to': 'New'}]")
    modified_entities: List[str] = Field(default_factory=list)
    unchanged_entities: List[str] = Field(default_factory=list)
    added_relations: List[List[str]] = Field(default_factory=list, description="[[subj, pred, obj]]")
    removed_relations: List[List[str]] = Field(default_factory=list)
    modified_relations: List[Dict[str, Any]] = Field(default_factory=list)
    unchanged_relations: List[List[str]] = Field(default_factory=list)
    items: List[DiffItem] = Field(default_factory=list, description="Granular diff items with quotes and severity")
    severity_summary: Dict[str, int] = Field(default_factory=dict, description="Counts by severity level")
    narrative: Optional[str] = Field(default="", description="Natural-language executive summary")


class TemporalNode(BaseModel):
    id: str = Field(..., description="Node canonical ID")
    canonical_name: str = Field(..., description="Display name")
    entity_type: str = Field(default="Entity")
    valid_from: str = Field(..., description="Version ID where node first appeared")
    valid_to: Optional[str] = Field(default=None, description="Version ID where node was removed, or None if current")
    versions: List[str] = Field(default_factory=list, description="All versions in which node exists")


class TemporalEdge(BaseModel):
    source: str = Field(..., description="Source node ID")
    predicate: str = Field(..., description="Relationship label")
    target: str = Field(..., description="Target node ID")
    valid_from: str = Field(..., description="Version ID where edge first appeared")
    valid_to: Optional[str] = Field(default=None, description="Version ID where edge was removed, or None if current")
    versions: List[str] = Field(default_factory=list, description="All versions in which edge exists")
