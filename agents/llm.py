"""
LLM interface abstraction for MARS agents.

Production uses GeminiLLM (Google Generative AI SDK).
StubLLM provides deterministic fallbacks for testing.
"""
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any


class LLMInterface(ABC):
    """Abstract interface for LLM backends."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Return a plain-text completion for *prompt*."""

    @abstractmethod
    def generate_structured(self, prompt: str, **kwargs: Any) -> dict:
        """Return a JSON-deserialized dict for *prompt*.

        Implementations must guarantee the return value is a dict.
        Callers handle KeyError / missing keys themselves.
        """


class GeminiLLM(LLMInterface):
    """Real LLM backend using Google GenAI SDK."""

    def __init__(self, model: str = "gemma-4-26b-a4b-it"):
        from google import genai
        self._client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        self._model = model

    def generate(self, prompt: str, **kwargs: Any) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        return response.text

    def generate_structured(self, prompt: str, **kwargs: Any) -> dict:
        response = self._client.models.generate_content(
            model=self._model,
            contents=f"{prompt}\n\nRespond with valid JSON only. No markdown, no explanation — just the JSON object.",
        )
        text = response.text.strip()
        # Handle potential markdown code blocks
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)


def get_llm(model: str = "gemma-4-26b-a4b-it") -> LLMInterface:
    """Return GeminiLLM if GOOGLE_API_KEY is set, otherwise StubLLM."""
    if os.environ.get("GOOGLE_API_KEY"):
        return GeminiLLM(model=model)
    return StubLLM()


class StubLLM(LLMInterface):
    """Deterministic stub for development and testing.

    Returns templated responses that match the expected shapes so that
    agents can be exercised without a real LLM backend.
    """

    def generate(self, prompt: str, **kwargs: Any) -> str:
        if "translate" in prompt.lower():
            return "[translated content]"
        if "chat" in prompt.lower() or "edit" in prompt.lower():
            return "Updated section content based on feedback."
        return "Generated content."

    def generate_structured(self, prompt: str, **kwargs: Any) -> dict:
        # ── draft-composer ─────────────────────────────────────────────────
        if "compose" in prompt.lower() or "changelog" in prompt.lower():
            return {
                "sections": [
                    {
                        "heading": "Executive Summary",
                        "blocks": [{"type": "paragraph", "text": "Stub executive summary."}],
                        "facts": [],
                        "citations": [],
                    },
                    {
                        "heading": "Critical Actions",
                        "blocks": [{"type": "paragraph", "text": "No critical actions identified."}],
                        "facts": [],
                        "citations": [],
                    },
                ]
            }
        # ── translation-agent ───────────────────────────────────────────────
        if "translat" in prompt.lower():
            return {
                "translated_blocks": [
                    {"type": "paragraph", "text": "[translated content]"}
                ],
                "confidence": 0.9,
                "low_confidence_terms": [],
            }
        # ── draft-chat ──────────────────────────────────────────────────────
        if "section" in prompt.lower() and "user" in prompt.lower():
            return {
                "updated_blocks": [
                    {"type": "paragraph", "text": "Updated section content based on feedback."}
                ],
                "explanation": "Applied requested changes.",
            }
        # ── source proposals ────────────────────────────────────────────────
        if "source" in prompt.lower() or "proposal" in prompt.lower():
            return {
                "proposals": [
                    {
                        "url": "https://eur-lex.europa.eu/stub",
                        "title": "Stub Regulation Proposal",
                        "publisher": "EUR-Lex",
                        "rationale": "Relevant to client ESG reporting obligations.",
                    }
                ]
            }
        return {}
