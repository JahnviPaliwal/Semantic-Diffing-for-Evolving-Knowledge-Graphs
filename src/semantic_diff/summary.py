"""
Provenance-grounded natural-language summary generator.
Produces executive change reports citing verbatim source quotes and severity levels.
"""
import json
import logging
import os
import re
from typing import Any, Optional

from groq import Groq

from .config import config
from .models import DiffResult, SeverityLevel

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """You are a senior knowledge graph analyst and compliance intelligence specialist.

Summarize the structural and semantic changes detected between document snapshot '{FROM_VERSION}' and '{TO_VERSION}'.

Structure your response into:
1. Executive Overview: 2-3 sentences highlighting total changes, major shifts, and critical severity points.
2. High-Impact & Critical Changes: Detail any governance, leadership, jurisdiction, liability, or exclusivity changes with citations.
3. Structural Additions & Removals: Summarize newly added or removed departments, products, or relationships.
4. Rebranding & Renames: Note any entities renamed or modified.

Ground your summary strictly in the provided diff and include verbatim quotes where available.

Diff JSON:
{DIFF}
"""


def generate_template_summary(diff: DiffResult) -> str:
    """Generate a clean, deterministic markdown narrative without external LLM dependencies."""
    sev = diff.severity_summary
    crit = sev.get("CRITICAL", 0)
    high = sev.get("HIGH", 0)

    lines = []
    lines.append(f"### Executive Change Summary ({diff.from_version} → {diff.to_version})")
    lines.append(
        f"A comparison between snapshot **{diff.from_version}** and **{diff.to_version}** detected "
        f"**{len(diff.added_entities)} added**, **{len(diff.removed_entities)} removed**, and "
        f"**{len(diff.renamed_entities)} renamed** entities, alongside "
        f"**{len(diff.added_relations)} added** and **{len(diff.removed_relations)} removed** relationships."
    )

    if crit > 0 or high > 0:
        lines.append(
            f"\n> ⚠️ **Impact Alert**: Detected **{crit} Critical** and **{high} High** severity changes "
            f"impacting governance, legal obligations, or executive leadership."
        )

    if diff.renamed_entities:
        lines.append("\n**Entity Rebrandings & Renames:**")
        for rp in diff.renamed_entities:
            lines.append(f"- **{rp['from']}** was updated / renamed to **{rp['to']}**.")

    if diff.added_entities:
        lines.append("\n**Key Additions:**")
        for ent in diff.added_entities[:6]:
            matching = [it for it in diff.items if it.canonical_name == ent and it.source_quote]
            quote_str = f" (*\"{matching[0].source_quote}\"*)" if matching else ""
            lines.append(f"- Added entity: `{ent}`{quote_str}")

    if diff.removed_entities:
        lines.append("\n**Key Removals:**")
        for ent in diff.removed_entities[:6]:
            lines.append(f"- Removed entity: `{ent}`")

    if diff.modified_relations:
        lines.append("\n**Modified Relationships:**")
        for mr in diff.modified_relations[:5]:
            lines.append(
                f"- Relation between `{mr['subject']}` and `{mr['object']}` shifted from "
                f"`{mr['old_predicate']}` to `{mr['new_predicate']}`."
            )

    return "\n".join(lines)


class SummaryGenerator:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or config.groq_api_key or os.getenv("GROQ_API_KEY", "")
        self.model = model or config.groq_model
        self._client: Optional[Groq] = None

    def _get_client(self) -> Optional[Groq]:
        if not self._client and self.api_key:
            try:
                self._client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client for summarization: {e}")
        return self._client

    def generate_summary(self, diff: DiffResult) -> str:
        """Produce natural-language executive summary grounded in source quotes and severity."""
        client = self._get_client()
        if not client:
            return generate_template_summary(diff)

        # Simplify diff payload for prompt
        diff_payload = {
            "from_version": diff.from_version,
            "to_version": diff.to_version,
            "added_entities": diff.added_entities,
            "removed_entities": diff.removed_entities,
            "renamed_entities": diff.renamed_entities,
            "added_relations": diff.added_relations,
            "removed_relations": diff.removed_relations,
            "modified_relations": diff.modified_relations,
            "severity_summary": diff.severity_summary,
            "high_severity_items": [
                {
                    "element": it.canonical_name,
                    "change": it.change_type.value,
                    "severity": it.severity.value,
                    "quote": it.source_quote,
                    "rationale": it.rationale,
                }
                for it in diff.items
                if it.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH)
            ],
        }

        prompt = (
            SUMMARY_PROMPT
            .replace("{FROM_VERSION}", diff.from_version)
            .replace("{TO_VERSION}", diff.to_version)
            .replace("{DIFF}", json.dumps(diff_payload, indent=2))
        )

        try:
            resp = client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            narrative = (resp.choices[0].message.content or "").strip()
            # Strip reasoning/thinking tokens if returned by Qwen reasoning models
            narrative = re.sub(r"<think>[\s\S]*?</think>", "", narrative, flags=re.DOTALL).strip()
            return narrative or generate_template_summary(diff)
        except Exception as e:
            logger.warning(f"Groq LLM summarization call failed ({e}). Falling back to template narrative.")
            return generate_template_summary(diff)
