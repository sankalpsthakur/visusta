"""
Shared fixtures for Visusta test suite.

Frozen date: 2026-02-15 — chosen because:
  - Sample data uses Feb 2026 period
  - regulatory_data/states/2026-02.json is the current state
  - All age-based scores are deterministic at this anchor
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest
from freezegun import freeze_time

# ── Module imports ──────────────────────────────────────────────────────────
from regulatory_screening import (
    ChangeDetail,
    ChangelogEntry,
    ChangeSeverity,
    ChangeType,
    GeographicScope,
    MonthlyScreeningInput,
    RegulationStatus,
    ScreeningInputItem,
    TopicCategory,
)
from quarterly_consolidator import (
    ChangeLogEntry,
    ChangeStatus,
    ImpactLevel,
    InvestmentType,
    RegulationScope,
    SourceReference,
    TimelineMilestone,
)


# ── Date anchor ─────────────────────────────────────────────────────────────

FROZEN_DATE = "2026-02-15"


# ── regulatory_screening fixtures ───────────────────────────────────────────

def make_screening_item(
    regulation_id: str = "REG-001",
    title: str = "Test Regulation Alpha",
    topic: TopicCategory = TopicCategory.GHG,
    description: str = "Detailed description of the regulation for testing purposes.",
    requirements_summary: str = "Companies must report Scope 1 and 2 emissions annually.",
    current_status: RegulationStatus = RegulationStatus.PROPOSED,
    effective_date: date | None = None,
    enforcement_date: date | None = None,
    review_deadline: date | None = None,
    geographic_scope: GeographicScope = GeographicScope.NATIONAL,
    applicable_countries: list[str] | None = None,
    version_date: date | None = None,
    tags: list[str] | None = None,
    confidence_score: float = 1.0,
) -> ScreeningInputItem:
    """Factory for ScreeningInputItem with sensible defaults."""
    return ScreeningInputItem(
        regulation_id=regulation_id,
        title=title,
        topic=topic,
        description=description,
        requirements_summary=requirements_summary,
        current_status=current_status,
        effective_date=effective_date,
        enforcement_date=enforcement_date,
        review_deadline=review_deadline,
        geographic_scope=geographic_scope,
        applicable_countries=applicable_countries if applicable_countries is not None else ["DE"],
        version_date=version_date or date(2026, 1, 1),
        tags=tags or [],
        confidence_score=confidence_score,
    )


def make_monthly_screening(
    period: str = "2026-01",
    screening_date: date | None = None,
    regulations: list[ScreeningInputItem] | None = None,
    topics_covered: list[TopicCategory] | None = None,
) -> MonthlyScreeningInput:
    """Factory for MonthlyScreeningInput."""
    return MonthlyScreeningInput(
        screening_period=period,
        screening_date=screening_date or date(2026, 1, 31),
        screened_by="test-agent",
        regulations=regulations or [make_screening_item()],
        topics_covered=topics_covered or list(TopicCategory),
    )


@pytest.fixture
def sample_screening_item() -> ScreeningInputItem:
    return make_screening_item()


@pytest.fixture
def basic_monthly_screening() -> MonthlyScreeningInput:
    return make_monthly_screening()


# ── quarterly_consolidator fixtures ─────────────────────────────────────────

def make_source(
    src_id: str = "SRC-001",
    title: str = "Official Regulation Gazette",
    reliability_score: float = 0.9,
    publish_date: date | None = None,
) -> SourceReference:
    """Factory for SourceReference."""
    return SourceReference(
        id=src_id,
        title=title,
        url=f"https://example.com/{src_id}",
        publisher="Official Publisher",
        publish_date=publish_date or date(2026, 1, 10),
        access_date=date(2026, 2, 1),
        reliability_score=reliability_score,
    )


def make_changelog_entry(
    entry_id: str = "CHG-001",
    regulation_code: str = "PPWR",
    regulation_name: str = "EU Packaging and Packaging Waste Regulation",
    reported_month: date | None = None,
    change_date: date | None = None,
    title: str = "New packaging recyclability standard published",
    description: str = (
        "The European Commission published updated recyclability criteria for packaging "
        "materials. This affects all packaging placed on the EU market from 2026 onwards "
        "and requires manufacturers to conduct detailed lifecycle assessments."
    ),
    change_type: str = "amendment",
    scope: RegulationScope = RegulationScope.EU,
    impact_level: ImpactLevel = ImpactLevel.HIGH,
    affected_areas: list[str] | None = None,
    investment_type: InvestmentType = InvestmentType.AUDIT,
    status: ChangeStatus = ChangeStatus.VALIDATED,
    sources: list[SourceReference] | None = None,
    milestones: list[TimelineMilestone] | None = None,
    action_items: list[str] | None = None,
    executive_summary: str | None = None,
) -> ChangeLogEntry:
    """
    Factory for ChangeLogEntry.

    Defaults are designed to PASS ChangeValidator out of the box:
      - 2 sources, reliability >= 0.9
      - VALIDATED status
      - change_date within 90 days of 2026-02-15 (frozen date)
      - description >= 50 chars
    """
    if sources is None:
        sources = [
            make_source("SRC-001", reliability_score=0.95),
            make_source("SRC-002", reliability_score=0.85),
        ]
    return ChangeLogEntry(
        id=entry_id,
        regulation_code=regulation_code,
        regulation_name=regulation_name,
        reported_month=reported_month or date(2026, 2, 1),
        change_date=change_date or date(2026, 2, 10),
        title=title,
        description=description,
        change_type=change_type,
        scope=scope,
        impact_level=impact_level,
        affected_areas=affected_areas or ["Packaging", "Compliance"],
        investment_type=investment_type,
        status=status,
        sources=sources,
        milestones=milestones or [],
        action_items=action_items or ["Conduct packaging audit", "Update supplier contracts"],
        executive_summary=executive_summary,
        created_at=datetime(2026, 2, 10, 9, 0),
        updated_at=datetime(2026, 2, 10, 9, 0),
    )


@pytest.fixture
def sample_changelog_entry() -> ChangeLogEntry:
    return make_changelog_entry()


@pytest.fixture
def two_source_validated_entry() -> ChangeLogEntry:
    """Entry that clearly passes all validation rules (under frozen date 2026-02-15)."""
    return make_changelog_entry(
        change_date=date(2026, 2, 10),  # 5 days ago, well within 90-day window
        status=ChangeStatus.VALIDATED,
    )
