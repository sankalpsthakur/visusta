"""
Tests for quarterly_consolidator.py

Frozen date: 2026-02-15 to make all date.today() and age-based calculations deterministic.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import List

import pytest
from freezegun import freeze_time

from quarterly_consolidator import (
    CONFIDENCE_MEDIUM_THRESHOLD,
    VALIDATION_MAX_AGE_DAYS,
    VALIDATION_MIN_SOURCES,
    ChangeLogEntry,
    ChangeStatus,
    ChangeValidator,
    ConflictResolver,
    ConsolidatedRegulation,
    ImpactLevel,
    InvestmentType,
    QuarterlyConsolidator,
    QuarterlyOutputFormatter,
    QuarterlySummary,
    RegulationScope,
    SourceReference,
    TimelineMilestone,
)

from tests.conftest import (
    FROZEN_DATE,
    make_changelog_entry,
    make_source,
)


# ═══════════════════════════════════════════════════════════════════════════
# ChangeLogEntry.calculate_confidence_score
# ═══════════════════════════════════════════════════════════════════════════

@freeze_time(FROZEN_DATE)
class TestCalculateConfidenceScore:
    """
    Frozen at 2026-02-15.

    Score formula: weighted average of three components
      sources  (50%): avg_source_reliability * min(num_sources / 2, 1.0)
      status   (30%): VALIDATED=1.0, PENDING=0.6, DRAFT=0.3, SUPERSEDED=0.2, RETRACTED=0.0
      age      (20%): max(0, 1 - age_days / 90)
    """

    def test_perfect_score_two_perfect_sources_validated_zero_age(self):
        entry = make_changelog_entry(
            sources=[
                make_source("S1", reliability_score=1.0),
                make_source("S2", reliability_score=1.0),
            ],
            status=ChangeStatus.VALIDATED,
            change_date=date(2026, 2, 15),  # same as frozen date — 0 days old
        )
        score = entry.calculate_confidence_score()
        # sources: avg=1.0 * (2/2)=1.0 * 0.5 = 0.5
        # status: 1.0 * 0.3 = 0.3
        # age: 1.0 * 0.2 = 0.2 (0 days old)
        assert score == pytest.approx(1.0, abs=0.01)

    def test_no_sources_gives_zero_source_component(self):
        entry = make_changelog_entry(
            sources=[],
            status=ChangeStatus.VALIDATED,
            change_date=date(2026, 2, 15),
        )
        score = entry.calculate_confidence_score()
        # sources: 0.0 * 0.5 = 0
        # status: 1.0 * 0.3 = 0.3
        # age: 1.0 * 0.2 = 0.2
        assert score == pytest.approx(0.5, abs=0.01)

    def test_retracted_status_zeroes_status_component(self):
        entry = make_changelog_entry(
            sources=[
                make_source("S1", reliability_score=1.0),
                make_source("S2", reliability_score=1.0),
            ],
            status=ChangeStatus.RETRACTED,
            change_date=date(2026, 2, 15),
        )
        score = entry.calculate_confidence_score()
        # sources: 1.0 * 0.5 = 0.5
        # status: 0.0 * 0.3 = 0
        # age: 1.0 * 0.2 = 0.2
        assert score == pytest.approx(0.7, abs=0.01)

    def test_age_factor_decreases_with_time(self):
        """Entry from 45 days ago should score lower than fresh entry (same other factors)."""
        fresh = make_changelog_entry(change_date=date(2026, 2, 15))   # 0 days
        old = make_changelog_entry(change_date=date(2026, 1, 1))      # 45 days
        assert fresh.calculate_confidence_score() > old.calculate_confidence_score()

    def test_age_factor_zero_when_older_than_max_age(self):
        """Entries older than 90 days have age_factor clamped to 0."""
        ancient = make_changelog_entry(change_date=date(2025, 11, 1))  # >90 days before 2026-02-15
        score = ancient.calculate_confidence_score()
        # age component = 0; score driven by sources + status only
        # sources: ~0.9 avg * 1.0 * 0.5 = 0.45
        # status: 1.0 * 0.3 = 0.3
        # age: 0 * 0.2 = 0
        assert score == pytest.approx(0.75, abs=0.02)

    def test_single_source_reduces_score_via_count_bonus(self):
        """Only 1 source → count_bonus = 0.5 → source component halved."""
        one_source = make_changelog_entry(
            sources=[make_source("S1", reliability_score=1.0)],
            status=ChangeStatus.VALIDATED,
            change_date=date(2026, 2, 15),
        )
        two_sources = make_changelog_entry(
            sources=[
                make_source("S1", reliability_score=1.0),
                make_source("S2", reliability_score=1.0),
            ],
            status=ChangeStatus.VALIDATED,
            change_date=date(2026, 2, 15),
        )
        assert one_source.calculate_confidence_score() < two_sources.calculate_confidence_score()

    def test_draft_status_gives_lower_status_score_than_validated(self):
        draft = make_changelog_entry(status=ChangeStatus.DRAFT, change_date=date(2026, 2, 15))
        validated = make_changelog_entry(status=ChangeStatus.VALIDATED, change_date=date(2026, 2, 15))
        assert draft.calculate_confidence_score() < validated.calculate_confidence_score()

    def test_score_is_rounded_to_two_decimal_places(self):
        entry = make_changelog_entry(change_date=date(2026, 2, 15))
        score = entry.calculate_confidence_score()
        assert score == round(score, 2)

    def test_score_is_between_zero_and_one(self):
        entry = make_changelog_entry()
        score = entry.calculate_confidence_score()
        assert 0.0 <= score <= 1.0

    def test_three_sources_count_bonus_capped_at_one(self):
        """Three sources: min(3/2, 1.0) = 1.0 — no extra bonus beyond 2."""
        three_src = make_changelog_entry(
            sources=[
                make_source("S1", reliability_score=1.0),
                make_source("S2", reliability_score=1.0),
                make_source("S3", reliability_score=1.0),
            ],
            change_date=date(2026, 2, 15),
            status=ChangeStatus.VALIDATED,
        )
        two_src = make_changelog_entry(
            sources=[
                make_source("S1", reliability_score=1.0),
                make_source("S2", reliability_score=1.0),
            ],
            change_date=date(2026, 2, 15),
            status=ChangeStatus.VALIDATED,
        )
        assert three_src.calculate_confidence_score() == two_src.calculate_confidence_score()


# ═══════════════════════════════════════════════════════════════════════════
# ChangeValidator
# ═══════════════════════════════════════════════════════════════════════════

@freeze_time(FROZEN_DATE)
class TestChangeValidator:

    def setup_method(self, *_):
        self.validator = ChangeValidator()

    def test_valid_entry_passes_all_rules(self):
        entry = make_changelog_entry()  # defaults designed to pass
        is_valid, issues = self.validator.validate(entry)
        assert is_valid, f"Expected valid but got issues: {issues}"
        assert issues == []

    def test_insufficient_sources_fails(self):
        entry = make_changelog_entry(sources=[make_source("S1")])  # only 1 source
        is_valid, issues = self.validator.validate(entry)
        assert not is_valid
        assert any("Insufficient sources" in msg for msg in issues)

    def test_no_sources_fails(self):
        entry = make_changelog_entry(sources=[])
        is_valid, issues = self.validator.validate(entry)
        assert not is_valid
        assert any("Insufficient sources" in msg or "No sources" in msg for msg in issues)

    def test_low_reliability_sources_fail(self):
        entry = make_changelog_entry(
            sources=[
                make_source("S1", reliability_score=0.3),
                make_source("S2", reliability_score=0.3),
            ]
        )
        is_valid, issues = self.validator.validate(entry)
        assert not is_valid
        assert any("reliability" in msg.lower() for msg in issues)

    def test_retracted_entry_fails(self):
        entry = make_changelog_entry(status=ChangeStatus.RETRACTED)
        is_valid, issues = self.validator.validate(entry)
        assert not is_valid
        assert any("retracted" in msg.lower() for msg in issues)

    def test_short_description_fails(self):
        entry = make_changelog_entry(description="Too short.")
        is_valid, issues = self.validator.validate(entry)
        assert not is_valid
        assert any("description" in msg.lower() for msg in issues)

    def test_description_of_exactly_50_chars_passes_length_check(self):
        entry = make_changelog_entry(description="A" * 50)
        is_valid, issues = self.validator.validate(entry)
        # May still fail other rules, but description should not be in issues
        desc_issues = [m for m in issues if "description" in m.lower()]
        assert desc_issues == []

    def test_entry_too_old_fails_date_check(self):
        entry = make_changelog_entry(
            change_date=date(2025, 11, 1),  # > 90 days before 2026-02-15
        )
        is_valid, issues = self.validator.validate(entry)
        assert not is_valid
        assert any("old" in msg.lower() or "days" in msg.lower() for msg in issues)

    def test_entry_exactly_at_age_limit_passes(self):
        # 90 days before 2026-02-15 = 2025-11-17
        boundary_date = date(2025, 11, 17)
        entry = make_changelog_entry(change_date=boundary_date)
        is_valid, issues = self.validator.validate(entry)
        date_issues = [m for m in issues if "old" in m.lower() or "days" in m.lower()]
        assert date_issues == []

    def test_batch_validate_segregates_valid_and_invalid(self):
        valid_entry = make_changelog_entry(entry_id="CHG-V")
        invalid_entry = make_changelog_entry(entry_id="CHG-I", sources=[])
        results = self.validator.batch_validate([valid_entry, invalid_entry])
        valid_ids = {e.id for e in results["valid"]}
        invalid_ids = {r["entry"].id for r in results["invalid"]}
        assert "CHG-V" in valid_ids
        assert "CHG-I" in invalid_ids

    def test_batch_validate_counts_by_status(self):
        entries = [
            make_changelog_entry(entry_id="E1", status=ChangeStatus.VALIDATED),
            make_changelog_entry(entry_id="E2", status=ChangeStatus.VALIDATED),
            make_changelog_entry(entry_id="E3", status=ChangeStatus.DRAFT, sources=[]),
        ]
        results = self.validator.batch_validate(entries)
        assert results["by_status"]["VALIDATED"] == 2
        assert results["by_status"]["DRAFT"] == 1

    def test_batch_validate_counts_by_regulation(self):
        entries = [
            make_changelog_entry(entry_id="E1", regulation_code="PPWR"),
            make_changelog_entry(entry_id="E2", regulation_code="PPWR"),
            make_changelog_entry(entry_id="E3", regulation_code="EUDR"),
        ]
        results = self.validator.batch_validate(entries)
        assert results["by_regulation"]["PPWR"] == 2
        assert results["by_regulation"]["EUDR"] == 1

    def test_custom_min_sources_threshold(self):
        validator = ChangeValidator(min_sources=3)
        entry = make_changelog_entry(
            sources=[make_source("S1"), make_source("S2")]
        )
        is_valid, issues = validator.validate(entry)
        assert not is_valid
        assert any("Insufficient sources" in msg for msg in issues)


# ═══════════════════════════════════════════════════════════════════════════
# ConflictResolver
# ═══════════════════════════════════════════════════════════════════════════

@freeze_time(FROZEN_DATE)
class TestConflictResolver:

    def setup_method(self, *_):
        self.resolver = ConflictResolver()

    def test_resolve_impact_returns_maximum(self):
        entries = [
            make_changelog_entry(entry_id="E1", impact_level=ImpactLevel.LOW),
            make_changelog_entry(entry_id="E2", impact_level=ImpactLevel.CRITICAL),
            make_changelog_entry(entry_id="E3", impact_level=ImpactLevel.MEDIUM),
        ]
        result = self.resolver.resolve(entries, "impact")
        assert result == ImpactLevel.CRITICAL

    def test_resolve_impact_all_same(self):
        entries = [
            make_changelog_entry(entry_id="E1", impact_level=ImpactLevel.HIGH),
            make_changelog_entry(entry_id="E2", impact_level=ImpactLevel.HIGH),
        ]
        result = self.resolver.resolve(entries, "impact")
        assert result == ImpactLevel.HIGH

    def test_resolve_status_returns_most_recent_validated(self):
        older = make_changelog_entry(
            entry_id="E1",
            status=ChangeStatus.VALIDATED,
        )
        older.updated_at = datetime(2026, 1, 10)
        newer = make_changelog_entry(
            entry_id="E2",
            status=ChangeStatus.VALIDATED,
        )
        newer.updated_at = datetime(2026, 2, 10)
        result = self.resolver.resolve([older, newer], "status")
        assert result == "VALIDATED"

    def test_resolve_deadline_prefers_confirmed_milestone(self):
        entry_confirmed = make_changelog_entry(
            entry_id="E1",
            milestones=[
                TimelineMilestone(
                    date=date(2026, 8, 1),
                    description="Confirmed deadline",
                    milestone_type="deadline",
                    confirmed=True,
                )
            ],
        )
        entry_unconfirmed = make_changelog_entry(
            entry_id="E2",
            milestones=[
                TimelineMilestone(
                    date=date(2026, 6, 1),
                    description="Unconfirmed deadline",
                    milestone_type="deadline",
                    confirmed=False,
                )
            ],
        )
        result = self.resolver.resolve([entry_confirmed, entry_unconfirmed], "deadline")
        # Confirmed milestone should win regardless of which date is earlier
        assert result == date(2026, 8, 1)

    def test_resolve_deadline_returns_none_when_no_milestones(self):
        entries = [make_changelog_entry(milestones=[])]
        result = self.resolver.resolve(entries, "deadline")
        assert result is None

    def test_resolve_description_uses_longest_validated(self):
        short = make_changelog_entry(entry_id="E1", description="Short description that meets fifty char minimum ok", status=ChangeStatus.VALIDATED)
        long = make_changelog_entry(
            entry_id="E2",
            description=(
                "This is a much longer validated description that provides more detail. "
                "It contains technical specifications and regulatory citations that are "
                "critical for compliance teams to understand the full scope."
            ),
            status=ChangeStatus.VALIDATED,
        )
        result = self.resolver.resolve([short, long], "description")
        assert result == long.description

    def test_resolve_unknown_conflict_type_falls_back_to_most_recent(self):
        older = make_changelog_entry(entry_id="E1", status=ChangeStatus.VALIDATED)
        older.updated_at = datetime(2026, 1, 1)
        newer = make_changelog_entry(entry_id="E2", status=ChangeStatus.VALIDATED)
        newer.updated_at = datetime(2026, 2, 10)
        result = self.resolver.resolve([older, newer], "unknown_conflict_type")
        # Falls back to _most_recent_validated; should return the newer entry
        assert result.id == "E2"


# ═══════════════════════════════════════════════════════════════════════════
# QuarterlyConsolidator.consolidate
# ═══════════════════════════════════════════════════════════════════════════

@freeze_time(FROZEN_DATE)
class TestQuarterlyConsolidatorConsolidate:

    def setup_method(self, *_):
        self.consolidator = QuarterlyConsolidator(quarter="Q1", year=2026)

    def test_empty_input_returns_empty_summary(self):
        summary = self.consolidator.consolidate([])
        assert summary.regulations == []
        assert summary.stats["total_entries_processed"] == 0

    def test_valid_entries_grouped_by_regulation(self):
        ppwr_jan = make_changelog_entry(
            entry_id="E1",
            regulation_code="PPWR",
            reported_month=date(2026, 1, 1),
        )
        ppwr_feb = make_changelog_entry(
            entry_id="E2",
            regulation_code="PPWR",
            reported_month=date(2026, 2, 1),
        )
        eudr = make_changelog_entry(
            entry_id="E3",
            regulation_code="EUDR",
            regulation_name="EU Deforestation Regulation",
            reported_month=date(2026, 1, 1),
        )
        summary = self.consolidator.consolidate([ppwr_jan, ppwr_feb, eudr])
        reg_codes = {r.regulation_code for r in summary.regulations}
        assert "PPWR" in reg_codes
        assert "EUDR" in reg_codes
        assert len(summary.regulations) == 2

    def test_invalid_entries_excluded_from_consolidation(self):
        """Entries failing validation should not contribute to consolidated output."""
        invalid = make_changelog_entry(
            entry_id="E-INVALID",
            regulation_code="INVALID",
            sources=[],  # will fail source count check
        )
        valid = make_changelog_entry(entry_id="E-VALID", regulation_code="PPWR")
        summary = self.consolidator.consolidate([invalid, valid])
        reg_codes = {r.regulation_code for r in summary.regulations}
        assert "PPWR" in reg_codes
        assert "INVALID" not in reg_codes

    def test_stats_track_valid_and_invalid_counts(self):
        valid = make_changelog_entry(entry_id="E-V")
        invalid = make_changelog_entry(entry_id="E-I", sources=[])
        summary = self.consolidator.consolidate([valid, invalid])
        assert summary.stats["total_entries_processed"] == 2
        assert summary.stats["valid_entries"] == 1
        assert summary.stats["invalid_entries"] == 1

    def test_quarter_and_reporting_period_set_correctly(self):
        summary = self.consolidator.consolidate([])
        assert summary.quarter == "Q1 2026"
        assert "January" in summary.reporting_period
        assert "March" in summary.reporting_period

    def test_q2_quarter_months_correct(self):
        consolidator = QuarterlyConsolidator(quarter="Q2", year=2026)
        summary = consolidator.consolidate([])
        assert "April" in summary.reporting_period
        assert "June" in summary.reporting_period

    def test_month_coverage_reflects_which_months_contributed(self):
        jan_entry = make_changelog_entry(
            entry_id="E1",
            regulation_code="PPWR",
            reported_month=date(2026, 1, 1),
        )
        feb_entry = make_changelog_entry(
            entry_id="E2",
            regulation_code="PPWR",
            reported_month=date(2026, 2, 1),
        )
        summary = self.consolidator.consolidate([jan_entry, feb_entry])
        ppwr = next(r for r in summary.regulations if r.regulation_code == "PPWR")
        assert "January" in ppwr.month_coverage
        assert "February" in ppwr.month_coverage

    def test_impact_level_escalated_to_maximum_across_months(self):
        low_jan = make_changelog_entry(
            entry_id="E1",
            regulation_code="PPWR",
            impact_level=ImpactLevel.LOW,
            reported_month=date(2026, 1, 1),
        )
        critical_feb = make_changelog_entry(
            entry_id="E2",
            regulation_code="PPWR",
            impact_level=ImpactLevel.CRITICAL,
            reported_month=date(2026, 2, 1),
        )
        summary = self.consolidator.consolidate([low_jan, critical_feb])
        ppwr = next(r for r in summary.regulations if r.regulation_code == "PPWR")
        assert ppwr.impact_level == ImpactLevel.CRITICAL

    def test_by_impact_stats_populated(self):
        critical = make_changelog_entry(
            entry_id="E1",
            regulation_code="REG-A",
            impact_level=ImpactLevel.CRITICAL,
        )
        high = make_changelog_entry(
            entry_id="E2",
            regulation_code="REG-B",
            regulation_name="Reg B",
            impact_level=ImpactLevel.HIGH,
        )
        summary = self.consolidator.consolidate([critical, high])
        by_impact = summary.stats["by_impact"]
        assert by_impact.get("CRITICAL", 0) >= 1
        assert by_impact.get("HIGH", 0) >= 1

    def test_themes_generated_for_multiple_critical_regulations(self):
        entries = [
            make_changelog_entry(
                entry_id=f"E{i}",
                regulation_code=f"REG-{i}",
                regulation_name=f"Regulation {i}",
                impact_level=ImpactLevel.CRITICAL,
            )
            for i in range(3)
        ]
        summary = self.consolidator.consolidate(entries)
        theme_names = [t["theme"] for t in summary.themes]
        assert any("convergence" in name.lower() or "critical" in name.lower() for name in theme_names)

    def test_single_regulation_single_month_no_progression_narrative(self):
        """Single entry: narrative should reference the regulation name."""
        entry = make_changelog_entry(
            regulation_code="PPWR",
            regulation_name="EU Packaging and Packaging Waste Regulation",
            reported_month=date(2026, 1, 1),
        )
        summary = self.consolidator.consolidate([entry])
        ppwr = summary.regulations[0]
        assert "EU Packaging" in ppwr.executive_summary

    def test_source_entry_ids_tracked(self):
        entry = make_changelog_entry(entry_id="CHG-001", regulation_code="PPWR")
        summary = self.consolidator.consolidate([entry])
        ppwr = summary.regulations[0]
        assert "CHG-001" in ppwr.source_entries


# ═══════════════════════════════════════════════════════════════════════════
# QuarterlyOutputFormatter
# ═══════════════════════════════════════════════════════════════════════════

@freeze_time(FROZEN_DATE)
class TestQuarterlyOutputFormatter:

    def _make_summary(self) -> QuarterlySummary:
        consolidator = QuarterlyConsolidator(quarter="Q1", year=2026)
        entries = [
            make_changelog_entry(
                entry_id="E1",
                regulation_code="PPWR",
                regulation_name="EU Packaging Regulation",
                impact_level=ImpactLevel.HIGH,
                milestones=[
                    TimelineMilestone(
                        date=date(2026, 8, 12),
                        description="General application",
                        milestone_type="deadline",
                        confirmed=True,
                    )
                ],
            ),
            make_changelog_entry(
                entry_id="E2",
                regulation_code="EUDR",
                regulation_name="EU Deforestation Regulation",
                impact_level=ImpactLevel.CRITICAL,
            ),
        ]
        return consolidator.consolidate(entries)

    def test_to_pdf_input_returns_dict_with_expected_keys(self):
        summary = self._make_summary()
        pdf_data = QuarterlyOutputFormatter.to_pdf_input(summary)
        assert isinstance(pdf_data, dict)
        for key in ("quarter", "reporting_period", "executive_summary", "regulation_sections"):
            assert key in pdf_data, f"Missing key: {key}"

    def test_to_pdf_input_regulation_sections_match_count(self):
        summary = self._make_summary()
        pdf_data = QuarterlyOutputFormatter.to_pdf_input(summary)
        assert len(pdf_data["regulation_sections"]) == len(summary.regulations)

    def test_to_json_produces_valid_json_string(self):
        summary = self._make_summary()
        json_str = QuarterlyOutputFormatter.to_json(summary)
        data = json.loads(json_str)  # must not raise
        assert "quarter" in data
        assert "regulations" in data

    def test_to_json_regulations_have_required_fields(self):
        summary = self._make_summary()
        json_str = QuarterlyOutputFormatter.to_json(summary)
        data = json.loads(json_str)
        for reg in data["regulations"]:
            for field in ("code", "name", "scope", "impact", "status"):
                assert field in reg, f"Missing field '{field}' in regulation JSON"

    def test_to_markdown_contains_quarter_header(self):
        summary = self._make_summary()
        md = QuarterlyOutputFormatter.to_markdown(summary)
        assert "Q1 2026" in md

    def test_to_markdown_contains_regulation_sections(self):
        summary = self._make_summary()
        md = QuarterlyOutputFormatter.to_markdown(summary)
        assert "PPWR" in md or "EU Packaging" in md

    def test_to_pdf_input_priority_matrix_sorted_by_impact(self):
        """CRITICAL regs should appear before HIGH regs in priority matrix."""
        summary = self._make_summary()
        pdf_data = QuarterlyOutputFormatter.to_pdf_input(summary)
        matrix = pdf_data.get("priority_matrix", [])
        if len(matrix) >= 2:
            # First row should be CRITICAL or same/higher than second
            impact_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "NONE": 4}
            first_impact = matrix[0][1]
            second_impact = matrix[1][1]
            assert impact_order.get(first_impact, 99) <= impact_order.get(second_impact, 99)

    def test_executive_summary_mentions_regulation_count(self):
        summary = self._make_summary()
        pdf_data = QuarterlyOutputFormatter.to_pdf_input(summary)
        exec_summary = pdf_data["executive_summary"]
        assert str(len(summary.regulations)) in exec_summary


# ═══════════════════════════════════════════════════════════════════════════
# Integration: Sample data from sample_monthly_data.json
# ═══════════════════════════════════════════════════════════════════════════

@freeze_time(FROZEN_DATE)
class TestSampleDataIntegration:
    """
    End-to-end tests using realistic data shaped after sample_monthly_data.json.

    These entries are VALIDATED, have 2+ reliable sources, fresh change_dates,
    and descriptions >= 50 chars — designed to pass ChangeValidator.
    """

    def _ppwr_entry(self) -> ChangeLogEntry:
        return make_changelog_entry(
            entry_id="CHG-2026-015",
            regulation_code="PPWR",
            regulation_name="EU Packaging and Packaging Waste Regulation",
            reported_month=date(2026, 2, 1),
            change_date=date(2026, 2, 10),
            title="ZSVR 2025 Minimum Standard Published",
            description=(
                "The German Central Agency Packaging Register (ZSVR) has published the 2025 Minimum "
                "Standard for assessing the recyclability of packaging. This standard acts as a bridge "
                "to PPWR compliance, providing specific technical criteria."
            ),
            scope=RegulationScope.GERMANY,
            impact_level=ImpactLevel.HIGH,
            affected_areas=["Packaging", "R&D", "Compliance"],
            investment_type=InvestmentType.AUDIT,
            sources=[
                make_source("SRC-024", reliability_score=0.95),
                make_source("SRC-025", reliability_score=0.8),
            ],
            milestones=[
                TimelineMilestone(
                    date=date(2026, 8, 12),
                    description="PPWR General Application Date",
                    milestone_type="deadline",
                    confirmed=True,
                )
            ],
            action_items=[
                "Compare current packaging portfolio against ZSVR 2025 criteria",
                "Identify packaging formats at risk of Grade D or E classification",
            ],
        )

    def _verpackdg_entry(self) -> ChangeLogEntry:
        return make_changelog_entry(
            entry_id="CHG-2026-017",
            regulation_code="VerpackDG",
            regulation_name="German Packaging Law Implementation Act",
            reported_month=date(2026, 2, 1),
            change_date=date(2026, 2, 5),
            description=(
                "The draft Verpackungs-Durchführungsgesetz (VerpackDG) continues to advance through "
                "the legislative process. The key provision mandating Extended Producer Responsibility "
                "(EPR) for B2B packaging remains intact with a new levy of approximately €5 per tonne."
            ),
            scope=RegulationScope.GERMANY,
            impact_level=ImpactLevel.CRITICAL,
            sources=[
                make_source("SRC-011", reliability_score=0.9),
                make_source("SRC-013", reliability_score=0.85),
                make_source("SRC-014", reliability_score=0.85),
            ],
        )

    def test_realistic_entries_pass_validation(self):
        validator = ChangeValidator()
        for entry in [self._ppwr_entry(), self._verpackdg_entry()]:
            is_valid, issues = validator.validate(entry)
            assert is_valid, f"Entry {entry.id} failed: {issues}"

    def test_consolidation_produces_two_regulations(self):
        consolidator = QuarterlyConsolidator(quarter="Q1", year=2026)
        summary = consolidator.consolidate([self._ppwr_entry(), self._verpackdg_entry()])
        assert len(summary.regulations) == 2

    def test_ppwr_deadline_resolved_from_milestone(self):
        consolidator = QuarterlyConsolidator(quarter="Q1", year=2026)
        summary = consolidator.consolidate([self._ppwr_entry()])
        ppwr = summary.regulations[0]
        assert ppwr.primary_deadline == date(2026, 8, 12)

    def test_verpackdg_critical_impact_preserved(self):
        consolidator = QuarterlyConsolidator(quarter="Q1", year=2026)
        summary = consolidator.consolidate([self._ppwr_entry(), self._verpackdg_entry()])
        verpackdg = next(r for r in summary.regulations if r.regulation_code == "VerpackDG")
        assert verpackdg.impact_level == ImpactLevel.CRITICAL

    def test_json_export_round_trips_correctly(self):
        consolidator = QuarterlyConsolidator(quarter="Q1", year=2026)
        summary = consolidator.consolidate([self._ppwr_entry(), self._verpackdg_entry()])
        json_str = QuarterlyOutputFormatter.to_json(summary)
        data = json.loads(json_str)
        reg_codes = {r["code"] for r in data["regulations"]}
        assert "PPWR" in reg_codes
        assert "VerpackDG" in reg_codes
