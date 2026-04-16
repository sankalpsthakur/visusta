"""
DraftComposerAgent — turns changelog + evidence + template sections into a
structured draft revision (list of DraftSection-compatible dicts).

Input context keys:
    changelog       list[dict]  — regulatory change entries
    evidence        list[dict]  — evidence records (optional)
    template_sections list[dict] — section definitions from a template version
    locale          str         — BCP-47 tag, e.g. "en", "de"

Output:
    {
        "sections": list[dict],  # each matches DraftSection shape
        "locale":   str,
        "log":      list[dict],
    }
"""
from __future__ import annotations

import uuid
from typing import Any

from .base import Agent
from .llm import LLMInterface, StubLLM


class DraftComposerAgent(Agent):
    def __init__(self, llm: LLMInterface | None = None):
        super().__init__("draft-composer")
        self._llm = llm or StubLLM()

    def run(self, context: dict) -> dict:
        changelog: list[dict] = context.get("changelog", [])
        evidence: list[dict] = context.get("evidence", [])
        template_sections: list[dict] = context.get("template_sections", [])
        locale: str = context.get("locale", "en")

        prompt = self._build_prompt(changelog, evidence, template_sections, locale)
        self.log(f"Composing draft for locale={locale}, changelog_entries={len(changelog)}")

        result: dict[str, Any] = self._llm.generate_structured(prompt)
        raw_sections: list[dict] = result.get("sections", [])

        sections = self._hydrate_sections(raw_sections, locale, template_sections)
        self.log(f"Composed {len(sections)} sections")

        return {"sections": sections, "locale": locale, "log": self.log_entries}

    # ── private ────────────────────────────────────────────────────────────

    def _build_prompt(
        self,
        changelog: list[dict],
        evidence: list[dict],
        template_sections: list[dict],
        locale: str,
    ) -> str:
        section_names = [s.get("heading", "") for s in template_sections]
        change_summaries = [
            f"- {c.get('title', c.get('description', 'change'))}"
            for c in changelog[:20]
        ]
        evidence_snippets = [
            f"- [{e.get('source_name', '')}] {e.get('snippet', '')}"
            for e in evidence[:10]
        ]
        return (
            f"compose changelog report in locale={locale}\n"
            f"Sections: {', '.join(section_names)}\n"
            f"Changes:\n" + "\n".join(change_summaries) + "\n"
            f"Evidence:\n" + "\n".join(evidence_snippets)
        )

    def _hydrate_sections(
        self,
        raw_sections: list[dict],
        locale: str,
        template_sections: list[dict],
    ) -> list[dict]:
        """Merge LLM output with template section definitions, adding IDs."""
        # Build a heading→template_section index for merging
        tpl_index = {
            s.get("heading", "").lower(): s
            for s in template_sections
        }

        hydrated = []
        for raw in raw_sections:
            heading = raw.get("heading", "")
            tpl = tpl_index.get(heading.lower(), {})
            hydrated.append({
                "section_id": str(uuid.uuid4()),
                "heading": heading or tpl.get("heading", ""),
                "locale": locale,
                "blocks": raw.get("blocks", []),
                "facts": raw.get("facts", []),
                "citations": raw.get("citations", []),
                "translation_status": "original",
                "approval_status": "pending",
                # Carry forward template metadata if present
                "template_section_id": tpl.get("section_id"),
            })

        # If LLM returned nothing, create a stub for each template section
        if not hydrated and template_sections:
            for tpl in template_sections:
                hydrated.append({
                    "section_id": str(uuid.uuid4()),
                    "heading": tpl.get("heading", ""),
                    "locale": locale,
                    "blocks": [{"type": "paragraph", "text": ""}],
                    "facts": [],
                    "citations": [],
                    "translation_status": "original",
                    "approval_status": "pending",
                    "template_section_id": tpl.get("section_id"),
                })

        return hydrated
