"""
backend/semantic_diff.py
Entity/relation extraction via Groq + graph diff computation + LLM summary.
"""
import re, json
from groq import Groq

MODEL = 'llama-3.3-70b-versatile'

EXTRACT_PROMPT = """You are an information-extraction system.

Given the text below, extract:
1. Named entities (people, organisations, locations, products, departments, roles, dates).
2. Relationships between pairs of entities as (subject, predicate, object) triples.

Return ONLY valid JSON in this exact format — no prose, no markdown fences:
{
  "entities": ["Entity1", "Entity2"],
  "relations": [["Subject", "predicate", "Object"]]
}

Rules:
- Entities must be meaningful, specific nouns or noun phrases.
- Predicates must be short verb phrases (e.g. "leads", "located_in", "partnered_with").
- Include only relations where both subject and object appear in the entity list.

Text:
\"\"\"
{TEXT}
\"\"\"
"""

SUMMARY_PROMPT = """You are a knowledge-graph analyst.

Summarise the following knowledge-graph diff in 3–5 clear sentences.
Highlight the most significant structural changes — new entities, removed entities, and key relationship shifts.
Be specific and name the entities that changed.

Diff (JSON):
{DIFF}
"""


def _client(api_key: str) -> Groq:
    return Groq(api_key=api_key)


def extract_entities_and_relations(text: str, api_key: str) -> dict:
    """Call Groq LLM to extract entities and relations from document text."""
    prompt = EXTRACT_PROMPT.replace('{TEXT}', text[:4000])
    client = _client(api_key)
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[{'role': 'user', 'content': prompt}],
    )
    raw = resp.choices[0].message.content.strip()
    # Strip markdown fences if present
    raw = re.sub(r'^```[a-z]*\n?', '', raw)
    raw = re.sub(r'\n?```$', '', raw)
    try:
        data = json.loads(raw)
        # Normalise: ensure both keys exist
        data.setdefault('entities', [])
        data.setdefault('relations', [])
        # Filter relations to only those where both nodes exist
        entity_set = set(data['entities'])
        data['relations'] = [
            r for r in data['relations']
            if len(r) == 3 and r[0] in entity_set and r[2] in entity_set
        ]
        return data
    except json.JSONDecodeError:
        return {'entities': [], 'relations': []}


def compute_diff(old_data: dict, new_data: dict) -> dict:
    """Compute set-difference between two KG snapshots."""
    old_ents = set(old_data.get('entities', []))
    new_ents = set(new_data.get('entities', []))
    old_rels = {tuple(r) for r in old_data.get('relations', []) if len(r) == 3}
    new_rels = {tuple(r) for r in new_data.get('relations', []) if len(r) == 3}

    return {
        'added_entities':    sorted(new_ents - old_ents),
        'removed_entities':  sorted(old_ents - new_ents),
        'unchanged_entities': sorted(old_ents & new_ents),
        'added_relations':   [list(r) for r in (new_rels - old_rels)],
        'removed_relations': [list(r) for r in (old_rels - new_rels)],
        'unchanged_relations': [list(r) for r in (old_rels & new_rels)],
    }


def summarise_diff(diff: dict, api_key: str) -> str:
    """Ask the LLM to write a plain-English summary of the diff."""
    prompt = SUMMARY_PROMPT.replace('{DIFF}', json.dumps(diff, indent=2))
    client = _client(api_key)
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.3,
        messages=[{'role': 'user', 'content': prompt}],
    )
    return resp.choices[0].message.content.strip()
