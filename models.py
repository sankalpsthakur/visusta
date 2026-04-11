#!/usr/bin/env python3
"""
VISUSTA — Shared Data Models and Adapter Layer

This module provides the bridge between the monthly regulatory screening output
(regulatory_screening.py) and the quarterly consolidation input (quarterly_consolidator.py).

It does NOT redefine existing enums or classes — it imports from both modules
and provides the mapping logic that connects them.

Import direction:
    models.py           <- imports from regulatory_screening + quarterly_consolidator
    pipeline.py         <- imports from models + both source modules
    regulatory_screening.py  — unchanged
    quarterly_consolidator.py — unchanged
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional, Dict, Any, Tuple

# ── Monthly (screening) types ─────────────────────────────────────────────────
from regulatory_screening import (
    ChangelogEntry as MonthlyChangelogEntry,
    MonthlyChangelog,
    ChangeType,
    ChangeSeverity,
    GeographicScope,
    TopicCategory,
    RegulationStatus,
    ChangeDetail,
)

# ── Quarterly (consolidation) types ──────────────────────────────────────────
from quarterly_consolidator import (
    ChangeLogEntry as QuarterlyChangeLogEntry,
    ImpactLevel,
    RegulationScope,
    ChangeStatus,
    InvestmentType,
    SourceReference,
    TimelineMilestone,
    QuarterlySummary,
    QuarterlyConsolidator,
    load_entries_from_json,
)


# ════════════════════════════════════════════════════════════════════════════
# MAPPING TABLES
# ════════════════════════════════════════════════════════════════════════════

# ChangeSeverity (lowercase values) → ImpactLevel (uppercase values)
SEVERITY_TO_IMPACT: Dict[ChangeSeverity, ImpactLevel] = {
    ChangeSeverity.CRITICAL: ImpactLevel.CRITICAL,
    ChangeSeverity.HIGH:     ImpactLevel.HIGH,
    ChangeSeverity.MEDIUM:   ImpactLevel.MEDIUM,
    ChangeSeverity.LOW:      ImpactLevel.LOW,
    ChangeSeverity.INFO:     ImpactLevel.NONE,
}

# GeographicScope → RegulationScope
# The codebase is Germany-centric (Hamburg / Rietberg facilities).
# NATIONAL defaults to DE; REGIONAL defaults to EU.
GEO_SCOPE_TO_REG_SCOPE: Dict[GeographicScope, RegulationScope] = {
    GeographicScope.GLOBAL:   RegulationScope.INTERNATIONAL,
    GeographicScope.REGIONAL: RegulationScope.EU,
    GeographicScope.NATIONAL: RegulationScope.GERMANY,
    GeographicScope.STATE:    RegulationScope.STATE,
    GeographicScope.LOCAL:    RegulationScope.LOCAL,
}

# ChangeType → free-form change_type string used by quarterly model
CHANGE_TYPE_TO_STRING: Dict[ChangeType, str] = {
    ChangeType.NEW_REGULATION:        "new_regulation",
    ChangeType.STATUS_PROMOTED_TO_LAW:"status_change",
    ChangeType.STATUS_ADVANCING:      "status_change",
    ChangeType.LAW_BEING_AMENDED:     "amendment",
    ChangeType.TIMELINE_UPDATED:      "deadline_change",
    ChangeType.CONTENT_UPDATED:       "content_update",
    ChangeType.METADATA_UPDATED:      "metadata_update",
    ChangeType.LAW_EXPIRED:           "expiry",
    ChangeType.REGULATION_ENDED:      "expiry",
    ChangeType.REGULATION_REMOVED:    "removal",
    ChangeType.NO_CHANGE:             "no_change",
    ChangeType.CARRIED_FORWARD:       "carried_forward",
}

# TopicCategory → affected area display strings
TOPIC_TO_AFFECTED_AREAS: Dict[TopicCategory, List[str]] = {
    TopicCategory.GHG:               ["GHG Reporting", "Climate"],
    TopicCategory.PACKAGING:         ["Packaging", "Compliance"],
    TopicCategory.WATER:             ["Water Management", "Operations"],
    TopicCategory.WASTE:             ["Waste Management", "Facilities"],
    TopicCategory.SOCIAL_HUMAN_RIGHTS: ["Supply Chain", "Compliance", "Legal"],
}


# ════════════════════════════════════════════════════════════════════════════
# ADAPTER
# ════════════════════════════════════════════════════════════════════════════

class MonthlyToQuarterlyAdapter:
    """
    Converts a monthly ChangelogEntry (regulatory_screening output) into
    a quarterly ChangeLogEntry (quarterly_consolidator input).

    This is a bridge layer — it does not modify either source model.
    Both classes are preserved unchanged; the adapter creates new quarterly
    objects from monthly data with sensible defaults where fields are absent.

    Usage::

        adapter = MonthlyToQuarterlyAdapter(period="2026-01")
        quarterly_entries = adapter.adapt_changelog(monthly_changelog)
        # pass quarterly_entries to QuarterlyConsolidator.consolidate()
    """

    def __init__(self, period: str):
        """
        Args:
            period: The screening period string, e.g. "2026-01".
                    Used to derive reported_month and to generate unique IDs.
        """
        self.period = period
        # Parse the reporting month from the period string (YYYY-MM)
        try:
            year, month = period.split("-")
            self.reported_month = date(int(year), int(month), 1)
        except (ValueError, AttributeError):
            self.reported_month = date.today().replace(day=1)

    # ── Public API ────────────────────────────────────────────────────────────

    def adapt_entry(self, entry: MonthlyChangelogEntry) -> QuarterlyChangeLogEntry:
        """
        Convert a single monthly ChangelogEntry to a quarterly ChangeLogEntry.

        Mapping rules:
        - regulation_id        → regulation_code  (1:1)
        - title                → title, regulation_name (regulation_name = title fallback)
        - severity             → impact_level  (via SEVERITY_TO_IMPACT)
        - change_type          → change_type string (via CHANGE_TYPE_TO_STRING)
        - geographic_scope     → scope  (via GEO_SCOPE_TO_REG_SCOPE)
        - entry_date           → change_date, reported_month
        - effective_date       → milestone with type "effective"
        - enforcement_date     → milestone with type "deadline"
        - action_required      → action_items
        - summary              → executive_summary
        - changes (ChangeDetail) → not mapped (different semantics; quarterly
          uses narrative descriptions, not field-diff objects)
        - sources              → empty list (not present in monthly model)
        - investment_type      → InvestmentType.NONE (not present in monthly model)
        - affected_areas       → derived from topic via TOPIC_TO_AFFECTED_AREAS
        """
        impact_level = SEVERITY_TO_IMPACT.get(entry.severity, ImpactLevel.MEDIUM)
        scope = GEO_SCOPE_TO_REG_SCOPE.get(entry.geographic_scope, RegulationScope.GERMANY)
        change_type_str = CHANGE_TYPE_TO_STRING.get(entry.change_type, "content_update")
        affected_areas = TOPIC_TO_AFFECTED_AREAS.get(entry.topic, ["Compliance"])

        # Build milestones from effective/enforcement dates
        milestones: List[TimelineMilestone] = []
        if entry.effective_date:
            milestones.append(TimelineMilestone(
                date=entry.effective_date,
                description=f"Effective date for {entry.regulation_id}",
                milestone_type="effective",
                confirmed=True,
            ))
        if entry.enforcement_date:
            milestones.append(TimelineMilestone(
                date=entry.enforcement_date,
                description=f"Enforcement deadline for {entry.regulation_id}",
                milestone_type="deadline",
                confirmed=True,
            ))

        # Map action_required to action_items list
        action_items: List[str] = []
        if entry.action_required:
            action_items.append(entry.action_required)

        # Determine change_date: prefer entry_date, fallback to reported_month
        change_date = entry.entry_date if entry.entry_date else self.reported_month

        # Generate unique quarterly entry ID
        entry_id = f"CHG-{self.period}-{entry.regulation_id}"

        # Map RegulationStatus to ChangeStatus
        status = self._map_regulation_status(entry.current_status)

        return QuarterlyChangeLogEntry(
            id=entry_id,
            regulation_code=entry.regulation_id,
            regulation_name=entry.title,
            reported_month=self.reported_month,
            change_date=change_date,
            title=entry.title,
            description=entry.summary or f"{entry.title} — {entry.change_type.value}",
            change_type=change_type_str,
            scope=scope,
            impact_level=impact_level,
            affected_areas=affected_areas,
            investment_type=InvestmentType.NONE,
            status=status,
            sources=[],
            related_entries=[],
            milestones=milestones,
            created_at=datetime.combine(change_date, datetime.min.time()),
            updated_at=datetime.combine(change_date, datetime.min.time()),
            executive_summary=entry.summary or None,
            action_items=action_items,
        )

    def adapt_changelog(
        self,
        changelog: MonthlyChangelog,
        exclude_carried_forward: bool = True,
    ) -> List[QuarterlyChangeLogEntry]:
        """
        Convert a full MonthlyChangelog into a list of quarterly ChangeLogEntry objects.

        Flattens all categories using MonthlyChangelog.all_entries(), then adapts each.

        Args:
            changelog: The monthly screening output.
            exclude_carried_forward: If True (default), skip entries where
                change_type is CARRIED_FORWARD or NO_CHANGE, since they carry
                no new information for quarterly consolidation.

        Returns:
            List of QuarterlyChangeLogEntry objects ready for QuarterlyConsolidator.
        """
        skip_types = set()
        if exclude_carried_forward:
            skip_types = {ChangeType.CARRIED_FORWARD, ChangeType.NO_CHANGE}

        quarterly_entries: List[QuarterlyChangeLogEntry] = []
        for entry in changelog.all_entries():
            if entry.change_type in skip_types:
                continue
            quarterly_entries.append(self.adapt_entry(entry))

        return quarterly_entries

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _map_regulation_status(status: RegulationStatus) -> ChangeStatus:
        """
        Map monthly RegulationStatus to quarterly ChangeStatus.

        Monthly status describes the state of the regulation itself.
        Quarterly status describes the confidence/validation state of the entry.
        The mapping is intentionally conservative — a passed law means the
        entry is validated; anything under discussion is pending.
        """
        mapping: Dict[RegulationStatus, ChangeStatus] = {
            RegulationStatus.LAW_PASSED:              ChangeStatus.VALIDATED,
            RegulationStatus.AMENDMENT_IN_PROGRESS:   ChangeStatus.PENDING,
            RegulationStatus.CHANGE_UNDER_DISCUSSION: ChangeStatus.PENDING,
            RegulationStatus.PROPOSED:                ChangeStatus.DRAFT,
            RegulationStatus.EXPIRED:                 ChangeStatus.SUPERSEDED,
            RegulationStatus.REPEALED:                ChangeStatus.SUPERSEDED,
        }
        return mapping.get(status, ChangeStatus.DRAFT)


# ════════════════════════════════════════════════════════════════════════════
# JSON LOADER — monthly changelog format (from regulatory_data/changelogs/)
# ════════════════════════════════════════════════════════════════════════════

def load_monthly_changelog_from_json(file_path: str) -> MonthlyChangelog:
    """
    Load a MonthlyChangelog from a JSON file written by FileSystemRegulationStore.

    The file format is the serialised dict produced by
    FileSystemRegulationStore._serialize_changelog() — structured by category
    (new_regulations, status_changes, …) rather than a flat entry list.

    Args:
        file_path: Path to the changelog JSON file (e.g. regulatory_data/changelogs/2026-02.json)

    Returns:
        MonthlyChangelog with all entry lists populated.
    """
    import json
    from pathlib import Path

    raw = json.loads(Path(file_path).read_text())

    def _parse_entries(items: list) -> List[MonthlyChangelogEntry]:
        entries = []
        for item in items:
            entries.append(_deserialise_changelog_entry(item))
        return entries

    changelog = MonthlyChangelog(
        screening_period=raw["screening_period"],
        generated_date=date.fromisoformat(raw["generated_date"]),
        previous_period=raw["previous_period"],
        executive_summary=raw.get("executive_summary", ""),
        total_regulations_tracked=raw.get("total_regulations_tracked", 0),
        total_changes_detected=raw.get("total_changes_detected", 0),
        new_regulations=_parse_entries(raw.get("new_regulations", [])),
        status_changes=_parse_entries(raw.get("status_changes", [])),
        content_updates=_parse_entries(raw.get("content_updates", [])),
        timeline_changes=_parse_entries(raw.get("timeline_changes", [])),
        metadata_updates=_parse_entries(raw.get("metadata_updates", [])),
        ended_regulations=_parse_entries(raw.get("ended_regulations", [])),
        carried_forward=_parse_entries(raw.get("carried_forward", [])),
        critical_actions=_parse_entries(raw.get("critical_actions", [])),
    )
    return changelog


def _deserialise_changelog_entry(item: Dict[str, Any]) -> MonthlyChangelogEntry:
    """
    Reconstruct a MonthlyChangelogEntry from its serialised dict form.

    Handles the format written by FileSystemRegulationStore._serialize_entry().
    """
    changes = [
        ChangeDetail(
            field_name=c.get("field", ""),
            old_value=c.get("old"),
            new_value=c.get("new"),
            change_description=c.get("description"),
        )
        for c in item.get("changes", [])
    ]

    topic_raw = item.get("topic", "ghg")
    try:
        topic = TopicCategory(topic_raw)
    except ValueError:
        topic = TopicCategory.GHG

    change_type_raw = item.get("change_type", "no_change")
    try:
        change_type = ChangeType(change_type_raw)
    except ValueError:
        change_type = ChangeType.NO_CHANGE

    severity_raw = item.get("severity", "info")
    try:
        severity = ChangeSeverity(severity_raw)
    except ValueError:
        severity = ChangeSeverity.INFO

    current_status_raw = item.get("current_status", "proposed")
    try:
        current_status = RegulationStatus(current_status_raw)
    except ValueError:
        current_status = RegulationStatus.PROPOSED

    return MonthlyChangelogEntry(
        regulation_id=item["regulation_id"],
        title=item.get("title", ""),
        topic=topic,
        change_type=change_type,
        severity=severity,
        changes=changes,
        current_status=current_status,
        effective_date=date.fromisoformat(item["effective_date"]) if item.get("effective_date") else None,
        enforcement_date=date.fromisoformat(item["enforcement_date"]) if item.get("enforcement_date") else None,
        summary=item.get("summary", ""),
        action_required=item.get("action_required"),
    )
