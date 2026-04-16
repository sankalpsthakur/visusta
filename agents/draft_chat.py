"""
DraftChatAgent — applies a conversational edit to a specific section in a draft.

The agent takes the full section list, the ID of the section to edit, and a
user message describing the desired change. It produces an updated section list
where the targeted section has new blocks (new section_id) and the rest are
returned unchanged.

Input context keys:
    sections        list[dict]  — full DraftSection-compatible list
    section_id      str         — the section to edit
    user_message    str         — the user's edit instruction
    conversation_history list[dict]  — prior chat messages (optional)
                                        each: {"role": "user"|"assistant", "content": str}

Output:
    {
        "sections": list[dict],   # full list, target section replaced
        "edited_section_id": str, # new section_id of the replaced section
        "explanation": str,       # agent's explanation of the change
        "log": list[dict],
    }
"""
from __future__ import annotations

import copy
import re
import uuid

from .base import Agent
from .llm import LLMInterface, StubLLM, get_llm


class DraftChatAgent(Agent):
    def __init__(self, llm: LLMInterface | None = None):
        super().__init__("draft-chat")
        self._llm = llm if llm is not None else get_llm()

    def run(self, context: dict) -> dict:
        sections: list[dict] = context.get("sections", [])
        section_id: str = context.get("section_id", "")
        user_message: str = context.get("user_message", "")
        history: list[dict] = context.get("conversation_history", [])

        self.log(f"Chat edit requested for section_id={section_id!r}")

        target = self._find_section(sections, section_id)
        if target is None:
            self.log(f"Section {section_id!r} not found — returning unchanged", level="warning")
            return {
                "sections": sections,
                "edited_section_id": None,
                "explanation": f"Section {section_id!r} not found.",
                "log": self.log_entries,
            }

        if isinstance(self._llm, StubLLM):
            updated_blocks, explanation = self._rewrite_without_llm(target, user_message)
        else:
            prompt = self._build_prompt(target, user_message, history)
            result = self._llm.generate_structured(prompt)
            updated_blocks = result.get("updated_blocks", [])
            explanation = result.get("explanation", "")

        if not updated_blocks:
            updated_blocks = copy.deepcopy(target.get("blocks", []))

        # Normalize LLM block format → DB block format
        normalized = []
        for i, blk in enumerate(updated_blocks):
            normalized.append({
                "block_id": blk.get("block_id", f"b{i + 1}"),
                "block_type": blk.get("block_type", blk.get("type", "paragraph")),
                "content": blk.get("content", blk.get("text", "")),
                "metadata": blk.get("metadata", {}),
            })

        new_section_id = str(uuid.uuid4())
        edited = {
            **target,
            "section_id": new_section_id,
            "blocks": normalized,
            # Editing a section resets its approval
            "approval_status": "pending",
        }

        updated_sections = [
            edited if s.get("section_id") == section_id else s
            for s in sections
        ]

        self.log(f"Section edited; new_section_id={new_section_id}")
        return {
            "sections": updated_sections,
            "edited_section_id": new_section_id,
            "explanation": explanation,
            "log": self.log_entries,
        }

    # ── private ────────────────────────────────────────────────────────────

    def _find_section(self, sections: list[dict], section_id: str) -> dict | None:
        for s in sections:
            if s.get("section_id") == section_id:
                return s
        return None

    def _build_prompt(
        self,
        section: dict,
        user_message: str,
        history: list[dict],
    ) -> str:
        heading = section.get("heading", "")
        # Stored blocks normalize text under "content"; LLM/composer sometimes
        # emits "text". Read both so the model sees the actual section body.
        block_texts = "\n".join(
            (b.get("content") or b.get("text") or "")
            for b in section.get("blocks", [])
            if (b.get("content") or b.get("text"))
        )
        history_lines = "\n".join(
            f"{m['role'].upper()}: {m['content']}"
            for m in history[-6:]  # last 3 turns
            if isinstance(m, dict) and "role" in m and "content" in m
        )
        return (
            f"Edit section based on user request\n"
            f"Section heading: {heading}\n"
            f"Current content:\n{block_texts}\n"
            f"{'Conversation history:' + chr(10) + history_lines if history_lines else ''}\n"
            f"User: {user_message}"
        )

    def _rewrite_without_llm(
        self,
        section: dict,
        user_message: str,
    ) -> tuple[list[dict], str]:
        existing_blocks = copy.deepcopy(section.get("blocks", []))
        current_text = self._extract_text(existing_blocks)
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", current_text)
            if sentence.strip()
        ]
        lower = user_message.lower()

        if "bullet" in lower or "list" in lower:
            items = sentences or [current_text] if current_text else []
            return (
                [{"type": "bullet_list", "text": "\n".join(items[:6])}] if items else existing_blocks,
                "Reframed the section as a short bullet list.",
            )

        if any(token in lower for token in ("concise", "short", "brief", "summary")):
            chosen: list[str] = []
            for sentence in sentences:
                if not chosen:
                    chosen.append(sentence)
                    continue
                if re.search(r"\b(\d{4}-\d{2}-\d{2}|deadline|due|required|action|risk)\b", sentence, re.I):
                    chosen.append(sentence)
                if len(chosen) >= 2:
                    break
            compact = " ".join(chosen or sentences[:2])
            return (
                [{"type": "paragraph", "text": compact or current_text}] if (compact or current_text) else existing_blocks,
                "Condensed the section while keeping the key action and timing details.",
            )

        if any(token in lower for token in ("action", "deadline", "risk", "next step")):
            items = [
                sentence for sentence in sentences
                if re.search(r"\b(deadline|due|required|action|risk|\d{4}-\d{2}-\d{2})\b", sentence, re.I)
            ]
            if not items:
                items = sentences[:3]
            return (
                [{"type": "bullet_list", "text": "\n".join(items[:6])}] if items else existing_blocks,
                "Highlighted the action-oriented points and timing dependencies.",
            )

        if any(token in lower for token in ("expand", "detail", "elaborate")):
            additions = []
            for fact in section.get("facts", [])[:3]:
                additions.append(str(fact))
            for citation in section.get("citations", [])[:2]:
                label = citation.get("label", "") if isinstance(citation, dict) else str(citation)
                additions.append(f"Reference: {label}")
            expanded_blocks = existing_blocks
            if additions:
                expanded_blocks = existing_blocks + [{"type": "bullet_list", "text": "\n".join(additions)}]
            return expanded_blocks, "Expanded the section with the stored facts and supporting references."

        return existing_blocks, "Kept the section content intact because the instruction did not require a structural rewrite."

    def _extract_text(self, blocks: list[dict]) -> str:
        parts = []
        for block in blocks:
            text = block.get("text", block.get("content", ""))
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
        return " ".join(parts)
