#!/usr/bin/env python3
"""
Monthly Regulatory Screening Module

Technical changelog generation for tracking regulatory changes across
GHG, Packaging, Water, Waste, and Social/Human Rights topics.
"""

from __future__ import annotations

import json
import difflib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import date
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional, Dict, Any, Protocol, Tuple, Set
from uuid import UUID, uuid4

from config import get_config


# ============================================================================
# ENUMERATIONS
# ============================================================================

class TopicCategory(Enum):
    """Regulatory topic categories."""
    GHG = "ghg"
    PACKAGING = "packaging"
    WATER = "water"
    WASTE = "waste"
    SOCIAL_HUMAN_RIGHTS = "social_human_rights"


class RegulationStatus(Enum):
    """Possible statuses for regulations."""
    LAW_PASSED = "law_passed"
    AMENDMENT_IN_PROGRESS = "amendment_in_progress"
    CHANGE_UNDER_DISCUSSION = "change_under_discussion"
    PROPOSED = "proposed"
    EXPIRED = "expired"
    REPEALED = "repealed"


class GeographicScope(Enum):
    """Geographic applicability levels."""
    GLOBAL = "global"
    REGIONAL = "regional"
    NATIONAL = "national"
    STATE = "state"
    LOCAL = "local"


class ChangeType(Enum):
    """Types of changes detected."""
    NEW_REGULATION = "new_regulation"
    STATUS_PROMOTED_TO_LAW = "status_promoted_to_law"
    STATUS_ADVANCING = "status_advancing"
    LAW_BEING_AMENDED = "law_being_amended"
    TIMELINE_UPDATED = "timeline_updated"
    CONTENT_UPDATED = "content_updated"
    METADATA_UPDATED = "metadata_updated"
    LAW_EXPIRED = "law_expired"
    REGULATION_ENDED = "regulation_ended"
    REGULATION_REMOVED = "regulation_removed"
    NO_CHANGE = "no_change"
    CARRIED_FORWARD = "carried_forward"


class ChangeSeverity(Enum):
    """Severity levels for changes."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# ============================================================================
# INPUT DATA MODELS
# ============================================================================

@dataclass
class RegulatoryReference:
    """External reference to regulation source."""
    source_name: str
    source_url: Optional[str] = None
    document_id: Optional[str] = None
    access_date: date = field(default_factory=date.today)


@dataclass
class ScreeningInputItem:
    """Single regulation entry from monthly screening."""
    regulation_id: str
    title: str
    topic: TopicCategory
    description: str
    requirements_summary: str
    current_status: RegulationStatus
    effective_date: Optional[date] = None
    enforcement_date: Optional[date] = None
    review_deadline: Optional[date] = None
    geographic_scope: GeographicScope = GeographicScope.NATIONAL
    applicable_countries: List[str] = field(default_factory=list)
    version_date: date = field(default_factory=date.today)
    references: List[RegulatoryReference] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    screening_source: str = ""
    confidence_score: float = 1.0
    notes: str = ""


@dataclass
class MonthlyScreeningInput:
    """Complete input for a month's screening cycle."""
    screening_period: str
    screening_date: date
    screened_by: str
    regulations: List[ScreeningInputItem]
    topics_covered: List[TopicCategory] = field(default_factory=list)
    data_quality_flags: List[str] = field(default_factory=list)


# ============================================================================
# OUTPUT DATA MODELS
# ============================================================================

@dataclass
class ChangeDetail:
    """Specific field that changed."""
    field_name: str
    old_value: Any
    new_value: Any
    change_description: Optional[str] = None


@dataclass
class ChangelogEntry:
    """Single regulation change entry."""
    regulation_id: str
    title: str
    topic: TopicCategory
    change_type: ChangeType
    severity: ChangeSeverity
    changes: List[ChangeDetail] = field(default_factory=list)
    current_status: RegulationStatus = RegulationStatus.PROPOSED
    effective_date: Optional[date] = None
    enforcement_date: Optional[date] = None
    geographic_scope: GeographicScope = GeographicScope.NATIONAL
    previous_version_date: Optional[date] = None
    first_seen_period: str = ""
    summary: str = ""
    action_required: Optional[str] = None
    entry_date: date = field(default_factory=date.today)


@dataclass
class TopicSummary:
    """Summary for a specific topic."""
    topic: TopicCategory
    new_regulations: int = 0
    status_changes: int = 0
    content_updates: int = 0
    timeline_changes: int = 0
    carried_forward: int = 0
    removed: int = 0
    critical_items: List[str] = field(default_factory=list)

@dataclass
class TopicChangeStatus:
    """Per-topic change status for the monthly technical screening."""
    topic: TopicCategory
    changed_since_last: bool = False
    level: Optional[RegulationStatus] = None  # law_passed | amendment_in_progress | change_under_discussion
    changes_detected: int = 0


@dataclass
class MonthlyChangelog:
    """Complete monthly changelog output."""
    screening_period: str
    generated_date: date
    previous_period: str
    new_regulations: List[ChangelogEntry] = field(default_factory=list)
    status_changes: List[ChangelogEntry] = field(default_factory=list)
    content_updates: List[ChangelogEntry] = field(default_factory=list)
    timeline_changes: List[ChangelogEntry] = field(default_factory=list)
    metadata_updates: List[ChangelogEntry] = field(default_factory=list)
    ended_regulations: List[ChangelogEntry] = field(default_factory=list)
    carried_forward: List[ChangelogEntry] = field(default_factory=list)
    topic_summaries: Dict[TopicCategory, TopicSummary] = field(default_factory=dict)
    topic_change_statuses: Dict[TopicCategory, TopicChangeStatus] = field(default_factory=dict)
    critical_actions: List[ChangelogEntry] = field(default_factory=list)
    total_regulations_tracked: int = 0
    total_changes_detected: int = 0
    executive_summary: str = ""
    
    def all_entries(self) -> List[ChangelogEntry]:
        """Flatten all entries for reporting."""
        return (
            self.new_regulations +
            self.status_changes +
            self.content_updates +
            self.timeline_changes +
            self.metadata_updates +
            self.ended_regulations +
            self.carried_forward
        )


# ============================================================================
# INTERNAL CLASSES
# ============================================================================

@dataclass
class FieldChange:
    """Internal field change tracking."""
    field_name: str
    old_value: Any
    new_value: Any
    description: Optional[str] = None


@dataclass
class RegulationDiff:
    """Internal class for tracking regulation differences."""
    regulation_id: str = ""
    previous_version_date: Optional[date] = None
    current_version_date: Optional[date] = None
    changes: List[FieldChange] = field(default_factory=list)
    
    def add_change(
        self,
        field: str,
        old: Any,
        new: Any,
        description: Optional[str] = None
    ) -> None:
        self.changes.append(FieldChange(field, old, new, description))
    
    def has_changes(self) -> bool:
        return len(self.changes) > 0


# ============================================================================
# STORAGE PROTOCOLS
# ============================================================================

class RegulationStore(Protocol):
    """Protocol for regulation persistence layer."""
    
    def get_previous_state(self, period: str) -> MonthlyScreeningInput:
        """Retrieve previous month's screening state."""
        ...
    
    def save_state(self, period: str, screening: MonthlyScreeningInput) -> None:
        """Save current screening as new state."""
        ...


class ScreeningSource(Protocol):
    """Protocol for data ingestion sources."""
    
    def fetch_screening_data(self, period: str) -> MonthlyScreeningInput:
        """Fetch screening data for a period."""
        ...


# ============================================================================
# FILE SYSTEM STORAGE IMPLEMENTATION
# ============================================================================

class FileSystemRegulationStore:
    """File-based storage for regulation states."""
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.states_path = self.base_path / "states"
        self.changelogs_path = self.base_path / "changelogs"
        self.states_path.mkdir(exist_ok=True)
        self.changelogs_path.mkdir(exist_ok=True)
    
    def get_previous_state(self, period: str) -> Optional[MonthlyScreeningInput]:
        """Load screening state for a period."""
        file_path = self.states_path / f"{period}.json"
        
        if not file_path.exists():
            return None
        
        data = json.loads(file_path.read_text())
        return self._deserialize_screening(data)
    
    def save_state(self, period: str, screening: MonthlyScreeningInput) -> None:
        """Save screening state."""
        file_path = self.states_path / f"{period}.json"
        data = self._serialize_screening(screening)
        file_path.write_text(json.dumps(data, indent=2, default=str))
    
    def save_changelog(self, changelog: MonthlyChangelog) -> None:
        """Archive generated changelog."""
        file_path = self.changelogs_path / f"{changelog.screening_period}.json"
        data = self._serialize_changelog(changelog)
        file_path.write_text(json.dumps(data, indent=2, default=str))
    
    def _serialize_screening(self, screening: MonthlyScreeningInput) -> Dict:
        """Convert screening to JSON-serializable dict."""
        return {
            "screening_period": screening.screening_period,
            "screening_date": screening.screening_date.isoformat(),
            "screened_by": screening.screened_by,
            "topics_covered": [t.value for t in screening.topics_covered],
            "data_quality_flags": screening.data_quality_flags,
            "regulations": [
                {
                    "regulation_id": r.regulation_id,
                    "title": r.title,
                    "topic": r.topic.value,
                    "description": r.description,
                    "requirements_summary": r.requirements_summary,
                    "current_status": r.current_status.value,
                    "effective_date": r.effective_date.isoformat() if r.effective_date else None,
                    "enforcement_date": r.enforcement_date.isoformat() if r.enforcement_date else None,
                    "review_deadline": r.review_deadline.isoformat() if r.review_deadline else None,
                    "geographic_scope": r.geographic_scope.value,
                    "applicable_countries": r.applicable_countries,
                    "version_date": r.version_date.isoformat(),
                    "tags": r.tags,
                    "screening_source": r.screening_source,
                    "confidence_score": r.confidence_score,
                    "notes": r.notes,
                }
                for r in screening.regulations
            ]
        }
    
    def _deserialize_screening(self, data: Dict) -> MonthlyScreeningInput:
        """Convert dict back to ScreeningInputItem."""
        regulations = []
        for r in data.get("regulations", []):
            regulations.append(ScreeningInputItem(
                regulation_id=r["regulation_id"],
                title=r["title"],
                topic=TopicCategory(r["topic"]),
                description=r["description"],
                requirements_summary=r["requirements_summary"],
                current_status=RegulationStatus(r["current_status"]),
                effective_date=date.fromisoformat(r["effective_date"]) if r.get("effective_date") else None,
                enforcement_date=date.fromisoformat(r["enforcement_date"]) if r.get("enforcement_date") else None,
                review_deadline=date.fromisoformat(r["review_deadline"]) if r.get("review_deadline") else None,
                geographic_scope=GeographicScope(r["geographic_scope"]),
                applicable_countries=r.get("applicable_countries", []),
                version_date=date.fromisoformat(r["version_date"]),
                tags=r.get("tags", []),
                screening_source=r.get("screening_source", ""),
                confidence_score=r.get("confidence_score", 1.0),
                notes=r.get("notes", ""),
            ))
        
        return MonthlyScreeningInput(
            screening_period=data["screening_period"],
            screening_date=date.fromisoformat(data["screening_date"]),
            screened_by=data["screened_by"],
            regulations=regulations,
            topics_covered=[TopicCategory(t) for t in data.get("topics_covered", [])],
            data_quality_flags=data.get("data_quality_flags", []),
        )
    
    def _serialize_changelog(self, changelog: MonthlyChangelog) -> Dict:
        """Convert changelog to JSON-serializable dict."""
        return {
            "screening_period": changelog.screening_period,
            "generated_date": changelog.generated_date.isoformat(),
            "previous_period": changelog.previous_period,
            "executive_summary": changelog.executive_summary,
            "total_regulations_tracked": changelog.total_regulations_tracked,
            "total_changes_detected": changelog.total_changes_detected,
            "topic_change_statuses": {
                topic.value: {
                    "changed_since_last": status.changed_since_last,
                    "level": status.level.value if status.level else None,
                    "changes_detected": status.changes_detected,
                }
                for topic, status in changelog.topic_change_statuses.items()
            },
            "new_regulations": [self._serialize_entry(e) for e in changelog.new_regulations],
            "status_changes": [self._serialize_entry(e) for e in changelog.status_changes],
            "content_updates": [self._serialize_entry(e) for e in changelog.content_updates],
            "timeline_changes": [self._serialize_entry(e) for e in changelog.timeline_changes],
            "metadata_updates": [self._serialize_entry(e) for e in changelog.metadata_updates],
            "ended_regulations": [self._serialize_entry(e) for e in changelog.ended_regulations],
            "carried_forward": [self._serialize_entry(e) for e in changelog.carried_forward],
            "critical_actions": [self._serialize_entry(e) for e in changelog.critical_actions],
        }
    
    def _serialize_entry(self, entry: ChangelogEntry) -> Dict:
        """Convert entry to dict."""
        return {
            "regulation_id": entry.regulation_id,
            "title": entry.title,
            "topic": entry.topic.value,
            "change_type": entry.change_type.value,
            "severity": entry.severity.value,
            "summary": entry.summary,
            "action_required": entry.action_required,
            "current_status": entry.current_status.value,
            "effective_date": entry.effective_date.isoformat() if entry.effective_date else None,
            "enforcement_date": entry.enforcement_date.isoformat() if entry.enforcement_date else None,
            "changes": [
                {
                    "field": c.field_name,
                    "old": str(c.old_value) if c.old_value is not None else None,
                    "new": str(c.new_value) if c.new_value is not None else None,
                    "description": c.change_description,
                }
                for c in entry.changes
            ]
        }


# ============================================================================
# MAIN SCREENING MODULE
# ============================================================================

class RegulatoryScreeningModule:
    """Main module for monthly regulatory screening and changelog generation."""
    
    def __init__(
        self,
        store: RegulationStore,
        sources: Optional[List[ScreeningSource]] = None,
        config: Optional[Dict] = None
    ):
        self.store = store
        self.sources = sources or []
        _cfg = get_config()
        # Merge YAML defaults under any caller-supplied config dict.
        _defaults: Dict[str, Any] = {
            "allowed_countries": _cfg.screening.allowed_countries,
            "critical_enforcement_window_days": _cfg.screening.critical_enforcement_window_days,
        }
        self.config = {**_defaults, **(config or {})}
        self.critical_enforcement_days = self.config.get("critical_enforcement_window_days")
    
    # ==================== PUBLIC API ====================
    
    def run_monthly_screening(
        self,
        period: str,
        input_data: Optional[MonthlyScreeningInput] = None
    ) -> MonthlyChangelog:
        """Execute full monthly screening workflow."""
        # Step 1: Get new screening data
        if input_data is None:
            new_screening = self._fetch_screening_data(period)
        else:
            new_screening = input_data

        new_screening = self._normalize_screening_input(new_screening)
        
        # Step 2: Get previous state
        previous_period = self._get_previous_period(period)
        previous_state = self.store.get_previous_state(previous_period)
        
        # Step 3: Detect changes
        changelog = self._generate_changelog(
            new_screening=new_screening,
            previous_state=previous_state,
            previous_period=previous_period
        )
        
        # Step 4: Post-processing
        changelog = self._post_process_changelog(changelog)
        
        # Step 5: Persist state
        self.store.save_state(period, new_screening)
        
        return changelog

    def _normalize_screening_input(self, screening: MonthlyScreeningInput) -> MonthlyScreeningInput:
        """
        Normalize inputs so the monthly technical screening is consistent:
        - Enforce optional jurisdiction filtering via `allowed_countries`
        - Always mark all topics as covered (per-topic "no change" still required)
        - Emit data quality flags for topics with no items
        """
        allowed_countries = set(self.config.get("allowed_countries", []))
        regulations = screening.regulations
        if allowed_countries:
            regulations = [
                r for r in regulations
                if set(r.applicable_countries).intersection(allowed_countries)
            ]

        present_topics = {r.topic for r in regulations}
        data_quality_flags = list(screening.data_quality_flags or [])
        for topic in TopicCategory:
            if topic not in present_topics:
                flag = f"no_items_for_topic:{topic.value}"
                if flag not in data_quality_flags:
                    data_quality_flags.append(flag)

        return MonthlyScreeningInput(
            screening_period=screening.screening_period,
            screening_date=screening.screening_date,
            screened_by=screening.screened_by,
            regulations=regulations,
            topics_covered=list(TopicCategory),
            data_quality_flags=data_quality_flags,
        )
    
    def export_changelog(
        self,
        changelog: MonthlyChangelog,
        format: str = "json",
        output_path: Optional[Path] = None
    ) -> str:
        """Export changelog to various formats."""
        exporters = {
            "json": self._export_json,
            "markdown": self._export_markdown,
        }
        
        exporter = exporters.get(format, self._export_json)
        return exporter(changelog, output_path)
    
    # ==================== CORE LOGIC ====================
    
    def _generate_changelog(
        self,
        new_screening: MonthlyScreeningInput,
        previous_state: Optional[MonthlyScreeningInput],
        previous_period: str
    ) -> MonthlyChangelog:
        """Core algorithm for change detection."""
        
        changelog = MonthlyChangelog(
            screening_period=new_screening.screening_period,
            generated_date=date.today(),
            previous_period=previous_period
        )
        
        # Build lookup from previous state
        prev_by_id: Dict[str, ScreeningInputItem] = {}
        first_seen_dates: Dict[str, str] = {}
        
        if previous_state:
            for reg in previous_state.regulations:
                prev_by_id[reg.regulation_id] = reg
                first_seen_dates[reg.regulation_id] = previous_period
        
        processed_ids: Set[str] = set()
        
        # Process each new regulation
        for new_reg in new_screening.regulations:
            reg_id = new_reg.regulation_id
            processed_ids.add(reg_id)
            
            prev_reg = prev_by_id.get(reg_id)
            
            if prev_reg is None:
                # NEW REGULATION
                entry = self._create_new_regulation_entry(
                    new_reg, new_screening.screening_period
                )
                changelog.new_regulations.append(entry)
                
            else:
                # EXISTING - check for changes
                diff = self._compare_regulations(prev_reg, new_reg)
                
                if diff.has_changes():
                    entry = self._create_change_entry(
                        prev_reg, new_reg, diff, 
                        first_seen_dates.get(reg_id, previous_period)
                    )
                    self._categorize_entry(changelog, entry)
                else:
                    # NO CHANGE - carry forward
                    entry = self._create_carry_forward_entry(
                        new_reg, first_seen_dates.get(reg_id, previous_period)
                    )
                    changelog.carried_forward.append(entry)
        
        # Check for removed/expired regulations
        if previous_state:
            for prev_reg in previous_state.regulations:
                if prev_reg.regulation_id not in processed_ids:
                    entry = self._create_removal_entry(prev_reg)
                    changelog.ended_regulations.append(entry)
        
        # Calculate statistics
        changelog.total_changes_detected = (
            len(changelog.new_regulations) +
            len(changelog.status_changes) +
            len(changelog.content_updates) +
            len(changelog.timeline_changes) +
            len(changelog.metadata_updates) +
            len(changelog.ended_regulations)
        )
        changelog.total_regulations_tracked = len(new_screening.regulations)
        
        return changelog
    
    def _compare_regulations(
        self,
        old: ScreeningInputItem,
        new: ScreeningInputItem
    ) -> RegulationDiff:
        """Detailed field-by-field comparison."""
        diff = RegulationDiff(
            regulation_id=old.regulation_id,
            previous_version_date=old.version_date,
            current_version_date=new.version_date
        )
        
        if old.current_status != new.current_status:
            diff.add_change(
                field="status",
                old=old.current_status,
                new=new.current_status,
                description=f"Status: {old.current_status.value} → {new.current_status.value}"
            )
        
        if old.title != new.title:
            diff.add_change(field="title", old=old.title, new=new.title)
        
        if old.description != new.description:
            diff.add_change(
                field="description",
                old=old.description,
                new=new.description,
                description=self._generate_text_diff(old.description, new.description)
            )
        
        if old.requirements_summary != new.requirements_summary:
            diff.add_change(
                field="requirements",
                old=old.requirements_summary,
                new=new.requirements_summary
            )
        
        if old.effective_date != new.effective_date:
            diff.add_change(
                field="effective_date",
                old=old.effective_date,
                new=new.effective_date
            )
        
        if old.enforcement_date != new.enforcement_date:
            diff.add_change(
                field="enforcement_date",
                old=old.enforcement_date,
                new=new.enforcement_date
            )
        
        if old.review_deadline != new.review_deadline:
            diff.add_change(
                field="review_deadline",
                old=old.review_deadline,
                new=new.review_deadline
            )
        
        if old.geographic_scope != new.geographic_scope:
            diff.add_change(
                field="geographic_scope",
                old=old.geographic_scope,
                new=new.geographic_scope
            )
        
        if set(old.applicable_countries) != set(new.applicable_countries):
            diff.add_change(
                field="applicable_countries",
                old=old.applicable_countries,
                new=new.applicable_countries
            )
        
        return diff
    
    def _classify_change_type(self, diff: RegulationDiff) -> ChangeType:
        """Classify change based on priority rules."""
        changes = {c.field_name for c in diff.changes}
        
        # Status changes
        if "status" in changes:
            status_change = next(c for c in diff.changes if c.field_name == "status")
            old_status = status_change.old_value
            new_status = status_change.new_value
            
            if new_status == RegulationStatus.LAW_PASSED:
                return ChangeType.STATUS_PROMOTED_TO_LAW
            
            if new_status in (RegulationStatus.EXPIRED, RegulationStatus.REPEALED):
                if old_status == RegulationStatus.LAW_PASSED:
                    return ChangeType.LAW_EXPIRED
                return ChangeType.REGULATION_ENDED
            
            if old_status == RegulationStatus.CHANGE_UNDER_DISCUSSION and \
               new_status == RegulationStatus.AMENDMENT_IN_PROGRESS:
                return ChangeType.STATUS_ADVANCING
            
            if old_status == RegulationStatus.LAW_PASSED and \
               new_status == RegulationStatus.AMENDMENT_IN_PROGRESS:
                return ChangeType.LAW_BEING_AMENDED
        
        # Timeline changes
        if {"effective_date", "enforcement_date", "review_deadline"} & changes:
            return ChangeType.TIMELINE_UPDATED
        
        # Content changes
        if {"description", "requirements"} & changes:
            return ChangeType.CONTENT_UPDATED
        
        # Metadata changes
        if {"title", "geographic_scope", "applicable_countries"} & changes:
            return ChangeType.METADATA_UPDATED
        
        return ChangeType.NO_CHANGE
    
    def _calculate_severity(
        self,
        entry: ChangelogEntry,
        diff: Optional[RegulationDiff] = None
    ) -> ChangeSeverity:
        """Calculate severity based on change type."""
        if entry.change_type == ChangeType.STATUS_PROMOTED_TO_LAW:
            return ChangeSeverity.CRITICAL
        
        if entry.change_type == ChangeType.LAW_EXPIRED:
            return ChangeSeverity.CRITICAL
        
        if entry.change_type == ChangeType.TIMELINE_UPDATED:
            if diff and any(c.field_name == "enforcement_date" for c in diff.changes):
                return ChangeSeverity.CRITICAL
        
        if entry.change_type in (ChangeType.STATUS_ADVANCING, ChangeType.LAW_BEING_AMENDED):
            return ChangeSeverity.HIGH
        
        if entry.change_type == ChangeType.CONTENT_UPDATED:
            return ChangeSeverity.HIGH
        
        if entry.change_type == ChangeType.TIMELINE_UPDATED:
            return ChangeSeverity.MEDIUM
        
        if entry.change_type == ChangeType.METADATA_UPDATED:
            return ChangeSeverity.LOW
        
        if entry.change_type == ChangeType.NEW_REGULATION:
            # Check for imminent enforcement
            if (entry.enforcement_date and 
                (entry.enforcement_date - date.today()).days < self.critical_enforcement_days):
                return ChangeSeverity.CRITICAL
            return ChangeSeverity.INFO
        
        return ChangeSeverity.INFO
    
    # ==================== ENTRY CREATION ====================
    
    def _create_new_regulation_entry(
        self,
        reg: ScreeningInputItem,
        first_seen_period: str
    ) -> ChangelogEntry:
        """Create entry for newly identified regulation."""
        entry = ChangelogEntry(
            regulation_id=reg.regulation_id,
            title=reg.title,
            topic=reg.topic,
            change_type=ChangeType.NEW_REGULATION,
            severity=ChangeSeverity.INFO,  # Will be updated
            changes=[ChangeDetail(
                field_name="status",
                old_value=None,
                new_value=reg.current_status,
                change_description="First time identified in screening"
            )],
            current_status=reg.current_status,
            effective_date=reg.effective_date,
            enforcement_date=reg.enforcement_date,
            geographic_scope=reg.geographic_scope,
            first_seen_period=first_seen_period,
            summary=f"New regulation identified: {reg.title}",
            action_required=self._suggest_action_for_new(reg)
        )
        
        entry.severity = self._calculate_severity(entry)
        return entry
    
    def _create_change_entry(
        self,
        old: ScreeningInputItem,
        new: ScreeningInputItem,
        diff: RegulationDiff,
        first_seen_period: str
    ) -> ChangelogEntry:
        """Create entry for changed regulation."""
        change_type = self._classify_change_type(diff)
        
        entry = ChangelogEntry(
            regulation_id=new.regulation_id,
            title=new.title,
            topic=new.topic,
            change_type=change_type,
            severity=ChangeSeverity.INFO,
            changes=[
                ChangeDetail(
                    field_name=c.field_name,
                    old_value=c.old_value,
                    new_value=c.new_value,
                    change_description=c.description
                )
                for c in diff.changes
            ],
            current_status=new.current_status,
            effective_date=new.effective_date,
            enforcement_date=new.enforcement_date,
            geographic_scope=new.geographic_scope,
            previous_version_date=diff.previous_version_date,
            first_seen_period=first_seen_period
        )
        
        entry.severity = self._calculate_severity(entry, diff)
        entry.summary = self._generate_change_summary(entry, diff)
        entry.action_required = self._suggest_action_for_change(entry, diff)
        
        return entry
    
    def _create_carry_forward_entry(
        self,
        reg: ScreeningInputItem,
        first_seen_period: str
    ) -> ChangelogEntry:
        """Create entry for unchanged regulation."""
        return ChangelogEntry(
            regulation_id=reg.regulation_id,
            title=reg.title,
            topic=reg.topic,
            change_type=ChangeType.CARRIED_FORWARD,
            severity=ChangeSeverity.INFO,
            current_status=reg.current_status,
            effective_date=reg.effective_date,
            enforcement_date=reg.enforcement_date,
            geographic_scope=reg.geographic_scope,
            first_seen_period=first_seen_period,
            summary=f"No changes - status: {reg.current_status.value}"
        )
    
    def _create_removal_entry(self, reg: ScreeningInputItem) -> ChangelogEntry:
        """Create entry for regulation no longer found."""
        return ChangelogEntry(
            regulation_id=reg.regulation_id,
            title=reg.title,
            topic=reg.topic,
            change_type=ChangeType.REGULATION_REMOVED,
            severity=ChangeSeverity.HIGH,
            changes=[ChangeDetail(
                field_name="presence",
                old_value="tracked",
                new_value="not_found",
                change_description="Regulation not found in current screening"
            )],
            current_status=reg.current_status,
            summary="Regulation no longer tracked - may be expired or repealed",
            action_required="Verify status with regulatory source"
        )
    
    def _categorize_entry(
        self,
        changelog: MonthlyChangelog,
        entry: ChangelogEntry
    ) -> None:
        """Route entry to appropriate list."""
        category_map = {
            ChangeType.NEW_REGULATION: changelog.new_regulations,
            ChangeType.STATUS_PROMOTED_TO_LAW: changelog.status_changes,
            ChangeType.STATUS_ADVANCING: changelog.status_changes,
            ChangeType.LAW_BEING_AMENDED: changelog.status_changes,
            ChangeType.TIMELINE_UPDATED: changelog.timeline_changes,
            ChangeType.CONTENT_UPDATED: changelog.content_updates,
            ChangeType.METADATA_UPDATED: changelog.metadata_updates,
            ChangeType.LAW_EXPIRED: changelog.ended_regulations,
            ChangeType.REGULATION_ENDED: changelog.ended_regulations,
            ChangeType.REGULATION_REMOVED: changelog.ended_regulations,
        }
        
        target_list = category_map.get(entry.change_type)
        if target_list is not None:
            target_list.append(entry)
        
        if entry.severity in (ChangeSeverity.CRITICAL, ChangeSeverity.HIGH):
            changelog.critical_actions.append(entry)
    
    # ==================== POST-PROCESSING ====================
    
    def _post_process_changelog(self, changelog: MonthlyChangelog) -> MonthlyChangelog:
        """Final processing: sort, summarize."""
        # Sort by severity then topic
        for entry_list in [
            changelog.new_regulations,
            changelog.status_changes,
            changelog.content_updates,
            changelog.timeline_changes,
            changelog.metadata_updates,
            changelog.ended_regulations,
            changelog.carried_forward
        ]:
            entry_list.sort(key=lambda e: (e.severity.value, e.topic.value))
        
        # Generate summaries
        changelog.topic_summaries = self._generate_topic_summaries(changelog)
        changelog.topic_change_statuses = self._generate_topic_change_statuses(changelog)
        changelog.executive_summary = self._generate_executive_summary(changelog)
        
        return changelog

    def _generate_topic_change_statuses(
        self,
        changelog: MonthlyChangelog,
    ) -> Dict[TopicCategory, TopicChangeStatus]:
        """
        Required monthly output: per topic, whether there was a change since last reporting and at
        which level (law passed, amendment in progress, change under discussion).
        """
        # Priority: higher number => higher level of change.
        level_priority = {
            RegulationStatus.LAW_PASSED: 3,
            RegulationStatus.AMENDMENT_IN_PROGRESS: 2,
            RegulationStatus.CHANGE_UNDER_DISCUSSION: 1,
        }

        statuses: Dict[TopicCategory, TopicChangeStatus] = {}
        for topic in TopicCategory:
            status = TopicChangeStatus(topic=topic)

            for entry in changelog.all_entries():
                if entry.topic != topic:
                    continue
                if entry.change_type in (ChangeType.CARRIED_FORWARD, ChangeType.NO_CHANGE):
                    continue

                status.changed_since_last = True
                status.changes_detected += 1

                candidate = entry.current_status
                if candidate in level_priority:
                    if status.level is None:
                        status.level = candidate
                    else:
                        if level_priority[candidate] > level_priority.get(status.level, 0):
                            status.level = candidate

            statuses[topic] = status

        return statuses
    
    def _generate_topic_summaries(
        self,
        changelog: MonthlyChangelog
    ) -> Dict[TopicCategory, TopicSummary]:
        """Generate per-topic statistics."""
        summaries = {}
        
        for topic in TopicCategory:
            summary = TopicSummary(topic=topic)
            
            for entry in changelog.all_entries():
                if entry.topic == topic:
                    if entry.change_type == ChangeType.NEW_REGULATION:
                        summary.new_regulations += 1
                    elif entry.change_type in (
                        ChangeType.STATUS_PROMOTED_TO_LAW,
                        ChangeType.STATUS_ADVANCING,
                        ChangeType.LAW_BEING_AMENDED
                    ):
                        summary.status_changes += 1
                    elif entry.change_type == ChangeType.CONTENT_UPDATED:
                        summary.content_updates += 1
                    elif entry.change_type == ChangeType.TIMELINE_UPDATED:
                        summary.timeline_changes += 1
                    elif entry.change_type == ChangeType.CARRIED_FORWARD:
                        summary.carried_forward += 1
                    elif entry.change_type in (
                        ChangeType.LAW_EXPIRED,
                        ChangeType.REGULATION_ENDED,
                        ChangeType.REGULATION_REMOVED
                    ):
                        summary.removed += 1
                    
                    if entry.severity == ChangeSeverity.CRITICAL:
                        summary.critical_items.append(entry.regulation_id)
            
            summaries[topic] = summary
        
        return summaries
    
    def _generate_executive_summary(self, changelog: MonthlyChangelog) -> str:
        """Generate narrative executive summary."""
        parts = [f"Regulatory Screening Report for {changelog.screening_period}\n"]
        
        critical_count = len(changelog.critical_actions)
        new_count = len(changelog.new_regulations)
        
        parts.append(
            f"• {changelog.total_regulations_tracked} regulations tracked\n"
            f"• {new_count} new regulations identified\n"
            f"• {changelog.total_changes_detected} changes detected ({critical_count} critical)\n"
        )
        
        if changelog.critical_actions:
            parts.append("\nCRITICAL ACTIONS REQUIRED:\n")
            for entry in changelog.critical_actions[:5]:
                parts.append(f"  - {entry.regulation_id}: {entry.action_required}\n")
        
        parts.append("\nBY TOPIC (change since last period):\n")
        for topic in TopicCategory:
            status = changelog.topic_change_statuses.get(topic) or TopicChangeStatus(topic=topic)
            if not status.changed_since_last:
                parts.append(f"  {topic.value}: no change\n")
                continue

            level = status.level.value if status.level else "unspecified"
            parts.append(f"  {topic.value}: CHANGED ({level})\n")
        
        return "".join(parts)
    
    # ==================== HELPERS ====================
    
    def _get_previous_period(self, current_period: str) -> str:
        """Calculate previous month from YYYY-MM format."""
        year, month = map(int, current_period.split("-"))
        if month == 1:
            return f"{year - 1}-12"
        else:
            return f"{year}-{month - 1:02d}"
    
    def _fetch_screening_data(self, period: str) -> MonthlyScreeningInput:
        """Aggregate from all sources."""
        all_regulations = []
        topics_covered: Set[TopicCategory] = set()
        
        for source in self.sources:
            screening = source.fetch_screening_data(period)
            all_regulations.extend(screening.regulations)
            topics_covered.update(screening.topics_covered)

        allowed_countries = set(self.config.get("allowed_countries", []))
        if allowed_countries:
            all_regulations = [
                r for r in all_regulations
                if set(r.applicable_countries).intersection(allowed_countries)
            ]

        # Deduplicate by regulation_id
        by_id: Dict[str, ScreeningInputItem] = {}
        for reg in all_regulations:
            if reg.regulation_id not in by_id:
                by_id[reg.regulation_id] = reg
            elif reg.confidence_score > by_id[reg.regulation_id].confidence_score:
                by_id[reg.regulation_id] = reg

        # Ensure monthly output always reports all required topics, even if "no change".
        topics_covered = set(TopicCategory)
        data_quality_flags: List[str] = []
        present_topics = {r.topic for r in by_id.values()}
        for topic in TopicCategory:
            if topic not in present_topics:
                data_quality_flags.append(f"no_items_for_topic:{topic.value}")
        
        return MonthlyScreeningInput(
            screening_period=period,
            screening_date=date.today(),
            screened_by="Automated Screening System",
            regulations=list(by_id.values()),
            topics_covered=list(topics_covered),
            data_quality_flags=data_quality_flags,
        )
    
    def _generate_text_diff(self, old_text: str, new_text: str) -> str:
        """Generate unified diff."""
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines, new_lines,
            fromfile="previous", tofile="current",
            lineterm=""
        )
        
        return "\n".join(list(diff)[:50])  # Limit length
    
    def _generate_change_summary(self, entry: ChangelogEntry, diff: RegulationDiff) -> str:
        """Generate human-readable summary."""
        summaries = []
        
        for change in entry.changes:
            if change.field_name == "status":
                old_val = change.old_value.value if change.old_value else "unknown"
                new_val = change.new_value.value if change.new_value else "unknown"
                summaries.append(f"Status: {old_val} → {new_val}")
            elif change.field_name == "enforcement_date":
                summaries.append(f"Enforcement: {change.new_value}")
            elif change.field_name == "requirements":
                summaries.append("Requirements updated")
        
        return "; ".join(summaries) if summaries else "Changes detected"
    
    def _suggest_action_for_new(self, reg: ScreeningInputItem) -> Optional[str]:
        """Suggest action for new regulation."""
        actions = {
            RegulationStatus.LAW_PASSED: "Review applicability and compliance requirements",
            RegulationStatus.AMENDMENT_IN_PROGRESS: "Monitor for final text and effective dates",
            RegulationStatus.CHANGE_UNDER_DISCUSSION: "Track for potential future impact",
            RegulationStatus.PROPOSED: "Assess potential impact if enacted",
        }
        return actions.get(reg.current_status, "Review and assess impact")
    
    def _suggest_action_for_change(
        self,
        entry: ChangelogEntry,
        diff: RegulationDiff
    ) -> Optional[str]:
        """Suggest action based on change."""
        if entry.change_type == ChangeType.STATUS_PROMOTED_TO_LAW:
            return "Confirm compliance strategy and implementation timeline"
        
        if entry.change_type == ChangeType.LAW_EXPIRED:
            return "Verify if replaced by new regulation"
        
        if entry.change_type == ChangeType.TIMELINE_UPDATED:
            date_change = next(
                (c for c in diff.changes if c.field_name == "enforcement_date"),
                None
            )
            if date_change:
                return f"Update compliance calendar: enforcement {date_change.new_value}"
        
        if entry.change_type == ChangeType.CONTENT_UPDATED:
            return "Review updated requirements for compliance impact"
        
        return None
    
    # ==================== EXPORT ====================
    
    def _export_json(
        self,
        changelog: MonthlyChangelog,
        output_path: Optional[Path] = None
    ) -> str:
        """Export to JSON."""
        store = FileSystemRegulationStore(self.store.base_path if hasattr(self.store, 'base_path') else Path("."))
        data = store._serialize_changelog(changelog)
        
        json_str = json.dumps(data, indent=2, default=str)
        
        if output_path:
            output_path.write_text(json_str)
        
        return json_str
    
    def _export_markdown(
        self,
        changelog: MonthlyChangelog,
        output_path: Optional[Path] = None
    ) -> str:
        """Export to Markdown."""
        lines = [
            f"# Monthly Regulatory Changelog: {changelog.screening_period}",
            "",
            f"**Generated:** {changelog.generated_date}",
            f"**Previous Period:** {changelog.previous_period}",
            "",
            "## Executive Summary",
            "",
            changelog.executive_summary,
            "",
            "## Statistics",
            "",
            f"- Total Regulations Tracked: {changelog.total_regulations_tracked}",
            f"- Changes Detected: {changelog.total_changes_detected}",
            f"- Critical Actions: {len(changelog.critical_actions)}",
            "",
        ]
        
        def add_section(title: str, entries: List[ChangelogEntry]) -> None:
            if not entries:
                return
            lines.extend([f"## {title}", ""])
            for entry in entries:
                lines.extend([
                    f"### {entry.regulation_id}: {entry.title}",
                    f"- **Topic:** {entry.topic.value}",
                    f"- **Severity:** {entry.severity.value}",
                    f"- **Status:** {entry.current_status.value}",
                    f"- **Summary:** {entry.summary}",
                ])
                if entry.action_required:
                    lines.append(f"- **Action Required:** {entry.action_required}")
                lines.append("")
        
        add_section("New Regulations", changelog.new_regulations)
        add_section("Status Changes", changelog.status_changes)
        add_section("Timeline Changes", changelog.timeline_changes)
        add_section("Content Updates", changelog.content_updates)
        add_section("Ended Regulations", changelog.ended_regulations)
        
        if changelog.critical_actions:
            lines.extend(["## Critical Actions Required", ""])
            for entry in changelog.critical_actions:
                lines.append(f"- **{entry.regulation_id}**: {entry.action_required}")
            lines.append("")
        
        md = "\n".join(lines)
        
        if output_path:
            output_path.write_text(md)
        
        return md


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def create_example_workflow():
    """Create example workflow demonstrating all scenarios."""
    
    # Initialize storage
    store = FileSystemRegulationStore(Path("./regulatory_data"))
    
    # Initialize module
    module = RegulatoryScreeningModule(
        store=store,
        config={
            "critical_enforcement_window_days": 90,
            "allowed_countries": ["EU", "DE"],
        }
    )
    
    # January 2026 - Initial state
    january_input = MonthlyScreeningInput(
        screening_period="2026-01",
        screening_date=date(2026, 1, 31),
        screened_by="Test System",
        regulations=[
            ScreeningInputItem(
                regulation_id="EU-CSRD-2022",
                title="Corporate Sustainability Reporting Directive",
                topic=TopicCategory.GHG,
                description="Comprehensive sustainability reporting requirements",
                requirements_summary="Report Scope 1, 2, 3 emissions",
                current_status=RegulationStatus.AMENDMENT_IN_PROGRESS,
                geographic_scope=GeographicScope.REGIONAL,
                applicable_countries=["EU"],
            ),
            ScreeningInputItem(
                regulation_id="DE-Packaging-Act",
                title="German Packaging Act",
                topic=TopicCategory.PACKAGING,
                description="Requirements for packaging registration and recycling",
                requirements_summary="Register packaging quantities",
                current_status=RegulationStatus.LAW_PASSED,
                enforcement_date=date(2025, 6, 1),
                geographic_scope=GeographicScope.NATIONAL,
                applicable_countries=["DE"],
            ),
        ],
        topics_covered=[TopicCategory.GHG, TopicCategory.PACKAGING]
    )
    
    # Run January screening
    print("=" * 60)
    print("JANUARY 2026 SCREENING (Initial)")
    print("=" * 60)
    
    jan_changelog = module.run_monthly_screening(
        period="2026-01",
        input_data=january_input
    )
    
    print(f"\nTotal tracked: {jan_changelog.total_regulations_tracked}")
    print(f"New regulations: {len(jan_changelog.new_regulations)}")
    print(f"Carried forward: {len(jan_changelog.carried_forward)}")
    
    # February 2026 - Multiple changes
    february_input = MonthlyScreeningInput(
        screening_period="2026-02",
        screening_date=date(2026, 2, 28),
        screened_by="Test System",
        regulations=[
            ScreeningInputItem(
                regulation_id="EU-CSRD-2022",
                title="Corporate Sustainability Reporting Directive",
                topic=TopicCategory.GHG,
                description="Comprehensive sustainability reporting requirements",
                requirements_summary="Report Scope 1, 2, 3 emissions with assurance",
                current_status=RegulationStatus.LAW_PASSED,  # STATUS CHANGE!
                enforcement_date=date(2025, 1, 1),  # NEW DATE!
                geographic_scope=GeographicScope.REGIONAL,
                applicable_countries=["EU"],
            ),
            ScreeningInputItem(
                regulation_id="DE-Packaging-Act",
                title="German Packaging Act",
                topic=TopicCategory.PACKAGING,
                description="Requirements for packaging registration and recycling",
                requirements_summary="Register packaging quantities",
                current_status=RegulationStatus.LAW_PASSED,
                enforcement_date=date(2025, 6, 1),
                geographic_scope=GeographicScope.NATIONAL,
                applicable_countries=["DE"],
            ),
            ScreeningInputItem(
                regulation_id="EU-Water-Framework",
                title="Water Framework Directive Update",
                topic=TopicCategory.WATER,
                description="Updated water quality standards",
                requirements_summary="Monitor discharge limits",
                current_status=RegulationStatus.CHANGE_UNDER_DISCUSSION,
                geographic_scope=GeographicScope.REGIONAL,
                applicable_countries=["EU"],
            ),
        ],
        topics_covered=[TopicCategory.GHG, TopicCategory.PACKAGING, TopicCategory.WATER]
    )
    
    # Run February screening
    print("\n" + "=" * 60)
    print("FEBRUARY 2026 SCREENING (Changes Detected)")
    print("=" * 60)
    
    feb_changelog = module.run_monthly_screening(
        period="2026-02",
        input_data=february_input
    )
    
    print(f"\n{feb_changelog.executive_summary}")
    
    print("\n--- CHANGE DETAILS ---")
    print(f"\nNew Regulations ({len(feb_changelog.new_regulations)}):")
    for e in feb_changelog.new_regulations:
        print(f"  - {e.regulation_id}: {e.title} [{e.severity.value}]")
    
    print(f"\nStatus Changes ({len(feb_changelog.status_changes)}):")
    for e in feb_changelog.status_changes:
        print(f"  - {e.regulation_id}: {e.summary} [{e.severity.value}]")
        if e.action_required:
            print(f"    Action: {e.action_required}")
    
    print(f"\nCarried Forward ({len(feb_changelog.carried_forward)}):")
    for e in feb_changelog.carried_forward:
        print(f"  - {e.regulation_id}: {e.title}")
    
    # Export to files
    store.save_changelog(feb_changelog)
    
    md_output = module.export_changelog(feb_changelog, format="markdown")
    print("\n--- MARKDOWN PREVIEW (first 1000 chars) ---")
    print(md_output[:1000] + "...")
    
    return feb_changelog


if __name__ == "__main__":
    create_example_workflow()
