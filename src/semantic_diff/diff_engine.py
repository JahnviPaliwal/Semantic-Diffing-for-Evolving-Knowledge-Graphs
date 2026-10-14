"""
Rich Semantic Diff Engine: computes structured graph differences distinguishing
ADDED, REMOVED, RENAMED, and MODIFIED nodes and edges, attaching source quotes,
chunk references, extraction confidence, and configurable domain severity ratings.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from .config import SeverityConfig, config
from .models import (
    ChangeType,
    DiffItem,
    DiffResult,
    ExtractionResult,
    SeverityLevel,
)
from .resolution import EntityResolver, normalize_name

logger = logging.getLogger(__name__)


def assign_severity(
    text_snippets: List[str],
    change_type: ChangeType,
    rules: Optional[SeverityConfig] = None,
) -> Tuple[SeverityLevel, str]:
    """
    Score the domain severity of a detected change based on semantic keywords and change type.
    Returns (SeverityLevel, rationale_explanation).
    """
    cfg = rules or config.severity_rules
    combined = " ".join([s.lower() for s in text_snippets if s])

    # 1. Critical keywords
    for kw in cfg.critical_keywords:
        if kw in combined:
            return (
                SeverityLevel.CRITICAL,
                f"Matched critical keyword '{kw}' (legal, jurisdiction, liability, or compliance shift)",
            )

    # 2. High keywords
    for kw in cfg.high_keywords:
        if kw in combined:
            return (
                SeverityLevel.HIGH,
                f"Matched high-impact keyword '{kw}' (exclusivity, leadership, restructuring, or obligations)",
            )

    # 3. Medium keywords
    for kw in cfg.medium_keywords:
        if kw in combined:
            return (
                SeverityLevel.MEDIUM,
                f"Matched operational keyword '{kw}' (partnerships, product launch, or organizational scope)",
            )

    # Structural heuristic based on change type
    if change_type == ChangeType.RENAMED:
        return SeverityLevel.MEDIUM, "Entity rebranding or title rename detected"
    if change_type in (ChangeType.REMOVED, ChangeType.MODIFIED):
        return SeverityLevel.MEDIUM, "Structural entity removal or relation modification"
    if change_type == ChangeType.ADDED:
        return SeverityLevel.LOW, "Routine addition of entity or relationship"

    return SeverityLevel.LOW, "Standard low-impact baseline element"


class SemanticDiffEngine:
    def __init__(self, resolver: Optional[EntityResolver] = None):
        self.resolver = resolver or EntityResolver()

    def compute_diff(
        self,
        old_data: ExtractionResult,
        new_data: ExtractionResult,
    ) -> DiffResult:
        """Compute rich semantic diff between baseline (v1) and updated (v2) extractions."""
        old_ents_list = [e.name for e in old_data.entities]
        new_ents_list = [e.name for e in new_data.entities]

        old_ent_lookup = {e.name: e for e in old_data.entities}
        new_ent_lookup = {e.name: e for e in new_data.entities}

        old_quotes = {e.name: e.source_quote for e in old_data.entities}
        new_quotes = {e.name: e.source_quote for e in new_data.entities}

        # 1. Resolve entities (handles exact match, normalize, embedding + fuzzy, and provenance cues)
        canonical_map, renamed_pairs = self.resolver.resolve_entities(
            old_ents_list, new_ents_list, old_quotes=old_quotes, new_quotes=new_quotes
        )

        renamed_from = {p["from"] for p in renamed_pairs}
        renamed_to = {p["to"] for p in renamed_pairs}

        added_entities: List[str] = []
        unchanged_entities: List[str] = []
        for new_name in new_ents_list:
            if new_name in renamed_to:
                continue
            if new_name in canonical_map:
                unchanged_entities.append(new_name)
            else:
                added_entities.append(new_name)

        removed_entities: List[str] = []
        for old_name in old_ents_list:
            if old_name in renamed_from:
                continue
            # Was this old_name mapped to anything in canonical_map?
            if old_name not in canonical_map.values():
                removed_entities.append(old_name)

        diff_items: List[DiffItem] = []

        # Record Added Entity Diff Items
        for name in added_entities:
            ent = new_ent_lookup.get(name)
            quote = ent.source_quote if ent else ""
            sev, rationale = assign_severity([name, quote, ent.type if ent else ""], ChangeType.ADDED)
            diff_items.append(
                DiffItem(
                    element_type="node",
                    change_type=ChangeType.ADDED,
                    canonical_name=name,
                    source_quote=quote,
                    chunk_reference=f"chunk_{ent.chunk_id}" if ent else "",
                    confidence=ent.confidence if ent else 0.95,
                    severity=sev,
                    rationale=rationale,
                )
            )

        # Record Removed Entity Diff Items
        for name in removed_entities:
            ent = old_ent_lookup.get(name)
            quote = ent.source_quote if ent else ""
            sev, rationale = assign_severity([name, quote, ent.type if ent else ""], ChangeType.REMOVED)
            diff_items.append(
                DiffItem(
                    element_type="node",
                    change_type=ChangeType.REMOVED,
                    canonical_name=name,
                    source_quote=quote,
                    chunk_reference=f"chunk_{ent.chunk_id}" if ent else "",
                    confidence=ent.confidence if ent else 0.95,
                    severity=sev,
                    rationale=rationale,
                )
            )

        # Record Renamed Entity Diff Items
        for rp in renamed_pairs:
            old_name = rp["from"]
            new_name = rp["to"]
            old_ent = old_ent_lookup.get(old_name)
            new_ent = new_ent_lookup.get(new_name)
            quotes = [old_ent.source_quote if old_ent else "", new_ent.source_quote if new_ent else ""]
            sev, rationale = assign_severity([old_name, new_name] + quotes, ChangeType.RENAMED)
            diff_items.append(
                DiffItem(
                    element_type="node",
                    change_type=ChangeType.RENAMED,
                    canonical_name=new_name,
                    previous_name=old_name,
                    source_quote=new_ent.source_quote if new_ent else (old_ent.source_quote if old_ent else ""),
                    chunk_reference=f"chunk_{new_ent.chunk_id}" if new_ent else "",
                    confidence=float(rp.get("confidence", 0.9)),
                    severity=sev,
                    rationale=rationale,
                )
            )

        # 2. Relation diffing
        # Normalize relations using canonical entity map
        def canonical_triple(s: str, p: str, o: str) -> Tuple[str, str, str]:
            c_s = canonical_map.get(s, s)
            c_o = canonical_map.get(o, o)
            return (c_s, p.lower().strip(), c_o)

        old_canonical_rels = {canonical_triple(r.subject, r.predicate, r.object): r for r in old_data.relations}
        new_canonical_rels = {canonical_triple(r.subject, r.predicate, r.object): r for r in new_data.relations}

        added_relations: List[List[str]] = []
        removed_relations: List[List[str]] = []
        unchanged_relations: List[List[str]] = []
        modified_relations: List[Dict[str, Any]] = []

        # Find matching or modified relations
        matched_old_triples = set()
        for new_trip, new_rel in new_canonical_rels.items():
            new_s, new_p, new_o = new_trip

            if new_trip in old_canonical_rels:
                matched_old_triples.add(new_trip)
                unchanged_relations.append([new_rel.subject, new_rel.predicate, new_rel.object])
                continue

            # Check if there is an old relation connecting the same subject and object with modified predicate
            found_mod = False
            for old_trip, old_rel in old_canonical_rels.items():
                if old_trip in matched_old_triples:
                    continue
                old_s, old_p, old_o = old_trip
                if old_s == new_s and old_o == new_o:
                    matched_old_triples.add(old_trip)
                    found_mod = True
                    modified_relations.append({
                        "subject": new_rel.subject,
                        "old_predicate": old_rel.predicate,
                        "new_predicate": new_rel.predicate,
                        "object": new_rel.object,
                    })
                    sev, rationale = assign_severity(
                        [new_rel.subject, old_rel.predicate, new_rel.predicate, new_rel.object, new_rel.source_quote],
                        ChangeType.MODIFIED,
                    )
                    diff_items.append(
                        DiffItem(
                            element_type="edge",
                            change_type=ChangeType.MODIFIED,
                            canonical_name=f"({new_rel.subject})-[{new_rel.predicate}]->({new_rel.object})",
                            previous_name=f"({old_rel.subject})-[{old_rel.predicate}]->({old_rel.object})",
                            source_quote=new_rel.source_quote,
                            confidence=0.92,
                            severity=sev,
                            rationale=rationale,
                        )
                    )
                    break

            if not found_mod:
                added_relations.append([new_rel.subject, new_rel.predicate, new_rel.object])
                sev, rationale = assign_severity(
                    [new_rel.subject, new_rel.predicate, new_rel.object, new_rel.source_quote],
                    ChangeType.ADDED,
                )
                diff_items.append(
                    DiffItem(
                        element_type="edge",
                        change_type=ChangeType.ADDED,
                        canonical_name=f"({new_rel.subject})-[{new_rel.predicate}]->({new_rel.object})",
                        source_quote=new_rel.source_quote,
                        confidence=0.92,
                        severity=sev,
                        rationale=rationale,
                    )
                )

        # Removed relations: remaining unmatched old triples
        for old_trip, old_rel in old_canonical_rels.items():
            if old_trip not in matched_old_triples:
                removed_relations.append([old_rel.subject, old_rel.predicate, old_rel.object])
                sev, rationale = assign_severity(
                    [old_rel.subject, old_rel.predicate, old_rel.object, old_rel.source_quote],
                    ChangeType.REMOVED,
                )
                diff_items.append(
                    DiffItem(
                        element_type="edge",
                        change_type=ChangeType.REMOVED,
                        canonical_name=f"({old_rel.subject})-[{old_rel.predicate}]->({old_rel.object})",
                        source_quote=old_rel.source_quote,
                        confidence=0.92,
                        severity=sev,
                        rationale=rationale,
                    )
                )

        # Compute severity summary counts
        severity_counts = {
            SeverityLevel.CRITICAL.value: sum(1 for it in diff_items if it.severity == SeverityLevel.CRITICAL),
            SeverityLevel.HIGH.value: sum(1 for it in diff_items if it.severity == SeverityLevel.HIGH),
            SeverityLevel.MEDIUM.value: sum(1 for it in diff_items if it.severity == SeverityLevel.MEDIUM),
            SeverityLevel.LOW.value: sum(1 for it in diff_items if it.severity == SeverityLevel.LOW),
        }

        return DiffResult(
            from_version=old_data.version_id,
            to_version=new_data.version_id,
            added_entities=sorted(added_entities),
            removed_entities=sorted(removed_entities),
            renamed_entities=renamed_pairs,
            modified_entities=[],
            unchanged_entities=sorted(unchanged_entities),
            added_relations=added_relations,
            removed_relations=removed_relations,
            modified_relations=modified_relations,
            unchanged_relations=unchanged_relations,
            items=diff_items,
            severity_summary=severity_counts,
            narrative="",
        )
