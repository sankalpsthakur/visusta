"""Tests for MARS agentic orchestration layer (Phase 4).

These tests run with the system Python (no LLM API keys required).
All LLM calls go through StubLLM, which returns deterministic responses.
"""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from agents.llm import LLMInterface, StubLLM
from agents.draft_composer import DraftComposerAgent
from agents.translation_agent import TranslationAgent
from agents.draft_chat import DraftChatAgent
from agents.source_scout import SourceScoutAgent


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture()
def stub_llm() -> StubLLM:
    return StubLLM()


@pytest.fixture()
def sample_sections() -> list[dict]:
    return [
        {
            "section_id": str(uuid.uuid4()),
            "heading": "Executive Summary",
            "locale": "en",
            "blocks": [{"type": "paragraph", "text": "This is the executive summary."}],
            "facts": [],
            "citations": [],
            "translation_status": "original",
            "approval_status": "pending",
        },
        {
            "section_id": str(uuid.uuid4()),
            "heading": "Critical Actions",
            "locale": "en",
            "blocks": [{"type": "paragraph", "text": "Action required: comply by Q3."}],
            "facts": [{"label": "Deadline", "value": "2026-09-30"}],
            "citations": ["Regulation (EU) 2024/123"],
            "translation_status": "original",
            "approval_status": "pending",
        },
    ]


@pytest.fixture()
def sample_changelog() -> list[dict]:
    return [
        {
            "title": "CSRD reporting threshold lowered",
            "description": "Companies with >250 employees now in scope.",
            "severity": "high",
            "topic": "ghg",
        },
        {
            "title": "Packaging Regulation update",
            "description": "New recyclability targets for Q2 2026.",
            "severity": "medium",
            "topic": "packaging",
        },
    ]


@pytest.fixture()
def template_sections() -> list[dict]:
    return [
        {"section_id": "ts-1", "heading": "Executive Summary", "order": 1},
        {"section_id": "ts-2", "heading": "Critical Actions", "order": 2},
    ]


# ── LLMInterface ───────────────────────────────────────────────────────────────

class TestLLMInterface:
    def test_stub_llm_is_concrete(self, stub_llm):
        assert isinstance(stub_llm, LLMInterface)

    def test_stub_generate_returns_string(self, stub_llm):
        result = stub_llm.generate("any prompt")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_stub_generate_structured_returns_dict(self, stub_llm):
        result = stub_llm.generate_structured("any prompt")
        assert isinstance(result, dict)

    def test_stub_generate_translate_keyword(self, stub_llm):
        result = stub_llm.generate("please translate this text")
        assert "[translated" in result.lower() or isinstance(result, str)

    def test_stub_generate_structured_compose(self, stub_llm):
        result = stub_llm.generate_structured("compose changelog for locale=de")
        assert "sections" in result
        assert isinstance(result["sections"], list)

    def test_stub_generate_structured_translate(self, stub_llm):
        result = stub_llm.generate_structured("translat section from en to de")
        assert "translated_blocks" in result

    def test_stub_generate_structured_chat(self, stub_llm):
        result = stub_llm.generate_structured("Edit section based on user request")
        assert "updated_blocks" in result

    def test_stub_generate_structured_source(self, stub_llm):
        result = stub_llm.generate_structured("source proposal for client=acme")
        assert "proposals" in result
        assert isinstance(result["proposals"], list)


# ── DraftComposerAgent ─────────────────────────────────────────────────────────

class TestDraftComposerAgent:
    def test_agent_name(self):
        agent = DraftComposerAgent()
        assert agent.name == "draft-composer"

    def test_run_returns_sections(self, sample_changelog, template_sections):
        agent = DraftComposerAgent()
        result = agent.run({
            "changelog": sample_changelog,
            "evidence": [],
            "template_sections": template_sections,
            "locale": "en",
        })
        assert "sections" in result
        assert isinstance(result["sections"], list)
        assert len(result["sections"]) > 0

    def test_sections_have_required_fields(self, sample_changelog, template_sections):
        agent = DraftComposerAgent()
        result = agent.run({
            "changelog": sample_changelog,
            "template_sections": template_sections,
            "locale": "fr",
        })
        for sec in result["sections"]:
            assert "section_id" in sec
            assert "heading" in sec
            assert "locale" in sec
            assert "blocks" in sec
            assert "translation_status" in sec
            assert "approval_status" in sec

    def test_sections_carry_locale(self, sample_changelog):
        agent = DraftComposerAgent()
        result = agent.run({"changelog": sample_changelog, "locale": "de"})
        for sec in result["sections"]:
            assert sec["locale"] == "de"

    def test_sections_have_unique_ids(self, sample_changelog, template_sections):
        agent = DraftComposerAgent()
        result = agent.run({
            "changelog": sample_changelog,
            "template_sections": template_sections,
            "locale": "en",
        })
        ids = [s["section_id"] for s in result["sections"]]
        assert len(ids) == len(set(ids)), "section_ids must be unique"

    def test_empty_changelog_still_returns_stub_sections(self, template_sections):
        """When LLM returns nothing, agent stubs one section per template section."""
        mock_llm = MagicMock(spec=LLMInterface)
        mock_llm.generate_structured.return_value = {}  # empty
        agent = DraftComposerAgent(llm=mock_llm)
        result = agent.run({
            "changelog": [],
            "template_sections": template_sections,
            "locale": "en",
        })
        assert len(result["sections"]) == len(template_sections)

    def test_approval_status_defaults_pending(self, sample_changelog):
        agent = DraftComposerAgent()
        result = agent.run({"changelog": sample_changelog, "locale": "en"})
        for sec in result["sections"]:
            assert sec["approval_status"] == "pending"

    def test_translation_status_is_original(self, sample_changelog):
        agent = DraftComposerAgent()
        result = agent.run({"changelog": sample_changelog, "locale": "en"})
        for sec in result["sections"]:
            assert sec["translation_status"] == "original"

    def test_log_entries_populated(self, sample_changelog):
        agent = DraftComposerAgent()
        agent.run({"changelog": sample_changelog, "locale": "en"})
        assert len(agent.log_entries) >= 1

    def test_result_includes_log(self, sample_changelog):
        agent = DraftComposerAgent()
        result = agent.run({"changelog": sample_changelog, "locale": "en"})
        assert "log" in result
        assert isinstance(result["log"], list)

    def test_custom_llm_injected(self, sample_changelog):
        mock_llm = MagicMock(spec=LLMInterface)
        mock_llm.generate_structured.return_value = {
            "sections": [
                {
                    "heading": "Custom Section",
                    "blocks": [{"type": "paragraph", "text": "custom"}],
                    "facts": [],
                    "citations": [],
                }
            ]
        }
        agent = DraftComposerAgent(llm=mock_llm)
        result = agent.run({"changelog": sample_changelog, "locale": "en"})
        assert result["sections"][0]["heading"] == "Custom Section"
        mock_llm.generate_structured.assert_called_once()

    def test_prompt_includes_locale(self, sample_changelog):
        mock_llm = MagicMock(spec=LLMInterface)
        mock_llm.generate_structured.return_value = {}
        agent = DraftComposerAgent(llm=mock_llm)
        agent.run({"changelog": sample_changelog, "locale": "es"})
        call_args = mock_llm.generate_structured.call_args[0][0]
        assert "es" in call_args

    def test_prompt_includes_changelog_titles(self, sample_changelog):
        mock_llm = MagicMock(spec=LLMInterface)
        mock_llm.generate_structured.return_value = {}
        agent = DraftComposerAgent(llm=mock_llm)
        agent.run({"changelog": sample_changelog, "locale": "en"})
        call_args = mock_llm.generate_structured.call_args[0][0]
        assert "CSRD" in call_args or "Packaging" in call_args


# ── TranslationAgent ───────────────────────────────────────────────────────────

class TestTranslationAgent:
    def test_agent_name(self):
        agent = TranslationAgent()
        assert agent.name == "translation-agent"

    def test_run_returns_sections(self, sample_sections):
        agent = TranslationAgent()
        result = agent.run({
            "sections": sample_sections,
            "target_locale": "de",
            "source_locale": "en",
        })
        assert "sections" in result
        assert len(result["sections"]) == len(sample_sections)

    def test_target_locale_in_output(self, sample_sections):
        agent = TranslationAgent()
        result = agent.run({
            "sections": sample_sections,
            "target_locale": "fr",
        })
        assert result["target_locale"] == "fr"
        for sec in result["sections"]:
            assert sec["locale"] == "fr"

    def test_sections_get_new_ids(self, sample_sections):
        original_ids = {s["section_id"] for s in sample_sections}
        agent = TranslationAgent()
        result = agent.run({"sections": sample_sections, "target_locale": "de"})
        new_ids = {s["section_id"] for s in result["sections"]}
        assert original_ids.isdisjoint(new_ids), "Translated sections must have new IDs"

    def test_citations_preserved(self, sample_sections):
        agent = TranslationAgent()
        result = agent.run({"sections": sample_sections, "target_locale": "it"})
        for orig, translated in zip(sample_sections, result["sections"]):
            assert translated["citations"] == orig["citations"]

    def test_facts_preserved(self, sample_sections):
        agent = TranslationAgent()
        result = agent.run({"sections": sample_sections, "target_locale": "it"})
        for orig, translated in zip(sample_sections, result["sections"]):
            assert translated["facts"] == orig["facts"]

    def test_approval_status_reset_to_pending(self, sample_sections):
        # Simulate an approved section being translated
        sample_sections[0]["approval_status"] = "approved"
        agent = TranslationAgent()
        result = agent.run({"sections": sample_sections, "target_locale": "de"})
        for sec in result["sections"]:
            assert sec["approval_status"] == "pending"

    def test_translation_status_field_set(self, sample_sections):
        agent = TranslationAgent()
        result = agent.run({"sections": sample_sections, "target_locale": "de"})
        for sec in result["sections"]:
            assert sec["translation_status"] in ("translated", "low_confidence")

    def test_low_confidence_count_returned(self, sample_sections):
        agent = TranslationAgent()
        result = agent.run({"sections": sample_sections, "target_locale": "de"})
        assert "low_confidence_count" in result
        assert isinstance(result["low_confidence_count"], int)

    def test_empty_sections(self):
        agent = TranslationAgent()
        result = agent.run({"sections": [], "target_locale": "de"})
        assert result["sections"] == []
        assert result["low_confidence_count"] == 0

    def test_glossary_included_in_prompt(self, sample_sections):
        mock_llm = MagicMock(spec=LLMInterface)
        mock_llm.generate_structured.return_value = {"translated_blocks": [], "confidence": 1.0}
        agent = TranslationAgent(llm=mock_llm)
        agent.run({
            "sections": sample_sections,
            "target_locale": "de",
            "glossary": {"GHG": "THG"},
        })
        for call in mock_llm.generate_structured.call_args_list:
            prompt = call[0][0]
            assert "GHG" in prompt or "THG" in prompt

    def test_fallback_to_original_blocks_when_llm_returns_empty(self, sample_sections):
        mock_llm = MagicMock(spec=LLMInterface)
        mock_llm.generate_structured.return_value = {"translated_blocks": [], "confidence": 1.0}
        agent = TranslationAgent(llm=mock_llm)
        result = agent.run({"sections": sample_sections, "target_locale": "pl"})
        for orig, translated in zip(sample_sections, result["sections"]):
            assert translated["blocks"] == orig["blocks"]


# ── DraftChatAgent ─────────────────────────────────────────────────────────────

class TestDraftChatAgent:
    def test_agent_name(self):
        agent = DraftChatAgent()
        assert agent.name == "draft-chat"

    def test_run_returns_sections(self, sample_sections):
        target_id = sample_sections[0]["section_id"]
        agent = DraftChatAgent()
        result = agent.run({
            "sections": sample_sections,
            "section_id": target_id,
            "user_message": "Make this more concise.",
        })
        assert "sections" in result
        assert len(result["sections"]) == len(sample_sections)

    def test_only_target_section_changes_id(self, sample_sections):
        target_id = sample_sections[0]["section_id"]
        other_id = sample_sections[1]["section_id"]
        agent = DraftChatAgent()
        result = agent.run({
            "sections": sample_sections,
            "section_id": target_id,
            "user_message": "Be brief.",
        })
        new_ids = [s["section_id"] for s in result["sections"]]
        assert new_ids[0] != target_id, "Edited section should have new ID"
        assert new_ids[1] == other_id, "Other sections should keep their IDs"

    def test_edited_section_id_in_result(self, sample_sections):
        target_id = sample_sections[0]["section_id"]
        agent = DraftChatAgent()
        result = agent.run({
            "sections": sample_sections,
            "section_id": target_id,
            "user_message": "Add a risk factor.",
        })
        assert result["edited_section_id"] is not None
        ids = [s["section_id"] for s in result["sections"]]
        assert result["edited_section_id"] in ids

    def test_invalid_section_id_returns_unchanged_sections(self, sample_sections):
        agent = DraftChatAgent()
        result = agent.run({
            "sections": sample_sections,
            "section_id": "nonexistent-id",
            "user_message": "Edit this.",
        })
        assert result["sections"] == sample_sections
        assert result["edited_section_id"] is None

    def test_approval_status_reset_after_edit(self, sample_sections):
        sample_sections[0]["approval_status"] = "approved"
        target_id = sample_sections[0]["section_id"]
        agent = DraftChatAgent()
        result = agent.run({
            "sections": sample_sections,
            "section_id": target_id,
            "user_message": "Revise.",
        })
        edited = next(s for s in result["sections"] if s["section_id"] == result["edited_section_id"])
        assert edited["approval_status"] == "pending"

    def test_conversation_history_included_in_prompt(self, sample_sections):
        target_id = sample_sections[0]["section_id"]
        mock_llm = MagicMock(spec=LLMInterface)
        mock_llm.generate_structured.return_value = {"updated_blocks": [], "explanation": ""}
        agent = DraftChatAgent(llm=mock_llm)
        history = [
            {"role": "user", "content": "What is the deadline?"},
            {"role": "assistant", "content": "The deadline is Q3 2026."},
        ]
        agent.run({
            "sections": sample_sections,
            "section_id": target_id,
            "user_message": "Make this shorter.",
            "conversation_history": history,
        })
        prompt = mock_llm.generate_structured.call_args[0][0]
        assert "What is the deadline" in prompt or "deadline" in prompt.lower()

    def test_user_message_in_prompt(self, sample_sections):
        target_id = sample_sections[0]["section_id"]
        mock_llm = MagicMock(spec=LLMInterface)
        mock_llm.generate_structured.return_value = {"updated_blocks": [], "explanation": ""}
        agent = DraftChatAgent(llm=mock_llm)
        agent.run({
            "sections": sample_sections,
            "section_id": target_id,
            "user_message": "Add a specific risk metric.",
        })
        prompt = mock_llm.generate_structured.call_args[0][0]
        assert "Add a specific risk metric" in prompt

    def test_explanation_in_result(self, sample_sections):
        target_id = sample_sections[0]["section_id"]
        agent = DraftChatAgent()
        result = agent.run({
            "sections": sample_sections,
            "section_id": target_id,
            "user_message": "Summarize.",
        })
        assert "explanation" in result

    def test_fallback_blocks_when_llm_returns_empty(self, sample_sections):
        target_id = sample_sections[0]["section_id"]
        original_blocks = sample_sections[0]["blocks"]
        mock_llm = MagicMock(spec=LLMInterface)
        mock_llm.generate_structured.return_value = {"updated_blocks": [], "explanation": ""}
        agent = DraftChatAgent(llm=mock_llm)
        result = agent.run({
            "sections": sample_sections,
            "section_id": target_id,
            "user_message": "Edit.",
        })
        edited = next(s for s in result["sections"] if s["section_id"] == result["edited_section_id"])
        assert edited["blocks"] == original_blocks


# ── SourceScoutAgent (extended) ────────────────────────────────────────────────

class TestSourceScoutProposeSourcesMethod:
    def test_propose_sources_returns_proposals_list(self, tmp_path):
        agent = SourceScoutAgent()
        result = agent.propose_sources(client_id="test-client")
        assert "proposals" in result
        assert isinstance(result["proposals"], list)

    def test_propose_sources_proposals_have_required_fields(self, tmp_path):
        agent = SourceScoutAgent()
        result = agent.propose_sources(client_id="test-client", context={
            "topics": ["ghg", "packaging"],
            "jurisdictions": ["EU"],
        })
        for proposal in result["proposals"]:
            assert "url" in proposal
            assert "title" in proposal
            assert "publisher" in proposal
            assert "rationale" in proposal

    def test_propose_sources_result_has_log(self):
        agent = SourceScoutAgent()
        result = agent.propose_sources(client_id="test-client")
        assert "log" in result
        assert isinstance(result["log"], list)

    def test_propose_sources_uses_context_topics(self):
        mock_llm = MagicMock(spec=LLMInterface)
        mock_llm.generate_structured.return_value = {"proposals": []}
        agent = SourceScoutAgent(llm=mock_llm)
        agent.propose_sources(
            client_id="acme",
            context={"topics": ["water", "waste"], "jurisdictions": ["DE"]},
        )
        prompt = mock_llm.generate_structured.call_args[0][0]
        assert "water" in prompt or "waste" in prompt
        assert "DE" in prompt or "acme" in prompt

    def test_propose_sources_client_id_in_prompt(self):
        mock_llm = MagicMock(spec=LLMInterface)
        mock_llm.generate_structured.return_value = {"proposals": []}
        agent = SourceScoutAgent(llm=mock_llm)
        agent.propose_sources(client_id="gerold-foods")
        prompt = mock_llm.generate_structured.call_args[0][0]
        assert "gerold-foods" in prompt

    def test_propose_sources_logs_entries(self):
        agent = SourceScoutAgent()
        agent.propose_sources(client_id="test-client")
        assert len(agent.log_entries) >= 1

    def test_existing_run_method_unaffected(self, tmp_path, monkeypatch):
        """Ensure the original run() still works after adding propose_sources()."""
        import agents.source_scout as ss_module
        monkeypatch.setattr(ss_module, "PROJECT_ROOT", tmp_path)
        agent = SourceScoutAgent()
        result = agent.run({
            "client_id": "test-client",
            "urls": ["https://example.com/regulation"],
        })
        assert "evidence_ids" in result
        assert isinstance(result["evidence_ids"], list)

    def test_propose_sources_custom_llm(self):
        mock_llm = MagicMock(spec=LLMInterface)
        mock_llm.generate_structured.return_value = {
            "proposals": [
                {
                    "url": "https://custom.example.com",
                    "title": "Custom Proposal",
                    "publisher": "Custom Publisher",
                    "rationale": "Highly relevant.",
                }
            ]
        }
        agent = SourceScoutAgent(llm=mock_llm)
        result = agent.propose_sources(client_id="client-x")
        assert len(result["proposals"]) == 1
        assert result["proposals"][0]["title"] == "Custom Proposal"
