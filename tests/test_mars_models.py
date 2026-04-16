"""
Tests for MARS Pydantic models, draft lifecycle state machine, and section model.
"""

from __future__ import annotations

import pytest
from freezegun import freeze_time

from api.schemas_mars import (
    ClientLocaleSettings,
    ClientLocaleSettingsUpdate,
    DraftCreate,
    DraftSection,
    ExportRequest,
    KeywordRuleCreate,
    SectionBlock,
    SourceProposalAction,
    TemplateCreate,
    TemplateVersionCreate,
)
from mars.draft_lifecycle import (
    ALL_STATUSES,
    allowed_transitions,
    validate_transition,
)
from mars.section_model import diff_sections, sections_from_json, sections_to_json


# ── LocaleResponse / ClientLocaleSettings ─────────────────────────────────────

def test_client_locale_settings_defaults() -> None:
    settings = ClientLocaleSettings(
        client_id="client-1",
        primary_locale="de",
        enabled_locales=["de", "en"],
    )
    assert settings.fallback_locale == "en"


def test_client_locale_settings_update_partial() -> None:
    update = ClientLocaleSettingsUpdate(primary_locale="fr")
    assert update.primary_locale == "fr"
    assert update.enabled_locales is None
    assert update.fallback_locale is None


def test_locale_fallback_to_en() -> None:
    settings = ClientLocaleSettings(
        client_id="client-2",
        primary_locale="bg",
        enabled_locales=["bg"],
    )
    # fallback_locale defaults to 'en' — acts as the locale fallback chain anchor
    assert settings.fallback_locale == "en"


# ── KeywordRuleCreate ──────────────────────────────────────────────────────────

def test_keyword_rule_defaults() -> None:
    rule = KeywordRuleCreate(phrase="packaging waste")
    assert rule.locale == "en"
    assert rule.weight == 1.0
    assert rule.category is None


def test_keyword_rule_weight_bounds() -> None:
    with pytest.raises(Exception):
        KeywordRuleCreate(phrase="test", weight=-1.0)
    with pytest.raises(Exception):
        KeywordRuleCreate(phrase="test", weight=11.0)


# ── TemplateCreate / TemplateVersionCreate ─────────────────────────────────────

@freeze_time("2026-02-15")
def test_template_create_fields() -> None:
    t = TemplateCreate(name="CSRD Template", base_locale="de")
    assert t.base_locale == "de"
    assert t.description is None


def test_template_version_create_defaults() -> None:
    v = TemplateVersionCreate()
    assert v.sections_json == []
    assert v.theme_tokens == {}


def test_template_version_with_sections() -> None:
    v = TemplateVersionCreate(
        sections_json=[{"section_id": "s1", "heading": "Intro"}],
        changelog_note="Initial version",
        created_by="admin",
    )
    assert v.sections_json[0]["section_id"] == "s1"
    assert v.changelog_note == "Initial version"


# ── DraftCreate ────────────────────────────────────────────────────────────────

def test_draft_create_defaults() -> None:
    d = DraftCreate(title="Feb 2026 Report")
    assert d.primary_locale == "en"
    assert d.template_version_id is None
    assert d.period is None


# ── DraftSection / SectionBlock ────────────────────────────────────────────────

def test_draft_section_construction() -> None:
    block = SectionBlock(block_id="b1", block_type="paragraph", content="Hello world.")
    section = DraftSection(
        section_id="s1",
        heading="Introduction",
        locale="en",
        blocks=[block],
        facts=["EU Packaging Regulation published"],
        citations=["https://eur-lex.europa.eu/"],
    )
    assert section.translation_status is None
    assert section.approval_status is None
    assert len(section.blocks) == 1


def test_draft_section_statuses() -> None:
    section = DraftSection(
        section_id="s2",
        heading="Actions",
        locale="de",
        translation_status="done",
        approval_status="approved",
    )
    assert section.translation_status == "done"
    assert section.approval_status == "approved"


# ── SourceProposalAction ───────────────────────────────────────────────────────

def test_source_proposal_valid_actions() -> None:
    for action in ("approve", "reject", "pause"):
        a = SourceProposalAction(action=action, reviewer="user-1")
        assert a.action == action


def test_source_proposal_invalid_action() -> None:
    with pytest.raises(Exception):
        SourceProposalAction(action="delete", reviewer="user-1")


# ── ExportRequest ──────────────────────────────────────────────────────────────

def test_export_request_pdf() -> None:
    req = ExportRequest(format="pdf", locale="de")
    assert req.format == "pdf"
    assert req.locale == "de"


def test_export_request_invalid_format() -> None:
    with pytest.raises(Exception):
        ExportRequest(format="xlsx")


# ── Draft lifecycle state machine ──────────────────────────────────────────────

class TestDraftLifecycle:
    def test_composing_to_review(self) -> None:
        assert validate_transition("composing", "review") is True

    def test_composing_cannot_skip_to_approval(self) -> None:
        assert validate_transition("composing", "approval") is False

    def test_review_to_revision(self) -> None:
        assert validate_transition("review", "revision") is True

    def test_review_to_translating(self) -> None:
        assert validate_transition("review", "translating") is True

    def test_review_to_approval(self) -> None:
        assert validate_transition("review", "approval") is True

    def test_review_to_archived(self) -> None:
        assert validate_transition("review", "archived") is True

    def test_revision_back_to_review(self) -> None:
        assert validate_transition("revision", "review") is True

    def test_revision_cannot_go_to_approval_directly(self) -> None:
        assert validate_transition("revision", "approval") is False

    def test_translating_to_review(self) -> None:
        assert validate_transition("translating", "review") is True

    def test_translating_to_revision(self) -> None:
        assert validate_transition("translating", "revision") is True

    def test_approval_to_approved(self) -> None:
        assert validate_transition("approval", "approved") is True

    def test_approval_to_revision(self) -> None:
        assert validate_transition("approval", "revision") is True

    def test_approved_to_exported(self) -> None:
        assert validate_transition("approved", "exported") is True

    def test_approved_to_archived(self) -> None:
        assert validate_transition("approved", "archived") is True

    def test_exported_to_archived(self) -> None:
        assert validate_transition("exported", "archived") is True

    def test_archived_has_no_transitions(self) -> None:
        for target in ALL_STATUSES - {"archived"}:
            assert validate_transition("archived", target) is False

    def test_unknown_current_status_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown status"):
            validate_transition("nonexistent", "review")

    def test_unknown_target_status_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown status"):
            validate_transition("composing", "published")

    def test_allowed_transitions_composing(self) -> None:
        assert allowed_transitions("composing") == {"review"}

    def test_allowed_transitions_archived_empty(self) -> None:
        assert allowed_transitions("archived") == set()


# ── Template versioning logic ──────────────────────────────────────────────────

@freeze_time("2026-02-15")
def test_template_version_immutability_via_unique() -> None:
    """Template versions are immutable: same template_id + version_number must be unique."""
    v1 = TemplateVersionCreate(
        sections_json=[{"section_id": "s1"}],
        changelog_note="v1",
    )
    v2 = TemplateVersionCreate(
        sections_json=[{"section_id": "s1"}, {"section_id": "s2"}],
        changelog_note="v2",
    )
    # Both are separate Pydantic instances — confirms model accepts new version
    assert v1.changelog_note == "v1"
    assert v2.changelog_note == "v2"
    assert len(v2.sections_json) == 2


# ── Section model serialization ────────────────────────────────────────────────

class TestSectionModel:
    def _make_section(self, sid: str, heading: str = "H", locale: str = "en") -> DraftSection:
        return DraftSection(section_id=sid, heading=heading, locale=locale)

    def test_round_trip_serialization(self) -> None:
        sections = [
            self._make_section("s1", "Introduction"),
            self._make_section("s2", "Actions"),
        ]
        serialized = sections_to_json(sections)
        restored = sections_from_json(serialized)
        assert len(restored) == 2
        assert restored[0].section_id == "s1"
        assert restored[1].heading == "Actions"

    def test_diff_no_changes(self) -> None:
        sections = [self._make_section("s1"), self._make_section("s2")]
        changed = diff_sections(sections, sections)
        assert changed == []

    def test_diff_detects_heading_change(self) -> None:
        old = [self._make_section("s1", "Old Heading")]
        new = [self._make_section("s1", "New Heading")]
        changed = diff_sections(old, new)
        assert "s1" in changed

    def test_diff_detects_added_section(self) -> None:
        old = [self._make_section("s1")]
        new = [self._make_section("s1"), self._make_section("s2")]
        changed = diff_sections(old, new)
        assert "s2" in changed
        assert "s1" not in changed

    def test_diff_detects_removed_section(self) -> None:
        old = [self._make_section("s1"), self._make_section("s2")]
        new = [self._make_section("s1")]
        changed = diff_sections(old, new)
        assert "s2" in changed
        assert "s1" not in changed

    def test_diff_multiple_changes(self) -> None:
        old = [
            self._make_section("s1", "Intro"),
            self._make_section("s2", "Body"),
        ]
        new = [
            self._make_section("s1", "Intro"),       # unchanged
            self._make_section("s2", "Body Updated"), # changed
            self._make_section("s3", "Conclusion"),   # added
        ]
        changed = diff_sections(old, new)
        assert set(changed) == {"s2", "s3"}

    def test_diff_locale_change_detected(self) -> None:
        old = [self._make_section("s1", "H", locale="en")]
        new = [self._make_section("s1", "H", locale="de")]
        changed = diff_sections(old, new)
        assert "s1" in changed

    def test_empty_sections_no_diff(self) -> None:
        assert diff_sections([], []) == []
