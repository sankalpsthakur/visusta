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
import json
import uuid
from typing import Any

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
    "nb": {
        "Executive Summary": "Sammendrag",
        "Critical Actions": "Kritiske tiltak",
        "Regulatory Changes": "Regulatoriske endringer",
        "References": "Kilder",
        "Key Facts": "Nøkkelfakta",
        "Action required": "Tiltak kreves",
        "Deadline": "Frist",
        "No critical actions identified.": "Ingen kritiske tiltak er identifisert.",
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
            translated_heading, translated_blocks, confidence, low_conf_terms = (
                self._translate_section_with_llm(
                    heading,
                    blocks,
                    target_locale,
                    source_locale,
                    glossary,
                )
            )

        # Stub/dev path stays permissive so local tests without a real LLM still
        # exercise the route. Real LLM path must fail loudly instead of silently
        # accepting untranslated English output.
        if not translated_blocks and isinstance(self._llm, StubLLM):
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
        *,
        retry: bool = False,
    ) -> str:
        payload = {
            "heading": heading,
            "blocks": [
                {
                    "block_type": block.get("block_type", block.get("type", "paragraph")),
                    "content": block.get("content", block.get("text", "")),
                }
                for block in blocks
            ],
        }
        glossary_hint = (
            "Glossary: " + ", ".join(f"{k}={v}" for k, v in list(glossary.items())[:10])
            if glossary
            else ""
        )
        retry_hint = (
            f"Your previous response left source-language text unchanged. Retry and ensure "
            f"the heading and every translatable block are actually in {target_locale}.\n"
            if retry
            else ""
        )
        return (
            f"Translate this draft section from {source_locale} to {target_locale}.\n"
            f"{retry_hint}"
            "Return one JSON object with exactly these keys:\n"
            '- "translated_heading": translated section heading in the target locale\n'
            '- "translated_blocks": translated blocks preserving original order and block types\n'
            '- "confidence": number from 0 to 1\n'
            '- "low_confidence_terms": array of source terms that may need review\n'
            "Rules:\n"
            "- Translate all user-facing text.\n"
            "- Preserve numbers, dates, URLs, citations, metadata, and proper nouns when appropriate.\n"
            "- For paragraph/heading blocks, keep content as a string.\n"
            "- For bullet_list blocks, keep content as an array of translated strings.\n"
            "- For table blocks, keep content as an array of rows, each row an array of translated cell strings.\n"
            f"{glossary_hint}\n"
            "Source section JSON:\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )

    def _translate_block_fallback(
        self,
        block: dict,
        target_locale: str,
        glossary: dict,
    ) -> dict:
        if "text" in block and isinstance(block.get("text"), str):
            block["text"] = self._translate_text(block["text"], target_locale, glossary)
        elif "content" in block:
            block["content"] = self._translate_content_fallback(
                block.get("content"),
                target_locale,
                glossary,
            )
        return block

    def _translate_text(self, text: str, target_locale: str, glossary: dict) -> str:
        translated = str(text)
        for source, replacement in FALLBACK_TRANSLATIONS.get(target_locale, {}).items():
            translated = translated.replace(source, replacement)
        for source, replacement in glossary.items():
            translated = translated.replace(str(source), str(replacement))
        return translated

    def _translate_content_fallback(
        self,
        content: Any,
        target_locale: str,
        glossary: dict,
    ) -> Any:
        if isinstance(content, str):
            return self._translate_text(content, target_locale, glossary)
        if isinstance(content, list):
            return [
                self._translate_content_fallback(item, target_locale, glossary)
                for item in content
            ]
        return content

    def _translate_section_with_llm(
        self,
        heading: str,
        blocks: list[dict],
        target_locale: str,
        source_locale: str,
        glossary: dict,
    ) -> tuple[str, list[dict], float, list[str]]:
        prompt = self._build_prompt(
            heading,
            blocks,
            target_locale,
            source_locale,
            glossary,
        )
        translated_heading, translated_blocks, confidence, low_conf_terms = self._parse_translation_result(
            self._llm.generate_structured(
                prompt,
                required_keys=[
                    "translated_heading",
                    "translated_blocks",
                    "confidence",
                    "low_confidence_terms",
                ],
            ),
            heading,
        )
        if not self._has_compatible_block_structure(blocks, translated_blocks) or self._looks_untranslated(
            heading,
            blocks,
            translated_heading,
            translated_blocks,
            target_locale,
            source_locale,
        ):
            self.log(
                f"Translation {source_locale}→{target_locale} came back malformed or unchanged; retrying with stricter prompt",
                level="warning",
            )
            retry_prompt = self._build_prompt(
                heading,
                blocks,
                target_locale,
                source_locale,
                glossary,
                retry=True,
            )
            translated_heading, translated_blocks, confidence, low_conf_terms = self._parse_translation_result(
                self._llm.generate_structured(
                    retry_prompt,
                    required_keys=[
                        "translated_heading",
                        "translated_blocks",
                        "confidence",
                        "low_confidence_terms",
                    ],
                ),
                heading,
            )
            if (
                not self._has_compatible_block_structure(blocks, translated_blocks)
                or self._looks_untranslated(
                    heading,
                    blocks,
                    translated_heading,
                    translated_blocks,
                    target_locale,
                    source_locale,
                )
            ):
                raise RuntimeError(
                    f"Translation {source_locale}→{target_locale} returned malformed or unchanged source-language content"
                )
        return translated_heading, translated_blocks, confidence, low_conf_terms

    def _parse_translation_result(
        self,
        result: dict[str, Any],
        heading: str,
    ) -> tuple[str, list[dict], float, list[str]]:
        required = [
            "translated_heading",
            "translated_blocks",
            "confidence",
            "low_confidence_terms",
        ]
        missing = [key for key in required if key not in result]
        if missing:
            raise RuntimeError(f"Translation response missing required keys: {missing}")
        translated_heading = str(result.get("translated_heading") or heading)
        translated_blocks = result.get("translated_blocks", [])
        if not isinstance(translated_blocks, list):
            raise RuntimeError("Translation returned no translated blocks")
        confidence = float(result.get("confidence", 1.0))
        low_conf_terms = list(result.get("low_confidence_terms", []))
        return translated_heading, translated_blocks, confidence, low_conf_terms

    def _looks_untranslated(
        self,
        heading: str,
        blocks: list[dict],
        translated_heading: str,
        translated_blocks: list[dict],
        target_locale: str,
        source_locale: str,
    ) -> bool:
        if target_locale == source_locale:
            return False
        source_parts = [
            self._render_content(block.get("content", block.get("text", "")))
            for block in blocks
        ]
        translated_parts = [
            self._render_content(block.get("content", block.get("text", "")))
            for block in translated_blocks
        ]
        compared = 0
        unchanged = 0
        for source_part, translated_part in zip(source_parts, translated_parts):
            if not source_part:
                continue
            compared += 1
            if source_part == translated_part:
                unchanged += 1
        if compared:
            return unchanged == compared
        return heading.strip() == translated_heading.strip()

    def _has_compatible_block_structure(
        self,
        source_blocks: list[dict],
        translated_blocks: list[dict],
    ) -> bool:
        if len(source_blocks) != len(translated_blocks):
            return False
        for source_block, translated_block in zip(source_blocks, translated_blocks):
            source_type = source_block.get("block_type", source_block.get("type", "paragraph"))
            translated_type = translated_block.get(
                "block_type",
                translated_block.get("type", "paragraph"),
            )
            if source_type != translated_type:
                return False
        return True

    def _render_content(self, content: Any) -> str:
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            rows = []
            for item in content:
                if isinstance(item, list):
                    row = " | ".join(str(cell) for cell in item if cell not in (None, ""))
                    if row:
                        rows.append(row)
                elif item not in (None, ""):
                    rows.append(str(item))
            return "\n".join(rows).strip()
        if content in (None, ""):
            return ""
        return str(content).strip()
