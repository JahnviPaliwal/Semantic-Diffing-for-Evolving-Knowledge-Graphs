"""
Extraction module: Pydantic-validated entity and relation extraction from documents,
with chunking for long texts, exponential backoff retries, deterministic temperature,
and SHA-256 disk caching.
"""
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple

from groq import Groq

from .config import config
from .models import ExtractedEntity, ExtractedRelation, ExtractionResult
from .utils.hashing import compute_text_hash
from .utils.text_chunker import TextChunk, chunk_text

logger = logging.getLogger(__name__)

EXTRACT_SYSTEM_PROMPT = """You are an expert knowledge extraction system.
Extract structured entities and their direct relationships from the provided text.

Return strictly a JSON object with this exact structure:
{
  "entities": [
    {
      "name": "Canonical Entity Name",
      "type": "Organization|Person|Product|Department|Role|Location|Concept|LegalTerm",
      "source_quote": "Verbatim short excerpt from the text containing this entity"
    }
  ],
  "relations": [
    {
      "subject": "Entity Name",
      "predicate": "short verb phrase (e.g. leads, partnered_with, governs, manages, rebranded_as)",
      "object": "Entity Name",
      "source_quote": "Verbatim sentence or clause expressing this relationship"
    }
  ]
}

Extraction Rules:
1. Extract named organizations, departments, people, roles, products, jurisdictions, and legal concepts.
2. Predicates must be concise verb phrases.
3. Every subject and object in "relations" must match an entry in "entities".
4. Every source_quote must be an exact, verbatim quote from the text.
5. Return ONLY the raw JSON object. No markdown fences, no explanatory prose.
"""

EXTRACT_USER_PROMPT = """Text to analyze:
\"\"\"
{TEXT}
\"\"\"
"""


class ExtractionManager:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        cache_dir: Optional[str] = None,
        enable_cache: Optional[bool] = None,
    ):
        self.api_key = api_key or config.groq_api_key or os.getenv("GROQ_API_KEY", "")
        self.model = model or config.groq_model
        self.fallback_models = config.fallback_models
        self.cache_dir = cache_dir or config.cache_dir
        self.enable_cache = config.enable_cache if enable_cache is None else enable_cache

        if self.enable_cache and not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)

        self._client: Optional[Groq] = None
        if self.api_key:
            self._client = Groq(api_key=self.api_key)

    def _get_client(self) -> Groq:
        if not self._client:
            key = self.api_key or os.getenv("GROQ_API_KEY", "")
            if not key:
                raise ValueError("Groq API key not provided and GROQ_API_KEY environment variable not set.")
            self._client = Groq(api_key=key)
        return self._client

    def _get_cache_path(self, doc_hash: str) -> str:
        return os.path.join(self.cache_dir, f"{doc_hash}.json")

    def _load_cached_result(self, doc_hash: str) -> Optional[ExtractionResult]:
        if not self.enable_cache:
            return None
        path = self._get_cache_path(doc_hash)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"Loaded cached extraction for hash {doc_hash[:8]}")
                    return ExtractionResult(**data)
            except Exception as e:
                logger.warning(f"Failed to read cache file {path}: {e}")
        return None

    def _save_cached_result(self, result: ExtractionResult) -> None:
        if not self.enable_cache:
            return
        path = self._get_cache_path(result.doc_hash)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(result.model_dump(), f, indent=2)
            logger.info(f"Saved extraction to cache: {path}")
        except Exception as e:
            logger.warning(f"Failed to write cache file {path}: {e}")

    def _call_groq_with_fallback(self, prompt: str) -> str:
        client = self._get_client()
        candidate_models = [self.model] + [m for m in self.fallback_models if m != self.model]

        last_error = None
        for mod in candidate_models:
            for attempt in range(config.max_retries):
                try:
                    resp = client.chat.completions.create(
                        model=mod,
                        temperature=config.temperature,
                        messages=[
                            {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                        ],
                    )
                    content = resp.choices[0].message.content or ""
                    # Strip reasoning/thinking tokens if returned by Qwen reasoning models
                    content = re.sub(r"<think>[\s\S]*?</think>", "", content, flags=re.DOTALL).strip()
                    # Strip markdown code blocks if returned
                    content = re.sub(r"^```(?:json)?\s*", "", content.strip(), flags=re.MULTILINE)
                    content = re.sub(r"```$", "", content.strip(), flags=re.MULTILINE)
                    return content.strip()
                except Exception as e:
                    last_error = e
                    wait_time = config.retry_backoff * (2 ** attempt)
                    logger.warning(f"LLM call failed with {mod} (attempt {attempt+1}/{config.max_retries}): {e}. Waiting {wait_time:.1f}s")
                    time.sleep(wait_time)
            logger.warning(f"All retries failed for model {mod}, falling back to next available model.")

        raise RuntimeError(f"All LLM models and retries failed. Last error: {last_error}")

    def _parse_llm_json(self, raw_json: str, chunk: TextChunk) -> Tuple[List[ExtractedEntity], List[ExtractedRelation]]:
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError as err:
            logger.error(f"Invalid JSON from LLM: {err}\nRaw snippet: {raw_json[:200]}")
            return [], []

        raw_entities = data.get("entities", [])
        raw_relations = data.get("relations", [])

        entities: List[ExtractedEntity] = []
        entity_name_set = set()

        for ent in raw_entities:
            if isinstance(ent, dict):
                name = str(ent.get("name", "")).strip()
                etype = str(ent.get("type", "Entity")).strip()
                quote = str(ent.get("source_quote", "")).strip()
            elif isinstance(ent, str):
                name = ent.strip()
                etype = "Entity"
                quote = ""
            else:
                continue

            if not name or name in entity_name_set:
                continue

            # Calculate character offsets if quote is present in the chunk
            offset_start = None
            offset_end = None
            if quote and quote in chunk.text:
                idx = chunk.text.find(quote)
                offset_start = chunk.start_char + idx
                offset_end = offset_start + len(quote)
            elif name in chunk.text:
                idx = chunk.text.find(name)
                offset_start = chunk.start_char + idx
                offset_end = offset_start + len(name)
                if not quote:
                    quote = name

            entity_name_set.add(name)
            entities.append(
                ExtractedEntity(
                    name=name,
                    type=etype,
                    source_quote=quote,
                    char_offset_start=offset_start,
                    char_offset_end=offset_end,
                    chunk_id=chunk.chunk_id,
                    confidence=0.95,
                )
            )

        relations: List[ExtractedRelation] = []
        for rel in raw_relations:
            if isinstance(rel, dict):
                s = str(rel.get("subject", "")).strip()
                p = str(rel.get("predicate", "")).strip()
                o = str(rel.get("object", "")).strip()
                q = str(rel.get("source_quote", "")).strip()
            elif isinstance(rel, (list, tuple)) and len(rel) >= 3:
                s = str(rel[0]).strip()
                p = str(rel[1]).strip()
                o = str(rel[2]).strip()
                q = ""
            else:
                continue

            if not s or not p or not o:
                continue

            # Ensure subject and object are registered entities
            if s not in entity_name_set:
                entity_name_set.add(s)
                entities.append(ExtractedEntity(name=s, type="Entity", source_quote="", chunk_id=chunk.chunk_id))
            if o not in entity_name_set:
                entity_name_set.add(o)
                entities.append(ExtractedEntity(name=o, type="Entity", source_quote="", chunk_id=chunk.chunk_id))

            relations.append(
                ExtractedRelation(
                    subject=s,
                    predicate=p,
                    object=o,
                    source_quote=q or f"{s} {p} {o}",
                    confidence=0.92,
                )
            )

        return entities, relations

    def _heuristic_fallback_extraction(self, chunk: TextChunk) -> Tuple[List[ExtractedEntity], List[ExtractedRelation]]:
        """Lightweight offline heuristic extraction when no Groq API key is present or LLM is unreachable."""
        entities: List[ExtractedEntity] = []
        relations: List[ExtractedRelation] = []
        seen_names = set()

        stop_words = {
            "The", "This", "That", "These", "Those", "A", "An", "In", "On", "At", "To", "For", "Of",
            "With", "By", "From", "About", "Against", "Between", "Into", "Through", "During",
            "Before", "After", "Above", "Below", "Under", "Further", "Then", "Once", "Here",
            "There", "When", "Where", "Why", "How", "All", "Any", "Both", "Each", "Few", "More",
            "Most", "Other", "Some", "Such", "No", "Nor", "Not", "Only", "Own", "Same", "So",
            "Than", "Too", "Very", "Can", "Will", "Just", "Should", "Now", "Section", "Article"
        }

        pattern = r'\b[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\b'
        matches = list(re.finditer(pattern, chunk.text))

        for m in matches:
            name = m.group().strip()
            if not name or name in stop_words or len(name) < 3:
                continue

            lower = name.lower()
            if any(term in lower for term in ["corp", "inc", "ltd", "llc", "company", "group", "holdings", "organization"]):
                etype = "Organization"
            elif any(term in lower for term in ["platform", "system", "service", "app", "pay", "tool", "api", "database"]):
                etype = "Product"
            elif any(term in lower for term in ["ceo", "cto", "cfo", "director", "officer", "manager", "president", "lead"]):
                etype = "Role"
            elif any(term in lower for term in ["lab", "department", "division", "team", "unit", "office"]):
                etype = "Department"
            elif any(term in lower for term in ["california", "delaware", "york", "francisco", "london", "europe", "us", "usa"]):
                etype = "Location"
            else:
                etype = "Entity"

            if name not in seen_names:
                seen_names.add(name)
                start_c = chunk.start_char + m.start()
                end_c = chunk.start_char + m.end()
                ent = ExtractedEntity(
                    name=name,
                    type=etype,
                    source_quote=name,
                    char_offset_start=start_c,
                    char_offset_end=end_c,
                    chunk_id=chunk.chunk_id,
                    confidence=0.85,
                )
                entities.append(ent)

        sentences = re.split(r'(?<=[.!?])\s+', chunk.text)
        known_predicates = [
            ("operates in", "operates_in"),
            ("headquartered in", "headquartered_in"),
            ("based in", "based_in"),
            ("rebranded as", "rebranded_as"),
            ("rebranded to", "rebranded_as"),
            ("develops", "develops"),
            ("developed", "develops"),
            ("launched", "launched"),
            ("leads", "leads"),
            ("led by", "led_by"),
            ("governed by", "governed_by"),
            ("partnered with", "partnered_with"),
            ("manages", "manages"),
            ("acquires", "acquires"),
            ("acquired", "acquires"),
            ("is a", "is_a"),
            ("works at", "works_at"),
        ]

        for sent in sentences:
            sent_str = sent.strip()
            if not sent_str:
                continue
            present = [e for e in entities if e.name in sent_str]
            if len(present) >= 2:
                for i in range(len(present) - 1):
                    subj = present[i].name
                    obj = present[i + 1].name
                    if subj == obj:
                        continue
                    sent_lower = sent_str.lower()
                    pred = "associated_with"
                    for phrase, canonical_pred in known_predicates:
                        if phrase in sent_lower:
                            pred = canonical_pred
                            break
                    relations.append(
                        ExtractedRelation(
                            subject=subj,
                            predicate=pred,
                            object=obj,
                            source_quote=sent_str,
                            confidence=0.80,
                        )
                    )

        return entities, relations

    def extract_from_text(self, text: str, version_id: str = "v1") -> ExtractionResult:
        """Process arbitrary document text with chunking, caching, and Pydantic validation."""
        text = text.strip()
        doc_hash = compute_text_hash(text)

        # 1. Check disk cache
        cached = self._load_cached_result(doc_hash)
        if cached:
            cached.version_id = version_id
            return cached

        # 2. Chunk text
        chunks = chunk_text(text, chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap)
        all_entities: List[ExtractedEntity] = []
        all_relations: List[ExtractedRelation] = []
        seen_entity_names = set()
        seen_relation_keys = set()

        for chunk in chunks:
            chunk_entities, chunk_relations = [], []
            has_key = bool(self.api_key or os.getenv("GROQ_API_KEY", ""))
            if has_key:
                try:
                    prompt = EXTRACT_USER_PROMPT.replace("{TEXT}", chunk.text)
                    raw_response = self._call_groq_with_fallback(prompt)
                    chunk_entities, chunk_relations = self._parse_llm_json(raw_response, chunk)
                except Exception as e:
                    logger.warning(f"Groq LLM extraction call failed ({e}). Falling back to offline heuristic extraction.")
                    chunk_entities, chunk_relations = self._heuristic_fallback_extraction(chunk)
            else:
                chunk_entities, chunk_relations = self._heuristic_fallback_extraction(chunk)

            for ent in chunk_entities:
                if ent.name not in seen_entity_names:
                    seen_entity_names.add(ent.name)
                    all_entities.append(ent)

            for rel in chunk_relations:
                key = (rel.subject, rel.predicate.lower(), rel.object)
                if key not in seen_relation_keys:
                    seen_relation_keys.add(key)
                    all_relations.append(rel)

        result = ExtractionResult(
            version_id=version_id,
            doc_hash=doc_hash,
            raw_text=text,
            entities=all_entities,
            relations=all_relations,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # 3. Cache result
        self._save_cached_result(result)
        return result

    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """Parse raw text from supported formats (.txt, .pdf, .docx)."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()

        elif ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                return "\n".join([page.extract_text() or "" for page in reader.pages])
            except ImportError:
                import fitz  # pymupdf fallback
                doc = fitz.open(file_path)
                return "\n".join([page.get_text() for page in doc])

        elif ext in [".docx", ".doc"]:
            import docx
            doc = docx.Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

        else:
            raise ValueError(f"Unsupported file format: {ext}. Supported formats are .txt, .pdf, .docx")
