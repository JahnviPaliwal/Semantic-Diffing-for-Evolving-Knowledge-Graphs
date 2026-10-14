"""
Hybrid Entity and Relation Resolution Engine.
Combines linguistic name normalization, sentence-transformers embedding similarity,
fuzzy string matching, and an LLM verification step for borderline entity pairs.
Distinguishes RENAMED / MODIFIED entities and relations from truly ADDED / REMOVED ones.
"""
import json
import logging
import os
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .config import config
from .models import ExtractedEntity, ResolvedEntity

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = None


def get_embedding_model():
    """Lazy-load the sentence-transformers embedding model with safe fallback."""
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        if os.getenv("DISABLE_HEAVY_EMBEDDINGS", "").lower() in ("1", "true", "yes"):
            _EMBEDDING_MODEL = False
            return _EMBEDDING_MODEL
        try:
            from sentence_transformers import SentenceTransformer
            _EMBEDDING_MODEL = SentenceTransformer(config.embedding_model_name)
            logger.info(f"Loaded sentence-transformers model: {config.embedding_model_name}")
        except Exception as e:
            logger.warning(f"Could not load sentence-transformers model ({e}). Using lexical fallback.")
            _EMBEDDING_MODEL = False
    return _EMBEDDING_MODEL


def normalize_name(name: str) -> str:
    """Normalize entity names: lowercase, strip punctuation and common organizational suffixes."""
    if not name:
        return ""
    text = name.strip().lower()
    # Remove punctuation
    text = re.sub(r"[^\w\s-]", "", text)
    # Strip common corporate and organizational suffixes
    suffixes = [
        r"\bcorp\b", r"\bcorporation\b", r"\binc\b", r"\bincorporated\b",
        r"\bllc\b", r"\bltd\b", r"\blimited\b", r"\bco\b", r"\bcompany\b",
        r"\bdept\b", r"\bdepartment\b", r"\bgroup\b", r"\bdivision\b"
    ]
    for s in suffixes:
        text = re.sub(s, "", text)
    return " ".join(text.split())


def compute_fuzzy_similarity(s1: str, s2: str) -> float:
    """Compute character-level SequenceMatcher similarity between two strings."""
    n1 = normalize_name(s1)
    n2 = normalize_name(s2)
    if not n1 and not n2:
        return 1.0
    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0
    return SequenceMatcher(None, n1, n2).ratio()


def compute_embedding_similarity(s1: str, s2: str) -> float:
    """Compute cosine similarity of embeddings for two entity names."""
    model = get_embedding_model()
    if not model:
        # High quality lexical and character n-gram cosine fallback
        n1 = normalize_name(s1)
        n2 = normalize_name(s2)
        if n1 == n2:
            return 1.0
        # Character 3-grams
        def ngrams(text: str, n=3):
            return set(text[i:i+n] for i in range(max(1, len(text) - n + 1)))
        ng1 = ngrams(n1)
        ng2 = ngrams(n2)
        jaccard = len(ng1 & ng2) / max(1, len(ng1 | ng2))
        words1 = set(n1.split())
        words2 = set(n2.split())
        word_overlap = len(words1 & words2) / max(1, max(len(words1), len(words2)))
        return float(max(jaccard, word_overlap))

    vecs = model.encode([s1, s2], normalize_embeddings=True)
    sim = float(np.dot(vecs[0], vecs[1]))
    return max(0.0, min(1.0, sim))


def compute_hybrid_similarity(s1: str, s2: str) -> float:
    """Weighted combination of embedding similarity and fuzzy string match."""
    fuzzy = compute_fuzzy_similarity(s1, s2)
    # Exact or near-exact string match bypasses embedding computation
    if fuzzy > 0.95:
        return 1.0
    embed = compute_embedding_similarity(s1, s2)
    score = (config.embed_weight * embed) + (config.fuzzy_weight * fuzzy)
    return float(np.clip(score, 0.0, 1.0))


BORDERLINE_PROMPT = """You are an ontology alignment expert.
Determine whether the following two entity names refer to the same real-world entity,
a renaming/rebranding of the same entity, or two distinct entities.

Entity A: "{NAME_A}"
Entity B: "{NAME_B}"

Return ONLY JSON:
{
  "is_same_or_renamed": true/false,
  "confidence": 0.0 to 1.0,
  "reason": "short explanation"
}
"""


class EntityResolver:
    def __init__(self, groq_client: Optional[Any] = None):
        self.groq_client = groq_client

    def _verify_borderline_llm(self, name_a: str, name_b: str) -> Tuple[bool, float]:
        """Ask LLM to disambiguate borderline similarity scores."""
        if not self.groq_client:
            from groq import Groq
            api_key = config.groq_api_key or os.getenv("GROQ_API_KEY", "")
            if api_key:
                try:
                    self.groq_client = Groq(api_key=api_key)
                except Exception:
                    self.groq_client = None

        if not self.groq_client:
            # Fallback if no LLM available: check token containment
            t_a = set(normalize_name(name_a).split())
            t_b = set(normalize_name(name_b).split())
            is_same = bool(t_a & t_b) and (len(t_a & t_b) / max(len(t_a), len(t_b)) >= 0.5)
            return is_same, 0.75

        try:
            prompt = BORDERLINE_PROMPT.replace("{NAME_A}", name_a).replace("{NAME_B}", name_b)
            resp = self.groq_client.chat.completions.create(
                model=config.groq_model,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = (resp.choices[0].message.content or "").strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
            raw = re.sub(r"```$", "", raw, flags=re.MULTILINE)
            data = json.loads(raw)
            return bool(data.get("is_same_or_renamed", False)), float(data.get("confidence", 0.8))
        except Exception as e:
            logger.warning(f"Borderline LLM verification error ({e}). Falling back to similarity.")
            return False, 0.5

    def resolve_entities(
        self,
        old_entities: List[str],
        new_entities: List[str],
        old_quotes: Optional[Dict[str, str]] = None,
        new_quotes: Optional[Dict[str, str]] = None,
    ) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
        """
        Compare old entity set against new entity set.
        Returns:
            canonical_map: Dict mapping new_name -> old_canonical_name (if equivalent)
            renamed_pairs: List of dicts [{'from': old_name, 'to': new_name, 'confidence': float}]
        """
        canonical_map: Dict[str, str] = {}
        renamed_pairs: List[Dict[str, str]] = []

        unmatched_old = set(old_entities)
        unmatched_new = set(new_entities)

        # 0. Check provenance quotes for explicit rebranding/renaming patterns
        if new_quotes:
            for new_ent, quote in new_quotes.items():
                if not quote or new_ent not in unmatched_new:
                    continue
                q_lower = quote.lower()
                if any(cue in q_lower for cue in ["rebranded", "renamed", "formerly", "replaced", "merged into"]):
                    for old_ent in list(unmatched_old):
                        if old_ent.lower() in q_lower:
                            canonical_map[new_ent] = old_ent
                            renamed_pairs.append({
                                "from": old_ent,
                                "to": new_ent,
                                "confidence": 0.98,
                            })
                            unmatched_old.discard(old_ent)
                            unmatched_new.discard(new_ent)
                            break

        # 1. Exact string match or normalized name exact match
        for new_ent in list(unmatched_new):
            new_norm = normalize_name(new_ent)
            for old_ent in list(unmatched_old):
                if new_ent == old_ent or new_norm == normalize_name(old_ent):
                    canonical_map[new_ent] = old_ent
                    unmatched_new.discard(new_ent)
                    unmatched_old.discard(old_ent)
                    break

        # 2. Hybrid similarity check for remaining candidates
        for new_ent in list(unmatched_new):
            best_match = None
            best_score = 0.0

            for old_ent in unmatched_old:
                score = compute_hybrid_similarity(old_ent, new_ent)
                if score > best_score:
                    best_score = score
                    best_match = old_ent

            if best_match:
                if best_score >= config.similarity_high_threshold:
                    # High confidence rename or near-duplicate
                    canonical_map[new_ent] = best_match
                    renamed_pairs.append({
                        "from": best_match,
                        "to": new_ent,
                        "confidence": round(best_score, 3)
                    })
                    unmatched_old.remove(best_match)
                    unmatched_new.remove(new_ent)
                elif best_score >= config.similarity_borderline_threshold:
                    # Borderline: ask LLM verification
                    is_same, conf = self._verify_borderline_llm(best_match, new_ent)
                    if is_same:
                        canonical_map[new_ent] = best_match
                        renamed_pairs.append({
                            "from": best_match,
                            "to": new_ent,
                            "confidence": round(conf, 3)
                        })
                        unmatched_old.remove(best_match)
                        unmatched_new.remove(new_ent)

        return canonical_map, renamed_pairs

    def resolve_predicates(self, old_pred: str, new_pred: str) -> Tuple[bool, float]:
        """Check if two predicates are semantically synonymous."""
        p1 = normalize_name(old_pred)
        p2 = normalize_name(new_pred)
        if p1 == p2:
            return True, 1.0

        fuzzy = compute_fuzzy_similarity(p1, p2)
        if fuzzy >= config.relation_similarity_threshold:
            return True, fuzzy

        embed = compute_embedding_similarity(old_pred, new_pred)
        if embed >= config.relation_similarity_threshold:
            return True, embed

        return False, max(fuzzy, embed)
