"""
semantic_diff.py
Core logic for extracting entities & relations from text,
and computing a "semantic diff" between two knowledge graph snapshots.
"""

import re
import json
from groq import Groq

# ── Groq client (reads GROQ_API_KEY from environment) ──────────────────────
client = Groq()
MODEL = "llama-3.1-8b-instant"


# ── 1. Extract entities and relationships from raw text ─────────────────────
def extract_entities_and_relations(text: str) -> dict:
    """
    Calls the LLM to pull out named entities and the relationships between them.
    Returns a dict like:
        {
          "entities": ["Alice", "Acme Corp", ...],
          "relations": [["Alice", "works_at", "Acme Corp"], ...]
        }
    """
    prompt = f"""You are an information-extraction assistant.
Given the text below, extract:
1. Named entities (people, organisations, locations, products, dates).
2. Relationships between pairs of entities (subject, predicate, object).

Return ONLY valid JSON in this exact format – no prose, no markdown fences:
{{
  "entities": ["Entity1", "Entity2"],
  "relations": [["Subject", "predicate", "Object"]]
}}

Text:
\"\"\"
{text[:3000]}
\"\"\"
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if present
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Return empty structure if parsing fails
        data = {"entities": [], "relations": []}

    return data


# ── 2. Compute diff between two graph snapshots ─────────────────────────────
def compute_diff(old_data: dict, new_data: dict) -> dict:
    """
    Compares two extraction results and returns what was added/removed.

    Parameters
    ----------
    old_data : dict  – previous snapshot {"entities": [...], "relations": [...]}
    new_data : dict  – new snapshot

    Returns
    -------
    dict with keys: added_entities, removed_entities,
                    added_relations, removed_relations
    """
    old_entities = set(old_data.get("entities", []))
    new_entities = set(new_data.get("entities", []))

    # Convert relation lists to tuples so they can live in a set
    old_relations = {tuple(r) for r in old_data.get("relations", [])}
    new_relations = {tuple(r) for r in new_data.get("relations", [])}

    return {
        "added_entities": sorted(new_entities - old_entities),
        "removed_entities": sorted(old_entities - new_entities),
        "added_relations": [list(r) for r in (new_relations - old_relations)],
        "removed_relations": [list(r) for r in (old_relations - new_relations)],
    }


# ── 3. Generate a human-readable diff summary via LLM ──────────────────────
def summarise_diff(diff: dict) -> str:
    """
    Asks the LLM to write a short natural-language summary of the diff.
    """
    prompt = f"""You are a knowledge-graph analyst.
Summarise the following knowledge-graph diff in 3-5 plain English sentences.
Highlight the most important changes.

Diff (JSON):
{json.dumps(diff, indent=2)}
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()
