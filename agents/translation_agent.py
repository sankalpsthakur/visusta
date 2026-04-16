"""
TranslationAgent — translates a list of DraftSection dicts into a target locale.

Preserves citations and facts (language-neutral); translates headings and block
text. Flags low-confidence terms in each section's translation_status field.

Input context keys:
    sections        list[dict]  — DraftSection-compatible dicts
    target_locale   str         — BCP-47 tag for destination language
    source_locale   str         — BCP-47 tag for source language (default "en")
    glossary        dict        — optional {term: translation} hints

Output:
    {
        "sections": list[dict],  # translated, new section_ids
        "target_locale": str,
        "low_confidence_count": int,
        "log": list[dict],
    }
"""
from __future__ import annotations

import copy
import uuid

from .base import Agent
from .llm import LLMInterface, StubLLM


class TranslationAgent(Agent):
    def __init__(self, llm: LLMInterface | None = None):
        super().__init__("translation-agent")
        self._llm = llm or StubLLM()

    def run(self, context: dict) -> dict:
        sections: list[dict] = context.get("sections", [])
        target_locale: str = context.get("target_locale", "en")
        source_locale: str = context.get("source_locale", "en")
        glossary: dict = context.get("glossary", {})

        self.log(
            f"Translating {len(sections)} sections "
            f"{source_locale}→{target_locale}"
        )

        translated = []
        low_confidence_count = 0

        for section in sections:
            t_section, low_conf = self._translate_section(
                section, target_locale, source_locale, glossary
            )
            translated.append(t_section)
            low_confidence_count += low_conf

        self.log(
            f"Translation complete; low_confidence_count={low_confidence_count}"
        )
        return {
            "sections": translated,
            "target_locale": target_locale,
            "low_confidence_count": low_confidence_count,
            "log": self.log_entries,
        }

    # ── private ────────────────────────────────────────────────────────────

    def _translate_section(
        self,
        section: dict,
        target_locale: str,
        source_locale: str,
        glossary: dict,
    ) -> tuple[dict, int]:
        blocks = section.get("blocks", [])
        heading = section.get("heading", "")

        prompt = self._build_prompt(heading, blocks, target_locale, source_locale, glossary)
        result = self._llm.generate_structured(prompt)

        translated_blocks = result.get("translated_blocks", [])
        confidence: float = result.get("confidence", 1.0)
        low_conf_terms: list[str] = result.get("low_confidence_terms", [])

        # Fall back to original blocks if LLM returned nothing
        if not translated_blocks:
            translated_blocks = copy.deepcopy(blocks)

        translation_status = (
            "low_confidence" if low_conf_terms or confidence < 0.75
            else "translated"
        )

        new_section = {
            **section,
            "section_id": str(uuid.uuid4()),
            "locale": target_locale,
            "blocks": translated_blocks,
            # facts/citations are language-neutral — preserve as-is
            "facts": section.get("facts", []),
            "citations": section.get("citations", []),
            "translation_status": translation_status,
            "approval_status": "pending",
        }

        return new_section, len(low_conf_terms)

    def _build_prompt(
        self,
        heading: str,
        blocks: list[dict],
        target_locale: str,
        source_locale: str,
        glossary: dict,
    ) -> str:
        block_texts = "\n".join(
            b.get("text", "") for b in blocks if b.get("text")
        )
        glossary_hint = (
            "Glossary: " + ", ".join(f"{k}={v}" for k, v in list(glossary.items())[:10])
            if glossary
            else ""
        )
        return (
            f"translat section from {source_locale} to {target_locale}\n"
            f"Heading: {heading}\n"
            f"Content:\n{block_texts}\n"
            f"{glossary_hint}"
        )
