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
import uuid

from .base import Agent
from .llm import LLMInterface, StubLLM


class DraftChatAgent(Agent):
    def __init__(self, llm: LLMInterface | None = None):
        super().__init__("draft-chat")
        self._llm = llm or StubLLM()

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

        prompt = self._build_prompt(target, user_message, history)
        result = self._llm.generate_structured(prompt)

        updated_blocks = result.get("updated_blocks", [])
        explanation: str = result.get("explanation", "")

        if not updated_blocks:
            updated_blocks = copy.deepcopy(target.get("blocks", []))

        new_section_id = str(uuid.uuid4())
        edited = {
            **target,
            "section_id": new_section_id,
            "blocks": updated_blocks,
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
        block_texts = "\n".join(
            b.get("text", "") for b in section.get("blocks", []) if b.get("text")
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
