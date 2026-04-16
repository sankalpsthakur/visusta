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
    def generate_structured(
        self,
        prompt: str,
        *,
        required_keys: list[str] | None = None,
        **kwargs: Any,
    ) -> dict:
        """Return a JSON-deserialized dict for *prompt*.

        If *required_keys* is provided, implementations must raise
        :class:`ValueError` when any listed key is missing from the parsed
        response. This is the contract callers use to prevent silent no-op
        fallbacks when the model ignores the requested schema.
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

    def generate_structured(
        self,
        prompt: str,
        *,
        required_keys: list[str] | None = None,
        **kwargs: Any,
    ) -> dict:
        """Call Gemini with response_mime_type=application/json.

        The SDK guarantees the response parses as JSON when this MIME type
        is set. We still run a defensive extraction step (strip markdown
        fences, trim preamble/postamble around the outermost braces) in
        case the model or SDK surface prose around the JSON payload.

        If *required_keys* is set, raises ValueError when any are missing
        so the caller's BackgroundTask worker can surface a real failure
        instead of silently falling back to a canned reply.
        """
        from google.genai import types  # local import — SDK only on GeminiLLM path

        config = types.GenerateContentConfig(response_mime_type="application/json")
        full_prompt = (
            f"{prompt}\n\n"
            "Respond with valid JSON only. No markdown fences, no preamble, no "
            "explanation outside the JSON object."
        )

        last_error: Exception | None = None
        for attempt in range(2):
            response = self._client.models.generate_content(
                model=self._model,
                contents=full_prompt,
                config=config,
            )
            text = (response.text or "").strip()
            # Strip markdown fences if the model ignored instructions and emitted them.
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            # Trim any preamble/postamble to the outermost JSON object.
            first_brace = text.find("{")
            last_brace = text.rfind("}")
            if first_brace != -1 and last_brace > first_brace:
                text = text[first_brace : last_brace + 1]

            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                last_error = exc
                # Retry once with a stricter reminder.
                full_prompt = (
                    "CRITICAL: your previous response was not valid JSON. Return "
                    "ONE JSON object only — no prose, no markdown, no keys outside "
                    "the object. Restart:\n\n" + prompt
                )
                continue

            if not isinstance(parsed, dict):
                last_error = ValueError(f"Expected JSON object, got {type(parsed).__name__}")
                full_prompt = (
                    "CRITICAL: return a JSON OBJECT (not an array or scalar). "
                    "Restart:\n\n" + prompt
                )
                continue

            if required_keys:
                missing = [k for k in required_keys if k not in parsed]
                if missing:
                    last_error = ValueError(
                        f"Response missing required keys: {missing}"
                    )
                    full_prompt = (
                        f"CRITICAL: your JSON must include these keys: "
                        f"{required_keys}. Restart:\n\n" + prompt
                    )
                    continue

            return parsed

        # Both attempts failed — surface the error so the background job
        # records status='failed' instead of silently succeeding with stub data.
        raise RuntimeError(
            f"LLM failed to return well-formed JSON after 2 attempts: {last_error}"
        )


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

    def generate_structured(
        self,
        prompt: str,
        *,
        required_keys: list[str] | None = None,
        **kwargs: Any,
    ) -> dict:
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
