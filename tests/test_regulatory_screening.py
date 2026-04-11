"""
Tests for regulatory_screening.py

Frozen date: 2026-02-15 to make all date.today() calls deterministic.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time

from regulatory_screening import (
    ChangeDetail,
    ChangelogEntry,
    ChangeSeverity,
    ChangeType,
    FileSystemRegulationStore,
    GeographicScope,
    MonthlyChangelog,
    MonthlyScreeningInput,
    RegulationDiff,
    RegulationStatus,
    RegulatoryScreeningModule,
    ScreeningInputItem,
    TopicCategory,
    TopicChangeStatus,
)

from tests.conftest import (
    FROZEN_DATE,
    make_monthly_screening,
    make_screening_item,
)


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _make_module(tmp_path: Path, config: dict | None = None) -> RegulatoryScreeningModule:
    store = FileSystemRegulationStore(tmp_path / "regulatory_data")
    return RegulatoryScreeningModule(store=store, config=config or {})


def _make_diff(
    regulation_id: str = "REG-001",
    changes: list[tuple[str, object, object]] | None = None,
) -> RegulationDiff:
    """Build a RegulationDiff from (field, old, new) tuples."""
    diff = RegulationDiff(
        regulation_id=regulation_id,
        previous_version_date=date(2026, 1, 1),
        current_version_date=date(2026, 2, 1),
    )
    for field, old, new in (changes or []):
        diff.add_change(field, old, new)
    return diff


def _make_entry(
    change_type: ChangeType = ChangeType.NO_CHANGE,
    enforcement_date: date | None = None,
    current_status: RegulationStatus = RegulationStatus.PROPOSED,
) -> ChangelogEntry:
    return ChangelogEntry(
        regulation_id="REG-001",
        title="Test Regulation",
        topic=TopicCategory.GHG,
        change_type=change_type,
        severity=ChangeSeverity.INFO,
        current_status=current_status,
        enforcement_date=enforcement_date,
    )


# ═══════════════════════════════════════════════════════════════════════════
# _compare_regulations
# ═══════════════════════════════════════════════════════════════════════════

class TestCompareRegulations:

    def setup_method(self):
        # Module isn't strictly needed — we call the private method directly
        # via a minimal instance; store is a MagicMock so no FS needed.
        self.module = RegulatoryScreeningModule(store=MagicMock())

    def test_identical_regulations_produce_no_diff(self):
        reg = make_screening_item()
        diff = self.module._compare_regulations(reg, reg)
        assert not diff.has_changes()

    def test_status_change_detected(self):
        old = make_screening_item(current_status=RegulationStatus.PROPOSED)
        new = make_screening_item(current_status=RegulationStatus.LAW_PASSED)
        diff = self.module._compare_regulations(old, new)
        assert diff.has_changes()
        fields = {c.field_name for c in diff.changes}
        assert "status" in fields

    def test_status_old_new_values_are_enum_members(self):
        old = make_screening_item(current_status=RegulationStatus.PROPOSED)
        new = make_screening_item(current_status=RegulationStatus.LAW_PASSED)
        diff = self.module._compare_regulations(old, new)
        status_change = next(c for c in diff.changes if c.field_name == "status")
        assert status_change.old_value == RegulationStatus.PROPOSED
        assert status_change.new_value == RegulationStatus.LAW_PASSED

    def test_title_change_detected(self):
        old = make_screening_item(title="Old Title")
        new = make_screening_item(title="New Title")
        diff = self.module._compare_regulations(old, new)
        fields = {c.field_name for c in diff.changes}
        assert "title" in fields

    def test_effective_date_change_detected(self):
        old = make_screening_item(effective_date=date(2026, 6, 1))
        new = make_screening_item(effective_date=date(2026, 9, 1))
        diff = self.module._compare_regulations(old, new)
        fields = {c.field_name for c in diff.changes}
        assert "effective_date" in fields

    def test_enforcement_date_change_detected(self):
        old = make_screening_item(enforcement_date=date(2026, 6, 1))
        new = make_screening_item(enforcement_date=date(2026, 12, 1))
        diff = self.module._compare_regulations(old, new)
        fields = {c.field_name for c in diff.changes}
        assert "enforcement_date" in fields

    def test_description_change_detected(self):
        old = make_screening_item(description="Original description text for compliance.")
        new = make_screening_item(description="Updated description text for compliance changes.")
        diff = self.module._compare_regulations(old, new)
        fields = {c.field_name for c in diff.changes}
        assert "description" in fields

    def test_geographic_scope_change_detected(self):
        old = make_screening_item(geographic_scope=GeographicScope.NATIONAL)
        new = make_screening_item(geographic_scope=GeographicScope.REGIONAL)
        diff = self.module._compare_regulations(old, new)
        fields = {c.field_name for c in diff.changes}
        assert "geographic_scope" in fields

    def test_applicable_countries_change_detected(self):
        old = make_screening_item(applicable_countries=["DE"])
        new = make_screening_item(applicable_countries=["DE", "FR"])
        diff = self.module._compare_regulations(old, new)
        fields = {c.field_name for c in diff.changes}
        assert "applicable_countries" in fields

    def test_applicable_countries_same_set_order_independent(self):
        old = make_screening_item(applicable_countries=["DE", "FR"])
        new = make_screening_item(applicable_countries=["FR", "DE"])
        diff = self.module._compare_regulations(old, new)
        # Order-independent set comparison — no diff expected
        fields = {c.field_name for c in diff.changes}
        assert "applicable_countries" not in fields

    def test_regulation_id_preserved_in_diff(self):
        old = make_screening_item(regulation_id="REG-XYZ")
        new = make_screening_item(regulation_id="REG-XYZ", title="New Title")
        diff = self.module._compare_regulations(old, new)
        assert diff.regulation_id == "REG-XYZ"

    def test_multiple_fields_changed_simultaneously(self):
        old = make_screening_item(
            current_status=RegulationStatus.PROPOSED,
            enforcement_date=date(2026, 6, 1),
        )
        new = make_screening_item(
            current_status=RegulationStatus.LAW_PASSED,
            enforcement_date=date(2026, 9, 1),
        )
        diff = self.module._compare_regulations(old, new)
        fields = {c.field_name for c in diff.changes}
        assert "status" in fields
        assert "enforcement_date" in fields


# ═══════════════════════════════════════════════════════════════════════════
# _classify_change_type
# ═══════════════════════════════════════════════════════════════════════════

class TestClassifyChangeType:

    def setup_method(self):
        self.module = RegulatoryScreeningModule(store=MagicMock())

    def test_new_status_law_passed_returns_promoted(self):
        diff = _make_diff(changes=[
            ("status", RegulationStatus.PROPOSED, RegulationStatus.LAW_PASSED),
        ])
        assert self.module._classify_change_type(diff) == ChangeType.STATUS_PROMOTED_TO_LAW

    def test_new_status_expired_from_law_returns_law_expired(self):
        diff = _make_diff(changes=[
            ("status", RegulationStatus.LAW_PASSED, RegulationStatus.EXPIRED),
        ])
        assert self.module._classify_change_type(diff) == ChangeType.LAW_EXPIRED

    def test_new_status_repealed_from_law_returns_law_expired(self):
        diff = _make_diff(changes=[
            ("status", RegulationStatus.LAW_PASSED, RegulationStatus.REPEALED),
        ])
        assert self.module._classify_change_type(diff) == ChangeType.LAW_EXPIRED

    def test_new_status_expired_from_non_law_returns_regulation_ended(self):
        diff = _make_diff(changes=[
            ("status", RegulationStatus.PROPOSED, RegulationStatus.EXPIRED),
        ])
        assert self.module._classify_change_type(diff) == ChangeType.REGULATION_ENDED

    def test_status_advancing_from_discussion_to_amendment(self):
        diff = _make_diff(changes=[
            (
                "status",
                RegulationStatus.CHANGE_UNDER_DISCUSSION,
                RegulationStatus.AMENDMENT_IN_PROGRESS,
            ),
        ])
        assert self.module._classify_change_type(diff) == ChangeType.STATUS_ADVANCING

    def test_law_being_amended_from_passed_to_amendment(self):
        diff = _make_diff(changes=[
            (
                "status",
                RegulationStatus.LAW_PASSED,
                RegulationStatus.AMENDMENT_IN_PROGRESS,
            ),
        ])
        assert self.module._classify_change_type(diff) == ChangeType.LAW_BEING_AMENDED

    def test_effective_date_change_returns_timeline_updated(self):
        diff = _make_diff(changes=[
            ("effective_date", date(2026, 6, 1), date(2026, 9, 1)),
        ])
        assert self.module._classify_change_type(diff) == ChangeType.TIMELINE_UPDATED

    def test_enforcement_date_change_returns_timeline_updated(self):
        diff = _make_diff(changes=[
            ("enforcement_date", date(2026, 6, 1), date(2026, 12, 1)),
        ])
        assert self.module._classify_change_type(diff) == ChangeType.TIMELINE_UPDATED

    def test_review_deadline_change_returns_timeline_updated(self):
        diff = _make_diff(changes=[
            ("review_deadline", date(2026, 3, 1), date(2026, 6, 1)),
        ])
        assert self.module._classify_change_type(diff) == ChangeType.TIMELINE_UPDATED

    def test_description_change_returns_content_updated(self):
        diff = _make_diff(changes=[
            ("description", "old text", "new text"),
        ])
        assert self.module._classify_change_type(diff) == ChangeType.CONTENT_UPDATED

    def test_requirements_change_returns_content_updated(self):
        diff = _make_diff(changes=[
            ("requirements", "old requirements", "new requirements"),
        ])
        assert self.module._classify_change_type(diff) == ChangeType.CONTENT_UPDATED

    def test_title_change_returns_metadata_updated(self):
        diff = _make_diff(changes=[
            ("title", "Old Title", "New Title"),
        ])
        assert self.module._classify_change_type(diff) == ChangeType.METADATA_UPDATED

    def test_geographic_scope_change_returns_metadata_updated(self):
        diff = _make_diff(changes=[
            ("geographic_scope", GeographicScope.NATIONAL, GeographicScope.REGIONAL),
        ])
        assert self.module._classify_change_type(diff) == ChangeType.METADATA_UPDATED

    def test_status_takes_priority_over_timeline_change(self):
        """Status field wins over concurrent timeline change."""
        diff = _make_diff(changes=[
            ("status", RegulationStatus.PROPOSED, RegulationStatus.LAW_PASSED),
            ("enforcement_date", date(2026, 6, 1), date(2026, 9, 1)),
        ])
        assert self.module._classify_change_type(diff) == ChangeType.STATUS_PROMOTED_TO_LAW


# ═══════════════════════════════════════════════════════════════════════════
# _calculate_severity
# ═══════════════════════════════════════════════════════════════════════════

@freeze_time(FROZEN_DATE)
class TestCalculateSeverity:

    def setup_method(self, *_):
        self.module = RegulatoryScreeningModule(store=MagicMock())

    def _entry(self, change_type, **kwargs):
        return _make_entry(change_type=change_type, **kwargs)

    def test_promoted_to_law_is_critical(self):
        entry = self._entry(ChangeType.STATUS_PROMOTED_TO_LAW)
        assert self.module._calculate_severity(entry) == ChangeSeverity.CRITICAL

    def test_law_expired_is_critical(self):
        entry = self._entry(ChangeType.LAW_EXPIRED)
        assert self.module._calculate_severity(entry) == ChangeSeverity.CRITICAL

    def test_timeline_with_enforcement_date_change_is_critical(self):
        diff = _make_diff(changes=[
            ("enforcement_date", date(2026, 6, 1), date(2026, 12, 1)),
        ])
        entry = self._entry(ChangeType.TIMELINE_UPDATED)
        assert self.module._calculate_severity(entry, diff) == ChangeSeverity.CRITICAL

    def test_timeline_with_effective_date_only_is_medium(self):
        diff = _make_diff(changes=[
            ("effective_date", date(2026, 6, 1), date(2026, 9, 1)),
        ])
        entry = self._entry(ChangeType.TIMELINE_UPDATED)
        assert self.module._calculate_severity(entry, diff) == ChangeSeverity.MEDIUM

    def test_status_advancing_is_high(self):
        entry = self._entry(ChangeType.STATUS_ADVANCING)
        assert self.module._calculate_severity(entry) == ChangeSeverity.HIGH

    def test_law_being_amended_is_high(self):
        entry = self._entry(ChangeType.LAW_BEING_AMENDED)
        assert self.module._calculate_severity(entry) == ChangeSeverity.HIGH

    def test_content_updated_is_high(self):
        entry = self._entry(ChangeType.CONTENT_UPDATED)
        assert self.module._calculate_severity(entry) == ChangeSeverity.HIGH

    def test_metadata_updated_is_low(self):
        entry = self._entry(ChangeType.METADATA_UPDATED)
        assert self.module._calculate_severity(entry) == ChangeSeverity.LOW

    def test_new_regulation_without_imminent_enforcement_is_info(self):
        # enforcement_date far in future (>90 days from frozen date)
        entry = self._entry(
            ChangeType.NEW_REGULATION,
            enforcement_date=date(2027, 1, 1),
        )
        assert self.module._calculate_severity(entry) == ChangeSeverity.INFO

    def test_new_regulation_with_imminent_enforcement_is_critical(self):
        # enforcement_date within critical_enforcement_window_days (default 90)
        # frozen at 2026-02-15; set enforcement 30 days out
        entry = self._entry(
            ChangeType.NEW_REGULATION,
            enforcement_date=date(2026, 3, 15),
        )
        assert self.module._calculate_severity(entry) == ChangeSeverity.CRITICAL

    def test_no_change_is_info(self):
        entry = self._entry(ChangeType.NO_CHANGE)
        assert self.module._calculate_severity(entry) == ChangeSeverity.INFO


# ═══════════════════════════════════════════════════════════════════════════
# _generate_changelog (integration)
# ═══════════════════════════════════════════════════════════════════════════

@freeze_time(FROZEN_DATE)
class TestGenerateChangelog:

    def setup_method(self, *_):
        self.module = RegulatoryScreeningModule(store=MagicMock())

    def _run(
        self,
        new_regs: list[ScreeningInputItem],
        prev_regs: list[ScreeningInputItem] | None = None,
        period: str = "2026-02",
        prev_period: str = "2026-01",
    ) -> MonthlyChangelog:
        new_screening = make_monthly_screening(period=period, regulations=new_regs)
        previous_state = (
            make_monthly_screening(period=prev_period, regulations=prev_regs)
            if prev_regs is not None
            else None
        )
        return self.module._generate_changelog(new_screening, previous_state, prev_period)

    def test_first_month_no_previous_state_all_new(self):
        regs = [
            make_screening_item(regulation_id="REG-001"),
            make_screening_item(regulation_id="REG-002"),
        ]
        changelog = self._run(new_regs=regs, prev_regs=None)
        assert len(changelog.new_regulations) == 2
        assert len(changelog.carried_forward) == 0

    def test_regulation_present_in_both_months_no_change_is_carried_forward(self):
        reg = make_screening_item(regulation_id="REG-001")
        changelog = self._run(new_regs=[reg], prev_regs=[reg])
        assert len(changelog.carried_forward) == 1
        assert len(changelog.new_regulations) == 0

    def test_regulation_removed_from_new_screening_appears_in_ended(self):
        old_reg = make_screening_item(regulation_id="REG-OLD")
        new_reg = make_screening_item(regulation_id="REG-NEW")
        changelog = self._run(new_regs=[new_reg], prev_regs=[old_reg])
        ended_ids = {e.regulation_id for e in changelog.ended_regulations}
        assert "REG-OLD" in ended_ids

    def test_status_change_to_law_passed_goes_to_status_changes(self):
        old_reg = make_screening_item(
            regulation_id="REG-001",
            current_status=RegulationStatus.PROPOSED,
        )
        new_reg = make_screening_item(
            regulation_id="REG-001",
            current_status=RegulationStatus.LAW_PASSED,
        )
        changelog = self._run(new_regs=[new_reg], prev_regs=[old_reg])
        assert len(changelog.status_changes) == 1
        assert changelog.status_changes[0].change_type == ChangeType.STATUS_PROMOTED_TO_LAW

    def test_enforcement_date_change_goes_to_timeline_changes(self):
        old_reg = make_screening_item(
            regulation_id="REG-001",
            enforcement_date=date(2026, 6, 1),
        )
        new_reg = make_screening_item(
            regulation_id="REG-001",
            enforcement_date=date(2026, 12, 1),
        )
        changelog = self._run(new_regs=[new_reg], prev_regs=[old_reg])
        assert len(changelog.timeline_changes) == 1

    def test_total_regulations_tracked_matches_new_screening(self):
        regs = [make_screening_item(regulation_id=f"REG-{i:03d}") for i in range(5)]
        changelog = self._run(new_regs=regs, prev_regs=None)
        assert changelog.total_regulations_tracked == 5

    def test_total_changes_detected_excludes_carried_forward(self):
        reg = make_screening_item(regulation_id="REG-001")
        changelog = self._run(new_regs=[reg], prev_regs=[reg])
        # The one unchanged reg is carried forward — not counted as a change
        assert changelog.total_changes_detected == 0

    def test_changelog_period_attributes_set_correctly(self):
        reg = make_screening_item()
        changelog = self._run(new_regs=[reg], period="2026-02", prev_period="2026-01")
        assert changelog.screening_period == "2026-02"
        assert changelog.previous_period == "2026-01"

    def test_critical_actions_populated_for_promoted_regulation(self):
        old_reg = make_screening_item(
            regulation_id="REG-001",
            current_status=RegulationStatus.PROPOSED,
        )
        new_reg = make_screening_item(
            regulation_id="REG-001",
            current_status=RegulationStatus.LAW_PASSED,
        )
        changelog = self._run(new_regs=[new_reg], prev_regs=[old_reg])
        critical_ids = {e.regulation_id for e in changelog.critical_actions}
        assert "REG-001" in critical_ids


# ═══════════════════════════════════════════════════════════════════════════
# _normalize_screening_input
# ═══════════════════════════════════════════════════════════════════════════

class TestNormalizeScreeningInput:

    def test_all_topics_covered_even_when_empty_topic_present(self):
        module = RegulatoryScreeningModule(store=MagicMock())
        # Only GHG regulation — other topics missing
        screening = make_monthly_screening(
            regulations=[make_screening_item(topic=TopicCategory.GHG)]
        )
        normalized = module._normalize_screening_input(screening)
        assert set(normalized.topics_covered) == set(TopicCategory)

    def test_data_quality_flag_emitted_for_missing_topic(self):
        module = RegulatoryScreeningModule(store=MagicMock())
        screening = make_monthly_screening(
            regulations=[make_screening_item(topic=TopicCategory.GHG)]
        )
        normalized = module._normalize_screening_input(screening)
        # Should have flags for every non-GHG topic
        for topic in TopicCategory:
            if topic != TopicCategory.GHG:
                assert f"no_items_for_topic:{topic.value}" in normalized.data_quality_flags

    def test_no_data_quality_flags_when_all_topics_covered(self):
        module = RegulatoryScreeningModule(store=MagicMock())
        regulations = [
            make_screening_item(regulation_id=f"REG-{t.value}", topic=t)
            for t in TopicCategory
        ]
        screening = make_monthly_screening(regulations=regulations)
        normalized = module._normalize_screening_input(screening)
        assert normalized.data_quality_flags == []

    def test_country_filter_removes_non_matching_regulations(self):
        module = RegulatoryScreeningModule(
            store=MagicMock(),
            config={"allowed_countries": ["DE"]},
        )
        reg_de = make_screening_item(regulation_id="REG-DE", applicable_countries=["DE"])
        reg_fr = make_screening_item(
            regulation_id="REG-FR",
            topic=TopicCategory.PACKAGING,
            applicable_countries=["FR"],
        )
        screening = make_monthly_screening(regulations=[reg_de, reg_fr])
        normalized = module._normalize_screening_input(screening)
        ids = {r.regulation_id for r in normalized.regulations}
        assert "REG-DE" in ids
        assert "REG-FR" not in ids

    def test_empty_allowed_countries_config_keeps_all_regulations(self):
        """Explicitly setting allowed_countries=[] disables country filtering."""
        module = RegulatoryScreeningModule(
            store=MagicMock(),
            config={"allowed_countries": []},
        )
        reg_de = make_screening_item(regulation_id="REG-DE", applicable_countries=["DE"])
        reg_fr = make_screening_item(
            regulation_id="REG-FR",
            topic=TopicCategory.PACKAGING,
            applicable_countries=["FR"],
        )
        screening = make_monthly_screening(regulations=[reg_de, reg_fr])
        normalized = module._normalize_screening_input(screening)
        ids = {r.regulation_id for r in normalized.regulations}
        assert "REG-DE" in ids
        assert "REG-FR" in ids


# ═══════════════════════════════════════════════════════════════════════════
# _get_previous_period
# ═══════════════════════════════════════════════════════════════════════════

class TestGetPreviousPeriod:

    def setup_method(self):
        self.module = RegulatoryScreeningModule(store=MagicMock())

    @pytest.mark.parametrize("current,expected", [
        ("2026-02", "2026-01"),
        ("2026-03", "2026-02"),
        ("2026-12", "2026-11"),
        ("2026-01", "2025-12"),   # year rollover edge case
        ("2000-01", "1999-12"),   # century boundary
    ])
    def test_previous_period_calculation(self, current, expected):
        assert self.module._get_previous_period(current) == expected


# ═══════════════════════════════════════════════════════════════════════════
# FileSystemRegulationStore
# ═══════════════════════════════════════════════════════════════════════════

class TestFileSystemRegulationStore:

    def test_get_previous_state_returns_none_when_no_file(self, tmp_path: Path):
        store = FileSystemRegulationStore(tmp_path / "data")
        result = store.get_previous_state("2026-01")
        assert result is None

    def test_save_and_load_round_trip(self, tmp_path: Path):
        store = FileSystemRegulationStore(tmp_path / "data")
        reg = make_screening_item(
            regulation_id="REG-001",
            title="Roundtrip Test",
            effective_date=date(2026, 6, 1),
        )
        screening = make_monthly_screening(period="2026-01", regulations=[reg])
        store.save_state("2026-01", screening)

        loaded = store.get_previous_state("2026-01")
        assert loaded is not None
        assert loaded.screening_period == "2026-01"
        assert len(loaded.regulations) == 1
        assert loaded.regulations[0].regulation_id == "REG-001"
        assert loaded.regulations[0].effective_date == date(2026, 6, 1)

    def test_save_creates_directories_automatically(self, tmp_path: Path):
        deep_path = tmp_path / "a" / "b" / "c"
        store = FileSystemRegulationStore(deep_path)
        screening = make_monthly_screening()
        store.save_state("2026-01", screening)
        assert (deep_path / "states" / "2026-01.json").exists()

    def test_saved_state_is_valid_json(self, tmp_path: Path):
        store = FileSystemRegulationStore(tmp_path / "data")
        store.save_state("2026-01", make_monthly_screening())
        file_path = tmp_path / "data" / "states" / "2026-01.json"
        content = json.loads(file_path.read_text())
        assert "regulations" in content
        assert "screening_period" in content

    def test_save_changelog_creates_file(self, tmp_path: Path):
        store = FileSystemRegulationStore(tmp_path / "data")
        changelog = MonthlyChangelog(
            screening_period="2026-02",
            generated_date=date(2026, 2, 15),
            previous_period="2026-01",
        )
        store.save_changelog(changelog)
        changelog_file = tmp_path / "data" / "changelogs" / "2026-02.json"
        assert changelog_file.exists()
        data = json.loads(changelog_file.read_text())
        assert data["screening_period"] == "2026-02"

    def test_round_trip_preserves_enum_values(self, tmp_path: Path):
        store = FileSystemRegulationStore(tmp_path / "data")
        reg = make_screening_item(
            current_status=RegulationStatus.LAW_PASSED,
            geographic_scope=GeographicScope.REGIONAL,
            topic=TopicCategory.PACKAGING,
        )
        screening = make_monthly_screening(regulations=[reg])
        store.save_state("2026-01", screening)
        loaded = store.get_previous_state("2026-01")
        assert loaded.regulations[0].current_status == RegulationStatus.LAW_PASSED
        assert loaded.regulations[0].geographic_scope == GeographicScope.REGIONAL
        assert loaded.regulations[0].topic == TopicCategory.PACKAGING

    def test_round_trip_with_none_dates(self, tmp_path: Path):
        store = FileSystemRegulationStore(tmp_path / "data")
        reg = make_screening_item(effective_date=None, enforcement_date=None)
        screening = make_monthly_screening(regulations=[reg])
        store.save_state("2026-01", screening)
        loaded = store.get_previous_state("2026-01")
        assert loaded.regulations[0].effective_date is None
        assert loaded.regulations[0].enforcement_date is None


# ═══════════════════════════════════════════════════════════════════════════
# Topic change status generation
# ═══════════════════════════════════════════════════════════════════════════

@freeze_time(FROZEN_DATE)
class TestTopicChangeStatusGeneration:

    def setup_method(self, *_):
        self.module = RegulatoryScreeningModule(store=MagicMock())

    def _make_changelog(
        self,
        new_regulations: list[ChangelogEntry] | None = None,
        status_changes: list[ChangelogEntry] | None = None,
        carried_forward: list[ChangelogEntry] | None = None,
    ) -> MonthlyChangelog:
        changelog = MonthlyChangelog(
            screening_period="2026-02",
            generated_date=date(2026, 2, 15),
            previous_period="2026-01",
        )
        changelog.new_regulations = new_regulations or []
        changelog.status_changes = status_changes or []
        changelog.carried_forward = carried_forward or []
        return changelog

    def _ghg_entry(self, change_type: ChangeType, current_status: RegulationStatus) -> ChangelogEntry:
        return ChangelogEntry(
            regulation_id="REG-001",
            title="GHG Test",
            topic=TopicCategory.GHG,
            change_type=change_type,
            severity=ChangeSeverity.HIGH,
            current_status=current_status,
        )

    def test_all_topics_present_in_output(self):
        changelog = self._make_changelog()
        statuses = self.module._generate_topic_change_statuses(changelog)
        assert set(statuses.keys()) == set(TopicCategory)

    def test_topic_with_no_changes_is_not_changed(self):
        changelog = self._make_changelog()
        statuses = self.module._generate_topic_change_statuses(changelog)
        assert statuses[TopicCategory.GHG].changed_since_last is False

    def test_new_regulation_marks_topic_changed(self):
        entry = self._ghg_entry(ChangeType.NEW_REGULATION, RegulationStatus.PROPOSED)
        changelog = self._make_changelog(new_regulations=[entry])
        statuses = self.module._generate_topic_change_statuses(changelog)
        assert statuses[TopicCategory.GHG].changed_since_last is True

    def test_carried_forward_does_not_mark_topic_changed(self):
        entry = self._ghg_entry(ChangeType.CARRIED_FORWARD, RegulationStatus.PROPOSED)
        changelog = self._make_changelog(carried_forward=[entry])
        statuses = self.module._generate_topic_change_statuses(changelog)
        assert statuses[TopicCategory.GHG].changed_since_last is False

    def test_law_passed_status_sets_level_to_law_passed(self):
        entry = self._ghg_entry(ChangeType.STATUS_PROMOTED_TO_LAW, RegulationStatus.LAW_PASSED)
        changelog = self._make_changelog(status_changes=[entry])
        statuses = self.module._generate_topic_change_statuses(changelog)
        assert statuses[TopicCategory.GHG].level == RegulationStatus.LAW_PASSED

    def test_amendment_in_progress_level_set(self):
        entry = self._ghg_entry(ChangeType.STATUS_ADVANCING, RegulationStatus.AMENDMENT_IN_PROGRESS)
        changelog = self._make_changelog(status_changes=[entry])
        statuses = self.module._generate_topic_change_statuses(changelog)
        assert statuses[TopicCategory.GHG].level == RegulationStatus.AMENDMENT_IN_PROGRESS

    def test_higher_priority_level_wins(self):
        """If both AMENDMENT_IN_PROGRESS and LAW_PASSED exist for same topic, LAW_PASSED wins."""
        entry_lower = self._ghg_entry(
            ChangeType.STATUS_ADVANCING, RegulationStatus.AMENDMENT_IN_PROGRESS
        )
        entry_higher = self._ghg_entry(
            ChangeType.STATUS_PROMOTED_TO_LAW, RegulationStatus.LAW_PASSED
        )
        changelog = self._make_changelog(status_changes=[entry_lower, entry_higher])
        statuses = self.module._generate_topic_change_statuses(changelog)
        assert statuses[TopicCategory.GHG].level == RegulationStatus.LAW_PASSED

    def test_changes_detected_count_is_accurate(self):
        entries = [
            self._ghg_entry(ChangeType.NEW_REGULATION, RegulationStatus.PROPOSED),
            self._ghg_entry(ChangeType.STATUS_ADVANCING, RegulationStatus.AMENDMENT_IN_PROGRESS),
        ]
        changelog = self._make_changelog(new_regulations=[entries[0]], status_changes=[entries[1]])
        statuses = self.module._generate_topic_change_statuses(changelog)
        assert statuses[TopicCategory.GHG].changes_detected == 2

    def test_packaging_topic_unaffected_by_ghg_changes(self):
        entry = self._ghg_entry(ChangeType.NEW_REGULATION, RegulationStatus.PROPOSED)
        changelog = self._make_changelog(new_regulations=[entry])
        statuses = self.module._generate_topic_change_statuses(changelog)
        assert statuses[TopicCategory.PACKAGING].changed_since_last is False


# ═══════════════════════════════════════════════════════════════════════════
# Full run_monthly_screening integration smoke test
# ═══════════════════════════════════════════════════════════════════════════

@freeze_time(FROZEN_DATE)
def test_run_monthly_screening_end_to_end(tmp_path: Path):
    """
    Smoke test: run two consecutive months through the full pipeline
    and verify the changelog captures the status change.
    """
    store = FileSystemRegulationStore(tmp_path / "regulatory_data")
    module = RegulatoryScreeningModule(store=store)

    # Month 1: REG-001 is PROPOSED
    jan_reg = make_screening_item(
        regulation_id="REG-001",
        current_status=RegulationStatus.PROPOSED,
        version_date=date(2026, 1, 15),
    )
    jan_screening = make_monthly_screening(
        period="2026-01",
        regulations=[jan_reg],
        screening_date=date(2026, 1, 31),
    )
    module.run_monthly_screening("2026-01", input_data=jan_screening)

    # Month 2: REG-001 promoted to LAW_PASSED
    feb_reg = make_screening_item(
        regulation_id="REG-001",
        current_status=RegulationStatus.LAW_PASSED,
        version_date=date(2026, 2, 10),
    )
    feb_screening = make_monthly_screening(
        period="2026-02",
        regulations=[feb_reg],
        screening_date=date(2026, 2, 15),
    )
    changelog = module.run_monthly_screening("2026-02", input_data=feb_screening)

    assert len(changelog.status_changes) == 1
    assert changelog.status_changes[0].change_type == ChangeType.STATUS_PROMOTED_TO_LAW
    assert changelog.status_changes[0].severity == ChangeSeverity.CRITICAL

    # Jan state persisted
    jan_state = store.get_previous_state("2026-01")
    assert jan_state is not None
