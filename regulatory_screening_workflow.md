# Monthly Regulatory Screening Workflow - Technical Design

## Overview
This document describes the monthly screening layer that produces the changelog artifact.

Historically, that artifact fed standalone monthly reporting and quarterly consolidation. In the current MARS draft-first flow, the changelog is an input to draft composition alongside template sections, evidence, keyword rules, and source proposals.

The supported live path is monthly screening -> changelog JSON -> draft revision -> approval -> export job.

---

## 1. Input Data Format

### 1.1 Monthly Screening Input Schema

```python
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

class TopicCategory(Enum):
    GHG = "ghg"
    PACKAGING = "packaging"
    WATER = "water"
    WASTE = "waste"
    SOCIAL_HUMAN_RIGHTS = "social_human_rights"

class RegulationStatus(Enum):
    LAW_PASSED = "law_passed"
    AMENDMENT_IN_PROGRESS = "amendment_in_progress"
    CHANGE_UNDER_DISCUSSION = "change_under_discussion"
    PROPOSED = "proposed"
    EXPIRED = "expired"
    REPEALED = "repealed"

class GeographicScope(Enum):
    GLOBAL = "global"
    REGIONAL = "regional"  # e.g., EU
    NATIONAL = "national"
    STATE = "state"
    LOCAL = "local"

@dataclass
class RegulatoryReference:
    """External reference to the regulation source."""
    source_name: str  # e.g., "EUR-Lex", "Federal Register"
    source_url: Optional[str] = None
    document_id: Optional[str] = None  # Official document reference
    access_date: date = field(default_factory=date.today)

@dataclass
class ScreeningInputItem:
    """Single regulation entry from monthly screening."""
    # Identification
    regulation_id: str  # Unique stable identifier (e.g., "EU-CSRD-2022")
    title: str
    topic: TopicCategory
    
    # Content
    description: str
    requirements_summary: str
    
    # Status & Timeline
    current_status: RegulationStatus
    effective_date: Optional[date] = None
    enforcement_date: Optional[date] = None
    review_deadline: Optional[date] = None
    
    # Scope
    geographic_scope: GeographicScope
    applicable_countries: List[str] = field(default_factory=list)
    
    # Metadata
    version_date: date = field(default_factory=date.today)
    references: List[RegulatoryReference] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # Screening metadata
    screening_source: str = ""  # Who/what identified this
    confidence_score: float = 1.0  # 0.0 to 1.0
    notes: str = ""

@dataclass  
class MonthlyScreeningInput:
    """Complete input for a month's screening cycle."""
    screening_period: str  # e.g., "2026-01"
    screening_date: date
    screened_by: str
    
    # All regulations identified this month
    regulations: List[ScreeningInputItem]
    
    # Metadata
    topics_covered: List[TopicCategory]
    data_quality_flags: List[str] = field(default_factory=list)
```

### 1.2 JSON Input Format (for file/API ingestion)

```json
{
  "screening_period": "2026-01",
  "screening_date": "2026-02-01",
  "screened_by": "Regulatory Intelligence Team",
  "topics_covered": ["ghg", "packaging", "water", "waste", "social_human_rights"],
  "regulations": [
    {
      "regulation_id": "EU-CSRD-2022",
      "title": "Corporate Sustainability Reporting Directive",
      "topic": "ghg",
      "description": "Requires detailed sustainability reporting including GHG emissions",
      "requirements_summary": "Large companies must report Scope 1, 2, and 3 emissions",
      "current_status": "law_passed",
      "effective_date": "2024-01-01",
      "enforcement_date": "2025-01-01",
      "geographic_scope": "regional",
      "applicable_countries": ["EU"],
      "version_date": "2026-02-01",
      "references": [
        {
          "source_name": "EUR-Lex",
          "source_url": "https://eur-lex.europa.eu/...",
          "document_id": "32022L2464"
        }
      ],
      "screening_source": "EUR-Lex Daily Feed"
    }
  ]
}
```

---

## 2. Change Detection Algorithm

### 2.1 Pseudocode

```
FUNCTION GenerateMonthlyChangelog(new_screening, previous_state):
    
    # 1. Build lookup from previous state
    prev_regulations = INDEX_BY(previous_state.regulations, "regulation_id")
    
    # 2. Initialize changelog
    changelog = NEW Changelog(screening_period=new_screening.screening_period)
    
    # 3. Process each regulation in new screening
    FOR EACH reg IN new_screening.regulations:
        prev_reg = prev_regulations.get(reg.regulation_id)
        
        IF prev_reg IS NULL:
            # NEW REGULATION - never seen before
            changelog.add_entry(CREATE_NEW_REGULATION_ENTRY(reg))
        ELSE:
            # EXISTING REGULATION - check for changes
            diff = COMPARE_REGULATIONS(prev_reg, reg)
            
            IF diff.has_changes():
                changelog.add_entry(CREATE_CHANGE_ENTRY(prev_reg, reg, diff))
            ELSE:
                # NO CHANGES - carry forward
                changelog.add_entry(CREATE_CARRY_FORWARD_ENTRY(prev_reg, reg))
        
        # Mark as processed
        prev_regulations[reg.regulation_id].processed = TRUE
    
    # 4. Check for removed/expired regulations
    FOR EACH prev_reg IN prev_regulations WHERE NOT processed:
        IF prev_reg.current_status NOT IN [expired, repealed]:
            # Regulation no longer in screening - may be expired
            changelog.add_entry(CREATE_REMOVAL_ENTRY(prev_reg))
    
    # 5. Generate summary statistics
    changelog.summary = GENERATE_SUMMARY(changelog.entries)
    
    RETURN changelog


FUNCTION COMPARE_REGULATIONS(old_reg, new_reg):
    diff = NEW RegulationDiff()
    
    # Core fields to compare
    IF old_reg.current_status != new_reg.current_status:
        diff.add_change("status", old_reg.current_status, new_reg.current_status)
    
    IF old_reg.title != new_reg.title:
        diff.add_change("title", old_reg.title, new_reg.title)
    
    IF old_reg.description != new_reg.description:
        diff.add_change("description", CONTENT_DIFF(old_reg.description, new_reg.description))
    
    IF old_reg.requirements_summary != new_reg.requirements_summary:
        diff.add_change("requirements", CONTENT_DIFF(old_reg.requirements_summary, new_reg.requirements_summary))
    
    IF old_reg.effective_date != new_reg.effective_date:
        diff.add_change("effective_date", old_reg.effective_date, new_reg.effective_date)
    
    IF old_reg.enforcement_date != new_reg.enforcement_date:
        diff.add_change("enforcement_date", old_reg.enforcement_date, new_reg.enforcement_date)
    
    IF old_reg.applicable_countries != new_reg.applicable_countries:
        diff.add_change("geographic_scope", old_reg.applicable_countries, new_reg.applicable_countries)
    
    IF old_reg.review_deadline != new_reg.review_deadline:
        diff.add_change("review_deadline", old_reg.review_deadline, new_reg.review_deadline)
    
    # Track version history
    diff.previous_version_date = old_reg.version_date
    diff.current_version_date = new_reg.version_date
    
    RETURN diff
```

### 2.2 Change Classification Logic

```
CLASSIFY_CHANGE(diff):
    
    changes = diff.changes.keys()
    
    # Priority 1: Status transitions
    IF "status" IN changes:
        status_transition = (diff.old_status, diff.new_status)
        
        IF status_transition == (proposed, law_passed):
            RETURN ChangeType.STATUS_PROMOTED_TO_LAW
        
        ELSE IF status_transition IN [
            (change_under_discussion, amendment_in_progress),
            (proposed, amendment_in_progress)
        ]:
            RETURN ChangeType.STATUS_ADVANCING
        
        ELSE IF status_transition == (law_passed, amendment_in_progress):
            RETURN ChangeType.LAW_BEING_AMENDED
        
        ELSE IF status_transition == (law_passed, expired):
            RETURN ChangeType.LAW_EXPIRED
        
        ELSE IF diff.new_status == expired OR diff.new_status == repealed:
            RETURN ChangeType.REGULATION_ENDED
    
    # Priority 2: Critical date changes
    IF "enforcement_date" IN changes OR "effective_date" IN changes:
        RETURN ChangeType.TIMELINE_UPDATED
    
    # Priority 3: Content changes
    IF "requirements" IN changes OR "description" IN changes:
        RETURN ChangeType.CONTENT_UPDATED
    
    # Priority 4: Minor changes
    IF "title" IN changes OR "geographic_scope" IN changes:
        RETURN ChangeType.METADATA_UPDATED
    
    RETURN ChangeType.NO_CHANGE
```

---

## 3. Output Format - Monthly Changelog Structure

### 3.1 Changelog Data Model

```python
from enum import Enum, auto
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import date

class ChangeType(Enum):
    # New regulations
    NEW_REGULATION = "new_regulation"
    
    # Status progression
    STATUS_PROMOTED_TO_LAW = "status_promoted_to_law"
    STATUS_ADVANCING = "status_advancing"
    LAW_BEING_AMENDED = "law_being_amended"
    
    # Updates
    TIMELINE_UPDATED = "timeline_updated"
    CONTENT_UPDATED = "content_updated"
    METADATA_UPDATED = "metadata_updated"
    
    # End of life
    LAW_EXPIRED = "law_expired"
    REGULATION_ENDED = "regulation_ended"
    REGULATION_REMOVED = "regulation_removed"
    
    # No change
    NO_CHANGE = "no_change"
    CARRIED_FORWARD = "carried_forward"

class ChangeSeverity(Enum):
    CRITICAL = "critical"      # New law passed, enforcement date changes
    HIGH = "high"              # Status advancement, content changes
    MEDIUM = "medium"          # Timeline updates
    LOW = "low"                # Metadata updates
    INFO = "info"              # Carried forward, no change

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
    # Identification
    regulation_id: str
    title: str
    topic: TopicCategory
    
    # Change classification
    change_type: ChangeType
    severity: ChangeSeverity
    
    # Detailed changes
    changes: List[ChangeDetail] = field(default_factory=list)
    
    # Current state snapshot
    current_status: RegulationStatus = RegulationStatus.PROPOSED
    effective_date: Optional[date] = None
    enforcement_date: Optional[date] = None
    geographic_scope: GeographicScope = GeographicScope.NATIONAL
    
    # Context
    previous_version_date: Optional[date] = None
    first_seen_period: str = ""  # When this regulation was first identified
    
    # Narrative
    summary: str = ""  # Human-readable summary of the change
    action_required: Optional[str] = None
    
    # Metadata
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
class MonthlyChangelog:
    """Complete monthly changelog output."""
    # Header
    screening_period: str
    generated_date: date
    previous_period: str
    
    # Categorized entries
    new_regulations: List[ChangelogEntry] = field(default_factory=list)
    status_changes: List[ChangelogEntry] = field(default_factory=list)
    content_updates: List[ChangelogEntry] = field(default_factory=list)
    timeline_changes: List[ChangelogEntry] = field(default_factory=list)
    metadata_updates: List[ChangelogEntry] = field(default_factory=list)
    ended_regulations: List[ChangelogEntry] = field(default_factory=list)
    carried_forward: List[ChangelogEntry] = field(default_factory=list)
    
    # Summaries
    topic_summaries: Dict[TopicCategory, TopicSummary] = field(default_factory=dict)
    critical_actions: List[ChangelogEntry] = field(default_factory=list)
    
    # Statistics
    total_regulations_tracked: int = 0
    total_changes_detected: int = 0
    
    # Narrative summary
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
```

### 3.2 JSON Output Format

```json
{
  "screening_period": "2026-02",
  "generated_date": "2026-02-01",
  "previous_period": "2026-01",
  "executive_summary": "5 new regulations identified, 3 status changes requiring attention...",
  
  "statistics": {
    "total_regulations_tracked": 47,
    "total_changes_detected": 12,
    "by_topic": {
      "ghg": { "new": 2, "changes": 3, "carried": 8 },
      "packaging": { "new": 1, "changes": 2, "carried": 5 },
      "water": { "new": 0, "changes": 1, "carried": 4 },
      "waste": { "new": 1, "changes": 1, "carried": 6 },
      "social_human_rights": { "new": 1, "changes": 5, "carried": 10 }
    }
  },
  
  "new_regulations": [
    {
      "regulation_id": "US-EPA-GHG-2026-001",
      "title": "New Power Plant GHG Standards",
      "topic": "ghg",
      "change_type": "new_regulation",
      "severity": "critical",
      "current_status": "proposed",
      "summary": "EPA proposed new performance standards for fossil fuel-fired power plants",
      "action_required": "Review applicability to company facilities",
      "changes": [
        {
          "field_name": "status",
          "old_value": null,
          "new_value": "proposed",
          "change_description": "First time identified in screening"
        }
      ]
    }
  ],
  
  "status_changes": [
    {
      "regulation_id": "EU-Packaging-Waste-2024",
      "title": "Packaging and Packaging Waste Regulation",
      "topic": "packaging",
      "change_type": "status_promoted_to_law",
      "severity": "critical",
      "current_status": "law_passed",
      "previous_status": "amendment_in_progress",
      "summary": "PPWR officially passed, enforcement begins 2025-08-18",
      "action_required": "Confirm compliance strategy for Q3 2025",
      "changes": [
        {
          "field_name": "status",
          "old_value": "amendment_in_progress",
          "new_value": "law_passed"
        },
        {
          "field_name": "enforcement_date",
          "old_value": null,
          "new_value": "2025-08-18"
        }
      ]
    }
  ],
  
  "critical_actions": [
    {
      "regulation_id": "EU-Packaging-Waste-2024",
      "severity": "critical",
      "action": "Confirm compliance strategy for Q3 2025",
      "deadline": "2025-08-18"
    }
  ]
}
```

### 3.3 Current handoff contract

The monthly changelog JSON should be treated as a handoff format, not the final report.

Current code expects a JSON object with top-level lists that can be flattened for:

- source proposal impact previews
- draft composition input
- evidence alignment

The draft composer reads changelog entries and evidence, then creates a new revision rather than rendering the changelog directly into PDF output.

---

## 4. Core Functions/Methods

### 4.1 Main Screening Module Interface

```python
from abc import ABC, abstractmethod
from typing import Protocol
import json
from pathlib import Path
from datetime import date
import difflib


class RegulationStore(Protocol):
    """Protocol for regulation persistence layer."""
    
    def get_previous_state(self, period: str) -> MonthlyScreeningInput:
        """Retrieve previous month's screening state."""
        ...
    
    def save_state(self, period: str, screening: MonthlyScreeningInput) -> None:
        """Save current screening as new state."""
        ...
    
    def get_regulation_history(self, regulation_id: str) -> List[MonthlyScreeningInput]:
        """Get full history for a specific regulation."""
        ...


class ScreeningSource(Protocol):
    """Protocol for data ingestion sources."""
    
    def fetch_screening_data(self, period: str) -> MonthlyScreeningInput:
        """Fetch screening data for a period."""
        ...


class RegulatoryScreeningModule:
    """
    Main module for monthly regulatory screening and changelog generation.
    """
    
    def __init__(
        self,
        store: RegulationStore,
        sources: List[ScreeningSource],
        config: Optional[Dict] = None
    ):
        self.store = store
        self.sources = sources
        self.config = config or {}
        self._severity_rules = self._init_severity_rules()
    
    # ==================== PUBLIC API ====================
    
    def run_monthly_screening(
        self,
        period: str,
        input_data: Optional[MonthlyScreeningInput] = None
    ) -> MonthlyChangelog:
        """
        Execute full monthly screening workflow.
        
        Args:
            period: Screening period (e.g., "2026-02")
            input_data: Optional pre-loaded screening data
        
        Returns:
            MonthlyChangelog with all detected changes
        """
        # Step 1: Get new screening data
        if input_data is None:
            new_screening = self._fetch_screening_data(period)
        else:
            new_screening = input_data
        
        # Step 2: Get previous state
        previous_period = self._get_previous_period(period)
        previous_state = self._get_previous_state(previous_period)
        
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
    
    def compare_regulations(
        self,
        old_reg: ScreeningInputItem,
        new_reg: ScreeningInputItem
    ) -> 'RegulationDiff':
        """
        Compare two regulation versions and return differences.
        """
        return self._compare_regulations_detailed(old_reg, new_reg)
    
    def classify_change(self, diff: 'RegulationDiff') -> ChangeType:
        """
        Classify the type of change based on detected differences.
        """
        return self._classify_change_type(diff)
    
    def generate_summary(self, changelog: MonthlyChangelog) -> str:
        """
        Generate human-readable executive summary.
        """
        return self._generate_executive_summary(changelog)
    
    def export_changelog(
        self,
        changelog: MonthlyChangelog,
        format: str = "json",
        output_path: Optional[Path] = None
    ) -> str:
        """
        Export changelog to various formats.
        
        Supported formats: json, markdown, pdf
        """
        exporters = {
            "json": self._export_json,
            "markdown": self._export_markdown,
            "pdf": self._export_pdf,
        }
        
        exporter = exporters.get(format, self._export_json)
        return exporter(changelog, output_path)
    
    # ==================== PRIVATE IMPLEMENTATION ====================
    
    def _fetch_screening_data(self, period: str) -> MonthlyScreeningInput:
        """Aggregate screening data from all configured sources."""
        all_regulations = []
        topics_covered = set()
        
        for source in self.sources:
            screening = source.fetch_screening_data(period)
            all_regulations.extend(screening.regulations)
            topics_covered.update(screening.topics_covered)
        
        # Deduplicate by regulation_id (keep highest confidence)
        regulations_by_id = {}
        for reg in all_regulations:
            if reg.regulation_id not in regulations_by_id:
                regulations_by_id[reg.regulation_id] = reg
            elif reg.confidence_score > regulations_by_id[reg.regulation_id].confidence_score:
                regulations_by_id[reg.regulation_id] = reg
        
        return MonthlyScreeningInput(
            screening_period=period,
            screening_date=date.today(),
            screened_by="Automated Screening System",
            regulations=list(regulations_by_id.values()),
            topics_covered=list(topics_covered)
        )
    
    def _get_previous_period(self, current_period: str) -> str:
        """Calculate previous month from YYYY-MM format."""
        year, month = map(int, current_period.split("-"))
        if month == 1:
            return f"{year - 1}-12"
        else:
            return f"{year}-{month - 1:02d}"
    
    def _get_previous_state(self, period: str) -> Optional[MonthlyScreeningInput]:
        """Retrieve previous state, return empty if none exists."""
        try:
            return self.store.get_previous_state(period)
        except FileNotFoundError:
            return None
    
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
        prev_by_id = {}
        first_seen_dates = {}
        
        if previous_state:
            for reg in previous_state.regulations:
                prev_by_id[reg.regulation_id] = reg
                first_seen_dates[reg.regulation_id] = previous_period
        
        processed_ids = set()
        
        # Process each new regulation
        for new_reg in new_screening.regulations:
            reg_id = new_reg.regulation_id
            processed_ids.add(reg_id)
            
            prev_reg = prev_by_id.get(reg_id)
            
            if prev_reg is None:
                # NEW REGULATION
                entry = self._create_new_regulation_entry(new_reg, new_screening.screening_period)
                changelog.new_regulations.append(entry)
                
            else:
                # EXISTING - check for changes
                diff = self._compare_regulations_detailed(prev_reg, new_reg)
                
                if diff.has_changes():
                    entry = self._create_change_entry(
                        prev_reg, new_reg, diff, first_seen_dates.get(reg_id, previous_period)
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
        changelog.total_changes_detected = len(changelog.all_entries()) - len(changelog.carried_forward)
        changelog.total_regulations_tracked = len(new_screening.regulations)
        
        return changelog
    
    def _compare_regulations_detailed(
        self,
        old: ScreeningInputItem,
        new: ScreeningInputItem
    ) -> 'RegulationDiff':
        """Detailed field-by-field comparison."""
        diff = RegulationDiff(
            regulation_id=old.regulation_id,
            previous_version_date=old.version_date,
            current_version_date=new.version_date
        )
        
        # Status change
        if old.current_status != new.current_status:
            diff.add_change(
                field="status",
                old=old.current_status,
                new=new.current_status,
                description=f"Status changed from {old.current_status.value} to {new.current_status.value}"
            )
        
        # Title change
        if old.title != new.title:
            diff.add_change(
                field="title",
                old=old.title,
                new=new.title,
                description="Title updated"
            )
        
        # Description change with content diff
        if old.description != new.description:
            content_diff = self._generate_text_diff(old.description, new.description)
            diff.add_change(
                field="description",
                old=old.description,
                new=new.description,
                description=content_diff
            )
        
        # Requirements change
        if old.requirements_summary != new.requirements_summary:
            content_diff = self._generate_text_diff(old.requirements_summary, new.requirements_summary)
            diff.add_change(
                field="requirements",
                old=old.requirements_summary,
                new=new.requirements_summary,
                description=content_diff
            )
        
        # Date changes
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
        
        # Geographic scope
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
    
    def _classify_change_type(self, diff: 'RegulationDiff') -> ChangeType:
        """Classify change based on priority rules."""
        changes = {c.field_name for c in diff.changes}
        
        # Check status changes first
        if "status" in changes:
            status_change = next(c for c in diff.changes if c.field_name == "status")
            old_status = status_change.old_value
            new_status = status_change.new_value
            
            # Promoted to law
            if new_status == RegulationStatus.LAW_PASSED:
                return ChangeType.STATUS_PROMOTED_TO_LAW
            
            # Ended regulations
            if new_status in (RegulationStatus.EXPIRED, RegulationStatus.REPEALED):
                if old_status == RegulationStatus.LAW_PASSED:
                    return ChangeType.LAW_EXPIRED
                return ChangeType.REGULATION_ENDED
            
            # Advancing through pipeline
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
        diff: Optional['RegulationDiff'] = None
    ) -> ChangeSeverity:
        """Calculate severity based on change type and content."""
        # Critical: New laws, enforcement date changes for existing laws
        if entry.change_type == ChangeType.STATUS_PROMOTED_TO_LAW:
            return ChangeSeverity.CRITICAL
        
        if entry.change_type == ChangeType.LAW_EXPIRED:
            return ChangeSeverity.CRITICAL
        
        if entry.change_type == ChangeType.TIMELINE_UPDATED:
            if diff and any(c.field_name == "enforcement_date" for c in diff.changes):
                return ChangeSeverity.CRITICAL
        
        # High: Status advancement, content changes
        if entry.change_type in (ChangeType.STATUS_ADVANCING, ChangeType.LAW_BEING_AMENDED):
            return ChangeSeverity.HIGH
        
        if entry.change_type == ChangeType.CONTENT_UPDATED:
            return ChangeSeverity.HIGH
        
        # Medium: Other timeline changes
        if entry.change_type == ChangeType.TIMELINE_UPDATED:
            return ChangeSeverity.MEDIUM
        
        # Low: Metadata
        if entry.change_type == ChangeType.METADATA_UPDATED:
            return ChangeSeverity.LOW
        
        # Info: New regulations (to be reviewed), no change
        if entry.change_type == ChangeType.NEW_REGULATION:
            return ChangeSeverity.INFO
        
        return ChangeSeverity.INFO
    
    def _create_new_regulation_entry(
        self,
        reg: ScreeningInputItem,
        first_seen_period: str
    ) -> ChangelogEntry:
        """Create entry for newly identified regulation."""
        return ChangelogEntry(
            regulation_id=reg.regulation_id,
            title=reg.title,
            topic=reg.topic,
            change_type=ChangeType.NEW_REGULATION,
            severity=ChangeSeverity.INFO,
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
    
    def _create_change_entry(
        self,
        old: ScreeningInputItem,
        new: ScreeningInputItem,
        diff: 'RegulationDiff',
        first_seen_period: str
    ) -> ChangelogEntry:
        """Create entry for changed regulation."""
        change_type = self._classify_change_type(diff)
        
        entry = ChangelogEntry(
            regulation_id=new.regulation_id,
            title=new.title,
            topic=new.topic,
            change_type=change_type,
            severity=ChangeSeverity.INFO,  # Will be updated
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
        """Create entry for unchanged regulation (carried forward)."""
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
            summary=f"Regulation no longer tracked - may be expired or repealed",
            action_required="Verify status with regulatory source"
        )
    
    def _categorize_entry(
        self,
        changelog: MonthlyChangelog,
        entry: ChangelogEntry
    ) -> None:
        """Route entry to appropriate list based on change type."""
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
        
        # Track critical items
        if entry.severity in (ChangeSeverity.CRITICAL, ChangeSeverity.HIGH):
            changelog.critical_actions.append(entry)
    
    def _post_process_changelog(self, changelog: MonthlyChangelog) -> MonthlyChangelog:
        """Final processing: sort, summarize, validate."""
        # Sort all lists by severity then topic
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
        
        # Generate topic summaries
        changelog.topic_summaries = self._generate_topic_summaries(changelog)
        
        # Generate executive summary
        changelog.executive_summary = self._generate_executive_summary(changelog)
        
        return changelog
    
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
        parts = []
        
        # Header
        parts.append(
            f"Regulatory Screening Report for {changelog.screening_period}\n"
        )
        
        # Key metrics
        critical_count = len(changelog.critical_actions)
        new_count = len(changelog.new_regulations)
        change_count = changelog.total_changes_detected
        
        parts.append(
            f"• {changelog.total_regulations_tracked} regulations tracked\n"
            f"• {new_count} new regulations identified\n"
            f"• {change_count} changes detected ({critical_count} critical)\n"
        )
        
        # Critical items highlight
        if changelog.critical_actions:
            parts.append("\nCRITICAL ACTIONS REQUIRED:\n")
            for entry in changelog.critical_actions[:5]:  # Top 5
                parts.append(
                    f"  - {entry.regulation_id}: {entry.title}\n"
                    f"    Action: {entry.action_required}\n"
                )
        
        # Topic highlights
        parts.append("\nBY TOPIC:\n")
        for topic, summary in changelog.topic_summaries.items():
            if summary.new_regulations or summary.status_changes:
                parts.append(
                    f"  {topic.value}: {summary.new_regulations} new, "
                    f"{summary.status_changes} status changes\n"
                )
        
        return "".join(parts)
    
    # ==================== HELPER METHODS ====================
    
    def _generate_text_diff(self, old_text: str, new_text: str) -> str:
        """Generate unified diff of text changes."""
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile="previous",
            tofile="current",
            lineterm=""
        )
        
        return "\n".join(diff)
    
    def _generate_change_summary(
        self,
        entry: ChangelogEntry,
        diff: 'RegulationDiff'
    ) -> str:
        """Generate human-readable change summary."""
        summaries = []
        
        for change in entry.changes:
            if change.field_name == "status":
                old_val = change.old_value.value if change.old_value else "unknown"
                new_val = change.new_value.value if change.new_value else "unknown"
                summaries.append(f"Status: {old_val} → {new_val}")
            
            elif change.field_name == "enforcement_date":
                summaries.append(f"Enforcement date updated to {change.new_value}")
            
            elif change.field_name == "requirements":
                summaries.append("Requirements updated")
        
        return "; ".join(summaries) if summaries else "Changes detected"
    
    def _suggest_action_for_new(self, reg: ScreeningInputItem) -> Optional[str]:
        """Suggest initial action for new regulation."""
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
        diff: 'RegulationDiff'
    ) -> Optional[str]:
        """Suggest action based on change type."""
        if entry.change_type == ChangeType.STATUS_PROMOTED_TO_LAW:
            return "Confirm compliance strategy and implementation timeline"
        
        if entry.change_type == ChangeType.LAW_EXPIRED:
            return "Verify if replaced by new regulation; archive if truly ended"
        
        if entry.change_type == ChangeType.TIMELINE_UPDATED:
            date_change = next(
                (c for c in diff.changes if c.field_name == "enforcement_date"),
                None
            )
            if date_change:
                return f"Update compliance calendar: new enforcement date {date_change.new_value}"
        
        if entry.change_type == ChangeType.CONTENT_UPDATED:
            return "Review updated requirements for compliance impact"
        
        return None
    
    def _init_severity_rules(self) -> Dict:
        """Initialize severity calculation rules."""
        return {
            "critical_status_transitions": [
                (None, RegulationStatus.LAW_PASSED),
                (RegulationStatus.LAW_PASSED, RegulationStatus.EXPIRED),
            ],
            "high_status_transitions": [
                (RegulationStatus.CHANGE_UNDER_DISCUSSION, RegulationStatus.AMENDMENT_IN_PROGRESS),
                (RegulationStatus.AMENDMENT_IN_PROGRESS, RegulationStatus.LAW_PASSED),
                (RegulationStatus.LAW_PASSED, RegulationStatus.AMENDMENT_IN_PROGRESS),
            ]
        }
    
    # ==================== EXPORT METHODS ====================
    
    def _export_json(
        self,
        changelog: MonthlyChangelog,
        output_path: Optional[Path] = None
    ) -> str:
        """Export to JSON format."""
        data = {
            "screening_period": changelog.screening_period,
            "generated_date": changelog.generated_date.isoformat(),
            "previous_period": changelog.previous_period,
            "executive_summary": changelog.executive_summary,
            "statistics": {
                "total_regulations_tracked": changelog.total_regulations_tracked,
                "total_changes_detected": changelog.total_changes_detected,
            },
            "entries": self._entries_to_dict(changelog)
        }
        
        json_str = json.dumps(data, indent=2, default=str)
        
        if output_path:
            output_path.write_text(json_str)
        
        return json_str
    
    def _entries_to_dict(self, changelog: MonthlyChangelog) -> Dict:
        """Convert entries to dictionary structure."""
        return {
            "new_regulations": [self._entry_to_dict(e) for e in changelog.new_regulations],
            "status_changes": [self._entry_to_dict(e) for e in changelog.status_changes],
            "content_updates": [self._entry_to_dict(e) for e in changelog.content_updates],
            "timeline_changes": [self._entry_to_dict(e) for e in changelog.timeline_changes],
            "metadata_updates": [self._entry_to_dict(e) for e in changelog.metadata_updates],
            "ended_regulations": [self._entry_to_dict(e) for e in changelog.ended_regulations],
            "carried_forward": [self._entry_to_dict(e) for e in changelog.carried_forward],
        }
    
    def _entry_to_dict(self, entry: ChangelogEntry) -> Dict:
        """Convert single entry to dictionary."""
        return {
            "regulation_id": entry.regulation_id,
            "title": entry.title,
            "topic": entry.topic.value,
            "change_type": entry.change_type.value,
            "severity": entry.severity.value,
            "summary": entry.summary,
            "action_required": entry.action_required,
            "current_status": entry.current_status.value,
            "changes": [
                {
                    "field": c.field_name,
                    "old": str(c.old_value) if c.old_value else None,
                    "new": str(c.new_value) if c.new_value else None,
                }
                for c in entry.changes
            ]
        }
    
    def _export_markdown(
        self,
        changelog: MonthlyChangelog,
        output_path: Optional[Path] = None
    ) -> str:
        """Export to Markdown format."""
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
        
        # Add sections for each change type
        if changelog.new_regulations:
            lines.extend(["## New Regulations", ""])
            for entry in changelog.new_regulations:
                lines.extend([
                    f"### {entry.regulation_id}: {entry.title}",
                    f"- **Topic:** {entry.topic.value}",
                    f"- **Status:** {entry.current_status.value}",
                    f"- **Summary:** {entry.summary}",
                    ""
                ])
        
        if changelog.critical_actions:
            lines.extend(["## Critical Actions Required", ""])
            for entry in changelog.critical_actions:
                lines.extend([
                    f"- **{entry.regulation_id}**: {entry.action_required}",
                    ""
                ])
        
        md = "\n".join(lines)
        
        if output_path:
            output_path.write_text(md)
        
        return md
    
    def _export_pdf(
        self,
        changelog: MonthlyChangelog,
        output_path: Optional[Path] = None
    ) -> str:
        """Export to PDF format (placeholder - would use reportlab/weasyprint)."""
        # This would generate a PDF using a library like reportlab or weasyprint
        # For now, return markdown as intermediate format
        return self._export_markdown(changelog, output_path)


# ==================== SUPPORTING CLASSES ====================

@dataclass
class RegulationDiff:
    """Internal class for tracking regulation differences."""
    regulation_id: str = ""
    previous_version_date: Optional[date] = None
    current_version_date: Optional[date] = None
    changes: List['FieldChange'] = field(default_factory=list)
    
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


@dataclass
class FieldChange:
    field_name: str
    old_value: Any
    new_value: Any
    description: Optional[str] = None
```

### 4.2 Integration with MARS draft composition

The screening workflow feeds the current draft-first layer indirectly:

- `drafts/{draft_id}/compose` reads changelog entries from `REGULATORY_DATA_DIR/{client_id}/changelogs`.
- Evidence files under `REGULATORY_DATA_DIR/{client_id}/evidence` can be passed into draft composition.
- `source-proposals/suggest` and `source-proposals/{id}/impact` use the changelog artifact to estimate source coverage.
- `keywords/preview` is a separate client-scoped helper for testing terms against sample text.
- `exports/import-docx` turns a reviewed DOCX into a new draft revision checkpoint.

---

## 5. Edge Case Handling

### 5.1 New Regulations (Never Seen Before)

```python
def handle_new_regulation(
    self,
    reg: ScreeningInputItem,
    current_period: str
) -> ChangelogEntry:
    """
    - Always creates NEW_REGULATION entry
    - Sets first_seen_period to current period
    - Severity = INFO (requires review, not urgent by default)
    - Suggests initial assessment action based on status
    - Adds to tracking store for future comparison
    """
    entry = ChangelogEntry(
        change_type=ChangeType.NEW_REGULATION,
        severity=ChangeSeverity.INFO,
        first_seen_period=current_period,
        action_required=self._suggest_action_for_new(reg)
    )
    
    # CRITICAL override: If immediately a passed law with near enforcement
    if reg.current_status == RegulationStatus.LAW_PASSED and \
       reg.enforcement_date and \
       (reg.enforcement_date - date.today()).days < 90:
        entry.severity = ChangeSeverity.CRITICAL
        entry.action_required = "URGENT: Law passed with imminent enforcement date"
    
    return entry
```

### 5.2 Status Changes

```python
def handle_status_change(
    self,
    old_status: RegulationStatus,
    new_status: RegulationStatus,
    reg: ScreeningInputItem
) -> Tuple[ChangeType, ChangeSeverity, str]:
    """
    Status Transition Matrix:
    
    FROM → TO                     | ChangeType              | Severity
    ------------------------------|-------------------------|----------
    any → LAW_PASSED              | STATUS_PROMOTED_TO_LAW  | CRITICAL
    LAW_PASSED → EXPIRED          | LAW_EXPIRED             | CRITICAL
    PROPOSED → AMENDMENT_IN_PROG  | STATUS_ADVANCING        | HIGH
    DISCUSSION → AMENDMENT_IN_PROG| STATUS_ADVANCING        | HIGH
    LAW_PASSED → AMENDMENT_IN_PROG| LAW_BEING_AMENDED       | HIGH
    any → EXPIRED/REPEALED        | REGULATION_ENDED        | HIGH
    """
    
    transition = (old_status, new_status)
    
    # Define transition rules
    rules = {
        (None, RegulationStatus.LAW_PASSED): (
            ChangeType.STATUS_PROMOTED_TO_LAW, ChangeSeverity.CRITICAL
        ),
        (RegulationStatus.AMENDMENT_IN_PROGRESS, RegulationStatus.LAW_PASSED): (
            ChangeType.STATUS_PROMOTED_TO_LAW, ChangeSeverity.CRITICAL
        ),
        (RegulationStatus.CHANGE_UNDER_DISCUSSION, RegulationStatus.AMENDMENT_IN_PROGRESS): (
            ChangeType.STATUS_ADVANCING, ChangeSeverity.HIGH
        ),
        (RegulationStatus.LAW_PASSED, RegulationStatus.EXPIRED): (
            ChangeType.LAW_EXPIRED, ChangeSeverity.CRITICAL
        ),
    }
    
    change_type, severity = rules.get(
        transition,
        (ChangeType.STATUS_ADVANCING, ChangeSeverity.MEDIUM)
    )
    
    # Generate appropriate summary
    summary = f"Status changed: {old_status.value} → {new_status.value}"
    
    return change_type, severity, summary
```

### 5.3 No Changes (Carry Forward)

```python
def handle_no_change(
    self,
    reg: ScreeningInputItem,
    first_seen_period: str,
    periods_since_change: int
) -> ChangelogEntry:
    """
    - Creates CARRIED_FORWARD entry
    - Severity = INFO
    - Tracks age since last change
    - Special handling for aging items:
      - If AMENDMENT_IN_PROGRESS for >6 months: flag for review
      - If PROPOSED for >12 months: may be stale
    """
    entry = ChangelogEntry(
        change_type=ChangeType.CARRIED_FORWARD,
        severity=ChangeSeverity.INFO,
        first_seen_period=first_seen_period,
        summary=f"No changes (tracking since {first_seen_period})"
    )
    
    # Flag long-pending items
    if reg.current_status == RegulationStatus.AMENDMENT_IN_PROGRESS and \
       periods_since_change > 6:
        entry.summary += " [Note: Amendment in progress for >6 months]"
    
    return entry
```

### 5.4 Expired/Removed Regulations

```python
def handle_removal(
    self,
    reg: ScreeningInputItem,
    last_period: str
) -> ChangelogEntry:
    """
    Scenarios:
    1. Regulation truly repealed/expired
    2. Regulation moved out of scope (no longer applicable to topics)
    3. Data error (should have been in new screening)
    
    Handling:
    - Create REGULATION_REMOVED entry
    - Severity = HIGH (requires verification)
    - Do NOT automatically mark as EXPIRED
    - Suggest verification action
    - Keep in tracking for 2 more periods (grace period)
    """
    entry = ChangelogEntry(
        change_type=ChangeType.REGULATION_REMOVED,
        severity=ChangeSeverity.HIGH,
        summary=f"Regulation not found in {last_period} screening",
        action_required="Verify status: check if expired, repealed, or screening gap"
    )
    
    # Soft delete - keep in state with removed flag
    # Actual removal happens after 2-period grace period
    
    return entry


def cleanup_expired_tracking(
    self,
    state: MonthlyScreeningInput,
    grace_periods: int = 2
) -> MonthlyScreeningInput:
    """
    After grace period, truly remove regulations that:
    - Have been marked removed for > grace_periods
    - Are confirmed EXPIRED or REPEALED
    - Have replacement regulation identified
    """
    # Implementation would track removal count per regulation
    pass
```

---

## 6. Data Store Implementation

```python
import json
from pathlib import Path
from typing import Dict, List, Optional


class FileSystemRegulationStore:
    """Simple file-based storage for regulation states."""
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories
        self.states_path = self.base_path / "states"
        self.changelogs_path = self.base_path / "changelogs"
        self.history_path = self.base_path / "history"
        
        for p in [self.states_path, self.changelogs_path, self.history_path]:
            p.mkdir(exist_ok=True)
    
    def get_previous_state(self, period: str) -> MonthlyScreeningInput:
        """Load screening state for a period."""
        file_path = self.states_path / f"{period}.json"
        
        if not file_path.exists():
            raise FileNotFoundError(f"No state found for period: {period}")
        
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
        # Serialize and save
        pass
    
    def get_regulation_history(self, regulation_id: str) -> List[Dict]:
        """Get historical snapshots for a regulation."""
        history_file = self.history_path / f"{regulation_id}.jsonl"
        
        if not history_file.exists():
            return []
        
        entries = []
        for line in history_file.read_text().strip().split("\n"):
            entries.append(json.loads(line))
        
        return entries
    
    def append_to_history(
        self,
        regulation_id: str,
        entry: Dict
    ) -> None:
        """Append entry to regulation's history log."""
        history_file = self.history_path / f"{regulation_id}.jsonl"
        
        with open(history_file, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    
    def _serialize_screening(self, screening: MonthlyScreeningInput) -> Dict:
        """Convert ScreeningInputItem to JSON-serializable dict."""
        return {
            "screening_period": screening.screening_period,
            "screening_date": screening.screening_date.isoformat(),
            "screened_by": screening.screened_by,
            "topics_covered": [t.value for t in screening.topics_covered],
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
        # Implementation omitted for brevity
        pass
```

---

## 7. Usage Example

```python
def main():
    """Example workflow execution."""
    
    # Initialize storage
    store = FileSystemRegulationStore(Path("./regulatory_data"))
    
    # Initialize screening module
    screening_module = RegulatoryScreeningModule(
        store=store,
        sources=[],  # Add API sources here
        config={
            "critical_enforcement_window_days": 90,
            "long_pending_warning_months": 6,
            "removal_grace_periods": 2,
        }
    )
    
    # Create sample input (normally from APIs/files)
    january_input = MonthlyScreeningInput(
        screening_period="2026-01",
        screening_date=date(2026, 1, 31),
        screened_by="Automated System",
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
            )
        ],
        topics_covered=list(TopicCategory)
    )
    
    # Run January screening
    jan_changelog = screening_module.run_monthly_screening(
        period="2026-01",
        input_data=january_input
    )
    
    # Export results
    screening_module.export_changelog(
        jan_changelog,
        format="markdown",
        output_path=Path("./reports/2026-01_changelog.md")
    )
    
    # February - new screening detects status change
    february_input = MonthlyScreeningInput(
        screening_period="2026-02",
        screening_date=date(2026, 2, 28),
        screened_by="Automated System",
        regulations=[
            ScreeningInputItem(
                regulation_id="EU-CSRD-2022",
                title="Corporate Sustainability Reporting Directive",
                topic=TopicCategory.GHG,
                description="Comprehensive sustainability reporting requirements",
                requirements_summary="Report Scope 1, 2, 3 emissions",
                current_status=RegulationStatus.LAW_PASSED,  # CHANGED!
                enforcement_date=date(2025, 1, 1),
                geographic_scope=GeographicScope.REGIONAL,
                applicable_countries=["EU"],
            ),
            ScreeningInputItem(
                regulation_id="US-EPA-GHG-2026-001",  # NEW!
                title="New Power Plant GHG Standards",
                topic=TopicCategory.GHG,
                description="EPA proposed new standards",
                requirements_summary="New performance standards",
                current_status=RegulationStatus.PROPOSED,
                geographic_scope=GeographicScope.NATIONAL,
                applicable_countries=["US"],
            )
        ],
        topics_covered=list(TopicCategory)
    )
    
    # Run February screening - will detect changes
    feb_changelog = screening_module.run_monthly_screening(
        period="2026-02",
        input_data=february_input
    )
    
    # Output:
    # - EU-CSRD: STATUS_PROMOTED_TO_LAW (CRITICAL)
    # - US-EPA-GHG: NEW_REGULATION (INFO)
    
    print(feb_changelog.executive_summary)


if __name__ == "__main__":
    main()
```

---

## Summary

This workflow provides:

1. **Structured Input**: JSON/dataclass format for monthly screening data with full metadata
2. **Robust Change Detection**: Field-by-field comparison with intelligent classification
3. **Rich Output**: Categorized changelog with severity levels and action recommendations
4. **MARS Handoff**: A stable monthly artifact that can feed draft composition, source impact previews, and DOCX revision checkpoints
5. **Complete Implementation**: Ready-to-use Python classes with all core functions
6. **Edge Case Handling**: Specific logic for new, changed, unchanged, and removed regulations
