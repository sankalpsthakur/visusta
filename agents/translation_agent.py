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
from .llm import LLMInterface, StubLLM, get_llm


FALLBACK_TRANSLATIONS: dict[str, dict[str, str]] = {
    "de": {
        "Executive Summary": "Zusammenfassung",
        "Critical Actions": "Kritische Maßnahmen",
        "Regulatory Changes": "Regulatorische Änderungen",
        "References": "Quellen",
        "Key Facts": "Kernfakten",
        "Action required": "Maßnahme erforderlich",
        "Deadline": "Frist",
        "No critical actions identified.": "Derzeit wurden keine kritischen Maßnahmen identifiziert.",
    },
    "sv": {
        "Executive Summary": "Sammanfattning",
        "Critical Actions": "Kritiska åtgärder",
        "Regulatory Changes": "Regulatoriska förändringar",
        "References": "Källor",
        "Key Facts": "Nyckelfakta",
        "Action required": "Åtgärd krävs",
        "Deadline": "Tidsfrist",
        "No critical actions identified.": "Inga kritiska åtgärder har identifierats.",
    },
    "fr": {
        "Executive Summary": "Résumé exécutif",
        "Critical Actions": "Actions critiques",
        "Regulatory Changes": "Évolutions réglementaires",
        "References": "Références",
        "Key Facts": "Points clés",
        "Action required": "Action requise",
        "Deadline": "Échéance",
        "No critical actions identified.": "Aucune action critique n'a été identifiée.",
    },
}


class TranslationAgent(Agent):
    def __init__(self, llm: LLMInterface | None = None):
        super().__init__("translation-agent")
        self._llm = llm if llm is not None else get_llm()

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
        translated_heading = heading

        if isinstance(self._llm, StubLLM):
            translated_blocks = [
                self._translate_block_fallback(block, target_locale, glossary)
                for block in copy.deepcopy(blocks)
            ]
            translated_heading = self._translate_text(heading, target_locale, glossary)
            confidence = 0.55 if target_locale != source_locale else 1.0
            low_conf_terms = [heading] if target_locale != source_locale else []
        else:
            prompt = self._build_prompt(heading, blocks, target_locale, source_locale, glossary)
            result = self._llm.generate_structured(prompt)
            translated_blocks = result.get("translated_blocks", [])
            confidence = result.get("confidence", 1.0)
            low_conf_terms = result.get("low_confidence_terms", [])

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
            "heading": translated_heading,
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
            str(b.get("text", b.get("content", "")))
            for b in blocks
            if b.get("text") or b.get("content")
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

    def _translate_block_fallback(
        self,
        block: dict,
        target_locale: str,
        glossary: dict,
    ) -> dict:
        if "text" in block and isinstance(block.get("text"), str):
            block["text"] = self._translate_text(block["text"], target_locale, glossary)
        elif "content" in block and isinstance(block.get("content"), str):
            block["content"] = self._translate_text(block["content"], target_locale, glossary)
        return block

    def _translate_text(self, text: str, target_locale: str, glossary: dict) -> str:
        translated = str(text)
        for source, replacement in FALLBACK_TRANSLATIONS.get(target_locale, {}).items():
            translated = translated.replace(source, replacement)
        for source, replacement in glossary.items():
            translated = translated.replace(str(source), str(replacement))
        return translated
