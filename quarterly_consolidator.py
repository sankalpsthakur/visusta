#!/usr/bin/env python3
"""
VISUSTA — Quarterly Regulatory Consolidation Module

This module provides functionality to aggregate, validate, and consolidate
3 months of regulatory change logs into a strategic quarterly view suitable
for PDF generation via ReportLab.

Key Design Principles:
1. Structured data models for change tracking
2. Validation logic for change quality/confidence
3. Conflict resolution for multi-month data
4. Narrative synthesis for executive reporting
5. Direct integration with existing PDF build pipeline
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from enum import Enum, auto
from typing import Optional, List, Dict, Any, Callable, Set, Tuple
from collections import defaultdict
from pathlib import Path

from config import get_config


# ═════════════════════════════════════════════════════════════════════════════
# ENUMERATIONS & CONSTANTS
# ═════════════════════════════════════════════════════════════════════════════

class ChangeStatus(Enum):
    """Lifecycle status of a regulatory change entry."""
    DRAFT = auto()           # Initial capture, unverified
    PENDING = auto()         # Awaiting confirmation
    VALIDATED = auto()       # Confirmed by reliable source
    SUPERSEDED = auto()      # Replaced by newer information
    RETRACTED = auto()       # Found to be incorrect


class ImpactLevel(Enum):
    """Business impact classification."""
    CRITICAL = "CRITICAL"    # Immediate action required
    HIGH = "HIGH"            # Significant operational impact
    MEDIUM = "MEDIUM"        # Moderate impact, plan accordingly
    LOW = "LOW"              # Minor impact, monitor
    NONE = "NONE"            # Informational only


class RegulationScope(Enum):
    """Geographic/jurisdictional scope."""
    EU = "EU"                # European Union level
    GERMANY = "DE"           # German federal level
    STATE = "STATE"          # German state level (e.g., NRW, Hamburg)
    LOCAL = "LOCAL"          # Municipal level
    INTERNATIONAL = "INT"    # Beyond EU


class InvestmentType(Enum):
    """Type of investment required for compliance."""
    CAPEX = "CAPEX"          # Capital expenditure
    OPEX = "OPEX"            # Operational expenditure
    RND = "R&D"              # Research and development
    AUDIT = "Audit"          # Compliance auditing
    IT = "IT Integration"    # Systems integration
    NONE = "None"            # No investment required


# Validation thresholds — sourced from config/visusta.yaml
_cfg = get_config()
VALIDATION_MIN_SOURCES     = _cfg.validation.min_sources
VALIDATION_MAX_AGE_DAYS    = _cfg.validation.max_age_days
CONFIDENCE_HIGH_THRESHOLD  = 0.8   # internal scoring constant, not user-configurable
CONFIDENCE_MEDIUM_THRESHOLD = _cfg.validation.confidence_threshold
_RELIABILITY_THRESHOLD      = _cfg.validation.reliability_threshold
_MIN_DESCRIPTION_LENGTH     = _cfg.validation.min_description_length


# ═════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class SourceReference:
    """Reference to a regulatory information source."""
    id: str
    title: str
    url: Optional[str] = None
    publisher: Optional[str] = None
    publish_date: Optional[date] = None
    access_date: date = field(default_factory=date.today)
    reliability_score: float = 0.8  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "publisher": self.publisher,
            "publish_date": self.publish_date.isoformat() if self.publish_date else None,
            "access_date": self.access_date.isoformat(),
            "reliability_score": self.reliability_score
        }


@dataclass
class TimelineMilestone:
    """A specific milestone in a regulation's timeline."""
    date: date
    description: str
    milestone_type: str  # e.g., "effective", "deadline", "draft", "transposition"
    confirmed: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "description": self.description,
            "milestone_type": self.milestone_type,
            "confirmed": self.confirmed
        }


@dataclass
class ChangeLogEntry:
    """
    Single regulatory change entry from monthly tracking.
    
    This is the atomic unit of the consolidation workflow.
    Each entry represents one discrete change observation.
    """
    # Identification
    id: str
    regulation_code: str  # e.g., "PPWR", "EUDR", "VerpackDG"
    regulation_name: str
    
    # Temporal
    reported_month: date  # Year-month this was reported (e.g., 2026-01-01 for Jan 2026)
    change_date: date     # When the change occurred/takes effect
    
    # Content
    title: str
    description: str
    change_type: str  # e.g., "amendment", "guidance", "deadline_change", "new_regulation"
    
    # Classification
    scope: RegulationScope
    impact_level: ImpactLevel
    affected_areas: List[str]  # e.g., ["Packaging", "Supply Chain", "Reporting"]
    investment_type: InvestmentType = InvestmentType.NONE
    
    # Status & Validation
    status: ChangeStatus = ChangeStatus.DRAFT
    sources: List[SourceReference] = field(default_factory=list)
    related_entries: List[str] = field(default_factory=list)  # IDs of related changes
    
    # Timeline (for multi-phase regulations)
    milestones: List[TimelineMilestone] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    validated_by: Optional[str] = None
    validation_notes: Optional[str] = None
    
    # Narrative content for reporting
    executive_summary: Optional[str] = None
    action_items: List[str] = field(default_factory=list)
    
    def calculate_confidence_score(self) -> float:
        """
        Calculate confidence score based on validation criteria.
        
        Returns a value between 0.0 and 1.0 representing the
        reliability of this change entry.
        """
        scores = []
        
        # Source reliability (weighted heavily)
        if self.sources:
            avg_source_reliability = sum(s.reliability_score for s in self.sources) / len(self.sources)
            source_count_bonus = min(len(self.sources) / VALIDATION_MIN_SOURCES, 1.0)
            scores.append(avg_source_reliability * source_count_bonus)
        else:
            scores.append(0.0)
        
        # Status factor
        status_scores = {
            ChangeStatus.VALIDATED: 1.0,
            ChangeStatus.PENDING: 0.6,
            ChangeStatus.DRAFT: 0.3,
            ChangeStatus.SUPERSEDED: 0.2,
            ChangeStatus.RETRACTED: 0.0
        }
        scores.append(status_scores.get(self.status, 0.3))
        
        # Age factor (newer is better for regulatory info)
        age_days = (date.today() - self.change_date).days
        age_factor = max(0, 1 - (age_days / VALIDATION_MAX_AGE_DAYS))
        scores.append(age_factor)
        
        # Weighted average
        weights = [0.5, 0.3, 0.2]
        confidence = sum(s * w for s, w in zip(scores, weights))
        return round(confidence, 2)
    
    def is_validated(self) -> bool:
        """Check if this entry passes validation criteria."""
        return (
            self.status == ChangeStatus.VALIDATED
            and len(self.sources) >= VALIDATION_MIN_SOURCES
            and self.calculate_confidence_score() >= CONFIDENCE_MEDIUM_THRESHOLD
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "regulation_code": self.regulation_code,
            "regulation_name": self.regulation_name,
            "reported_month": self.reported_month.isoformat(),
            "change_date": self.change_date.isoformat(),
            "title": self.title,
            "description": self.description,
            "change_type": self.change_type,
            "scope": self.scope.value,
            "impact_level": self.impact_level.value,
            "affected_areas": self.affected_areas,
            "investment_type": self.investment_type.value,
            "status": self.status.name,
            "sources": [s.to_dict() for s in self.sources],
            "related_entries": self.related_entries,
            "milestones": [m.to_dict() for m in self.milestones],
            "confidence_score": self.calculate_confidence_score(),
            "executive_summary": self.executive_summary,
            "action_items": self.action_items
        }


@dataclass
class ConsolidatedRegulation:
    """
    Aggregated view of a regulation across the quarter.
    
    This represents the output of the consolidation process,
    providing a unified narrative for a single regulation.
    """
    regulation_code: str
    regulation_name: str
    scope: RegulationScope
    
    # Aggregation results
    impact_level: ImpactLevel
    latest_status: str
    primary_deadline: Optional[date] = None
    
    # Consolidated narrative
    executive_summary: str = ""
    strategic_implications: str = ""
    key_developments: List[str] = field(default_factory=list)
    
    # Actionable items
    recommended_actions: List[Dict[str, Any]] = field(default_factory=list)
    investment_requirements: List[Dict[str, Any]] = field(default_factory=list)
    
    # Source data
    source_entries: List[str] = field(default_factory=list)  # IDs of consolidated entries
    month_coverage: Set[str] = field(default_factory=set)  # Which months contributed
    
    # Metadata
    first_observed: Optional[date] = None
    last_updated: Optional[date] = None
    confidence_trend: str = "stable"  # "improving", "stable", "declining"
    
    def to_pdf_content(self) -> Dict[str, Any]:
        """
        Convert to dictionary format suitable for PDF generation.
        
        Returns a structure compatible with the existing ReportLab
        build pipeline in build_quarterly_brief.py.
        """
        return {
            "regulation_code": self.regulation_code,
            "regulation_name": self.regulation_name,
            "scope": self.scope.value,
            "impact_level": self.impact_level.value,
            "status": self.latest_status,
            "primary_deadline": self.primary_deadline.isoformat() if self.primary_deadline else None,
            "executive_summary": self.executive_summary,
            "strategic_implications": self.strategic_implications,
            "key_developments": self.key_developments,
            "recommended_actions": self.recommended_actions,
            "investment_requirements": self.investment_requirements,
            "month_coverage": sorted(list(self.month_coverage)),
            "confidence_trend": self.confidence_trend
        }


@dataclass
class QuarterlySummary:
    """
    Complete quarterly consolidation output.
    
    This is the final output of the consolidation workflow,
    ready for PDF generation or further processing.
    """
    quarter: str  # e.g., "Q1 2026"
    reporting_period: str  # e.g., "January - March 2026"
    generated_at: datetime = field(default_factory=datetime.now)
    
    # Consolidated regulations
    regulations: List[ConsolidatedRegulation] = field(default_factory=list)
    
    # Cross-cutting analysis
    themes: List[Dict[str, Any]] = field(default_factory=list)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    resource_implications: Dict[str, Any] = field(default_factory=dict)
    
    # Statistics
    stats: Dict[str, Any] = field(default_factory=dict)
    
    def to_pdf_format(self) -> Dict[str, Any]:
        """
        Export to format optimized for ReportLab PDF generation.
        
        Structure mirrors the content sections in build_quarterly_brief.py
        """
        return {
            "quarter": self.quarter,
            "reporting_period": self.reporting_period,
            "executive_summary": self._generate_executive_summary(),
            "priority_matrix": self._build_priority_matrix(),
            "regulation_sections": [r.to_pdf_content() for r in self.regulations],
            "strategic_themes": self.themes,
            "risk_assessment": self.risk_assessment,
            "resource_implications": self.resource_implications,
            "stats": self.stats
        }
    
    def _generate_executive_summary(self) -> str:
        """Generate executive summary from consolidated data."""
        critical_count = sum(1 for r in self.regulations if r.impact_level == ImpactLevel.CRITICAL)
        high_count = sum(1 for r in self.regulations if r.impact_level == ImpactLevel.HIGH)
        
        return (
            f"This Quarterly Strategic Brief consolidates {len(self.regulations)} key regulatory "
            f"developments from {self.reporting_period}. The quarter shows {critical_count} critical "
            f"and {high_count} high-priority regulatory drivers requiring strategic attention."
        )
    
    def _build_priority_matrix(self) -> List[List[str]]:
        """Build strategic priority matrix table data."""
        matrix = []
        for reg in sorted(self.regulations, 
                         key=lambda r: (r.impact_level != ImpactLevel.CRITICAL, 
                                       r.impact_level != ImpactLevel.HIGH)):
            matrix.append([
                reg.regulation_code,
                reg.impact_level.value,
                reg.primary_deadline.strftime("%b %d, %Y") if reg.primary_deadline else "TBD",
                ", ".join(reg.regulation_name.split()[:3]),  # Truncated name
                reg.investment_requirements[0].get("type", "TBD") if reg.investment_requirements else "TBD"
            ])
        return matrix


# ═════════════════════════════════════════════════════════════════════════════
# VALIDATION LOGIC
# ═════════════════════════════════════════════════════════════════════════════

class ChangeValidator:
    """
    Validates regulatory change entries for quality and reliability.
    
    Implements business rules for what constitutes a "validated" change
    suitable for quarterly reporting.
    """
    
    def __init__(
        self,
        min_sources: int = VALIDATION_MIN_SOURCES,
        min_confidence: float = CONFIDENCE_MEDIUM_THRESHOLD,
        max_age_days: int = VALIDATION_MAX_AGE_DAYS
    ):
        self.min_sources = min_sources
        self.min_confidence = min_confidence
        self.max_age_days = max_age_days
        self.validation_rules: List[Callable[[ChangeLogEntry], Tuple[bool, str]]] = [
            self._check_source_count,
            self._check_source_reliability,
            self._check_confidence_score,
            self._check_not_retracted,
            self._check_has_description,
            self._check_date_validity
        ]
    
    def validate(self, entry: ChangeLogEntry) -> Tuple[bool, List[str]]:
        """
        Validate a single change entry.
        
        Returns (is_valid, list_of_issues) tuple.
        """
        issues = []
        for rule in self.validation_rules:
            passed, message = rule(entry)
            if not passed:
                issues.append(message)
        
        return len(issues) == 0, issues
    
    def _check_source_count(self, entry: ChangeLogEntry) -> Tuple[bool, str]:
        if len(entry.sources) < self.min_sources:
            return False, f"Insufficient sources: {len(entry.sources)} < {self.min_sources}"
        return True, ""
    
    def _check_source_reliability(self, entry: ChangeLogEntry) -> Tuple[bool, str]:
        if not entry.sources:
            return False, "No sources provided"
        avg_reliability = sum(s.reliability_score for s in entry.sources) / len(entry.sources)
        if avg_reliability < _RELIABILITY_THRESHOLD:
            return False, f"Source reliability too low: {avg_reliability:.2f}"
        return True, ""
    
    def _check_confidence_score(self, entry: ChangeLogEntry) -> Tuple[bool, str]:
        score = entry.calculate_confidence_score()
        if score < self.min_confidence:
            return False, f"Confidence score below threshold: {score:.2f} < {self.min_confidence}"
        return True, ""
    
    def _check_not_retracted(self, entry: ChangeLogEntry) -> Tuple[bool, str]:
        if entry.status == ChangeStatus.RETRACTED:
            return False, "Entry has been retracted"
        return True, ""
    
    def _check_has_description(self, entry: ChangeLogEntry) -> Tuple[bool, str]:
        if not entry.description or len(entry.description) < _MIN_DESCRIPTION_LENGTH:
            return False, "Description too short or missing"
        return True, ""
    
    def _check_date_validity(self, entry: ChangeLogEntry) -> Tuple[bool, str]:
        age_days = (date.today() - entry.change_date).days
        if age_days > self.max_age_days:
            return False, f"Entry too old: {age_days} days > {self.max_age_days}"
        return True, ""
    
    def batch_validate(self, entries: List[ChangeLogEntry]) -> Dict[str, Any]:
        """Validate multiple entries and return summary statistics."""
        results = {
            "valid": [],
            "invalid": [],
            "by_status": defaultdict(int),
            "by_regulation": defaultdict(int)
        }
        
        for entry in entries:
            is_valid, issues = self.validate(entry)
            if is_valid:
                results["valid"].append(entry)
            else:
                results["invalid"].append({"entry": entry, "issues": issues})
            
            results["by_status"][entry.status.name] += 1
            results["by_regulation"][entry.regulation_code] += 1
        
        return results


# ═════════════════════════════════════════════════════════════════════════════
# CONSOLIDATION LOGIC
# ═════════════════════════════════════════════════════════════════════════════

class ConflictResolver:
    """
    Resolves conflicts between multiple entries for the same regulation.
    
    When different months report conflicting information about the same
    regulation, this class determines the authoritative view.
    """
    
    def __init__(self):
        self.resolution_strategies = {
            "deadline": self._resolve_deadline_conflict,
            "status": self._resolve_status_conflict,
            "impact": self._resolve_impact_conflict,
            "description": self._resolve_description_conflict
        }
    
    def resolve(
        self,
        entries: List[ChangeLogEntry],
        conflict_type: str
    ) -> Any:
        """
        Resolve conflicts of a specific type.
        
        Args:
            entries: List of entries with potential conflicts
            conflict_type: Type of conflict to resolve
            
        Returns:
            The resolved value
        """
        strategy = self.resolution_strategies.get(conflict_type)
        if not strategy:
            # Default: take the most recent validated entry
            return self._most_recent_validated(entries)
        return strategy(entries)
    
    def _most_recent_validated(self, entries: List[ChangeLogEntry]) -> ChangeLogEntry:
        """Select the most recent validated entry."""
        validated = [e for e in entries if e.status == ChangeStatus.VALIDATED]
        if validated:
            return max(validated, key=lambda e: e.updated_at)
        return max(entries, key=lambda e: e.updated_at)
    
    def _resolve_deadline_conflict(self, entries: List[ChangeLogEntry]) -> Optional[date]:
        """
        Resolve conflicting deadline information.
        
        Strategy: Use the most recently reported validated deadline.
        If multiple validated entries, prefer the one with highest confidence.
        """
        deadlines = []
        for entry in entries:
            for milestone in entry.milestones:
                if milestone.milestone_type in ("deadline", "effective"):
                    deadlines.append((
                        milestone.date,
                        entry.calculate_confidence_score(),
                        entry.updated_at,
                        milestone.confirmed
                    ))
        
        if not deadlines:
            return None
        
        # Sort by: confirmed (True first), confidence (high first), recency
        deadlines.sort(key=lambda d: (-d[3], -d[1], -d[2].timestamp()))
        return deadlines[0][0]
    
    def _resolve_status_conflict(self, entries: List[ChangeLogEntry]) -> str:
        """
        Resolve conflicting status information.
        
        Strategy: Use the status from the most recent entry unless
        an older entry has higher confidence and is validated.
        """
        best_entry = self._most_recent_validated(entries)
        return best_entry.status.name
    
    def _resolve_impact_conflict(self, entries: List[ChangeLogEntry]) -> ImpactLevel:
        """
        Resolve conflicting impact assessments.
        
        Strategy: Take the maximum impact level (most conservative).
        A CRITICAL assessment overrides MEDIUM, etc.
        """
        impact_priority = {
            ImpactLevel.CRITICAL: 4,
            ImpactLevel.HIGH: 3,
            ImpactLevel.MEDIUM: 2,
            ImpactLevel.LOW: 1,
            ImpactLevel.NONE: 0
        }
        return max(entries, key=lambda e: impact_priority.get(e.impact_level, 0)).impact_level
    
    def _resolve_description_conflict(self, entries: List[ChangeLogEntry]) -> str:
        """
        Resolve conflicting descriptions.
        
        Strategy: Use the longest description from a validated entry,
        as it likely contains the most complete information.
        """
        validated = [e for e in entries if e.status == ChangeStatus.VALIDATED]
        if validated:
            return max(validated, key=lambda e: len(e.description)).description
        return max(entries, key=lambda e: len(e.description)).description


class QuarterlyConsolidator:
    """
    Main consolidation engine for quarterly regulatory reporting.
    
    This class orchestrates the aggregation of 3 monthly changelogs
    into a strategic quarterly view.
    """
    
    def __init__(
        self,
        quarter: str,
        year: int,
        validator: Optional[ChangeValidator] = None,
        resolver: Optional[ConflictResolver] = None
    ):
        self.quarter = quarter
        self.year = year
        self.validator = validator or ChangeValidator()
        self.resolver = resolver or ConflictResolver()
        
        # Determine months in this quarter
        quarter_months = {"Q1": [1, 2, 3], "Q2": [4, 5, 6], 
                         "Q3": [7, 8, 9], "Q4": [10, 11, 12]}
        self.months = quarter_months.get(quarter, [1, 2, 3])
        self.month_names = [datetime(2000, m, 1).strftime("%B") for m in self.months]
    
    def consolidate(self, monthly_entries: List[ChangeLogEntry]) -> QuarterlySummary:
        """
        Main entry point: consolidate monthly entries into quarterly view.
        
        Args:
            monthly_entries: All change entries from the 3 months
            
        Returns:
            QuarterlySummary with consolidated regulatory view
        """
        # Step 1: Validate all entries
        validation_results = self.validator.batch_validate(monthly_entries)
        valid_entries = validation_results["valid"]
        
        # Step 2: Group by regulation
        by_regulation = self._group_by_regulation(valid_entries)
        
        # Step 3: Consolidate each regulation
        consolidated_regs = []
        for reg_code, entries in by_regulation.items():
            consolidated = self._consolidate_regulation(reg_code, entries)
            consolidated_regs.append(consolidated)
        
        # Step 4: Generate cross-cutting analysis
        themes = self._extract_strategic_themes(consolidated_regs)
        risk_assessment = self._assess_risks(consolidated_regs)
        resource_implications = self._analyze_resources(consolidated_regs)
        
        # Step 5: Compile statistics
        stats = {
            "total_entries_processed": len(monthly_entries),
            "valid_entries": len(valid_entries),
            "invalid_entries": len(validation_results["invalid"]),
            "regulations_consolidated": len(consolidated_regs),
            "by_impact": self._count_by_impact(consolidated_regs),
            "by_scope": self._count_by_scope(consolidated_regs),
            "month_coverage": {m: sum(1 for e in valid_entries 
                                     if e.reported_month.month == self.months[i])
                              for i, m in enumerate(self.month_names)}
        }
        
        return QuarterlySummary(
            quarter=f"{self.quarter} {self.year}",
            reporting_period=f"{self.month_names[0]} - {self.month_names[-1]} {self.year}",
            regulations=consolidated_regs,
            themes=themes,
            risk_assessment=risk_assessment,
            resource_implications=resource_implications,
            stats=stats
        )
    
    def _group_by_regulation(
        self,
        entries: List[ChangeLogEntry]
    ) -> Dict[str, List[ChangeLogEntry]]:
        """Group entries by regulation code."""
        groups = defaultdict(list)
        for entry in entries:
            groups[entry.regulation_code].append(entry)
        return dict(groups)
    
    def _consolidate_regulation(
        self,
        reg_code: str,
        entries: List[ChangeLogEntry]
    ) -> ConsolidatedRegulation:
        """
        Consolidate multiple entries for a single regulation.
        
        This is the core consolidation logic that transforms
        tracking-mode entries into reporting-mode narrative.
        """
        # Get representative entry for metadata
        representative = max(entries, key=lambda e: e.updated_at)
        
        # Resolve conflicts
        impact_level = self.resolver.resolve(entries, "impact")
        primary_deadline = self.resolver.resolve(entries, "deadline")
        latest_status = self.resolver.resolve(entries, "status")
        
        # Build narrative from entry progression
        narrative = self._build_narrative(entries)
        
        # Extract key developments (chronological order)
        developments = self._extract_developments(entries)
        
        # Determine confidence trend
        confidence_trend = self._analyze_confidence_trend(entries)
        
        # Build recommended actions
        actions = self._consolidate_actions(entries)
        
        # Build investment requirements
        investments = self._consolidate_investments(entries)
        
        # Determine month coverage
        month_coverage = {e.reported_month.strftime("%B") for e in entries}
        
        return ConsolidatedRegulation(
            regulation_code=reg_code,
            regulation_name=representative.regulation_name,
            scope=representative.scope,
            impact_level=impact_level,
            latest_status=latest_status,
            primary_deadline=primary_deadline,
            executive_summary=narrative["executive_summary"],
            strategic_implications=narrative["strategic_implications"],
            key_developments=developments,
            recommended_actions=actions,
            investment_requirements=investments,
            source_entries=[e.id for e in entries],
            month_coverage=month_coverage,
            first_observed=min(e.change_date for e in entries),
            last_updated=max(e.updated_at for e in entries),
            confidence_trend=confidence_trend
        )
    
    def _build_narrative(self, entries: List[ChangeLogEntry]) -> Dict[str, str]:
        """
        Build narrative summaries from entry progression.
        
        Transforms technical tracking entries into strategic
        executive summary language.
        """
        # Sort by date
        sorted_entries = sorted(entries, key=lambda e: e.change_date)
        
        # Build executive summary
        latest = sorted_entries[-1]
        if len(sorted_entries) == 1:
            exec_summary = (
                f"{latest.regulation_name} was identified in {latest.reported_month.strftime('%B')} "
                f"as {latest.impact_level.value.lower()} priority. {latest.executive_summary or latest.description[:200]}"
            )
        else:
            progression = self._describe_progression(sorted_entries)
            exec_summary = (
                f"{latest.regulation_name} evolved over the quarter: {progression} "
                f"Current status indicates {latest.impact_level.value.lower()} impact with "
                f"{latest.status.name.lower()} confirmation."
            )
        
        # Build strategic implications
        implications = self._derive_implications(sorted_entries)
        
        return {
            "executive_summary": exec_summary,
            "strategic_implications": implications
        }
    
    def _describe_progression(self, entries: List[ChangeLogEntry]) -> str:
        """Describe how a regulation evolved over entries."""
        if len(entries) < 2:
            return entries[0].title if entries else ""
        
        # Look for patterns: escalation, clarification, deadline shift
        first_impact = entries[0].impact_level
        last_impact = entries[-1].impact_level
        
        impact_priority = {
            ImpactLevel.CRITICAL: 4, ImpactLevel.HIGH: 3,
            ImpactLevel.MEDIUM: 2, ImpactLevel.LOW: 1, ImpactLevel.NONE: 0
        }
        
        if impact_priority[last_impact] > impact_priority[first_impact]:
            return f"escalating from {first_impact.value} to {last_impact.value} priority."
        elif impact_priority[last_impact] < impact_priority[first_impact]:
            return f"de-escalating from {first_impact.value} to {last_impact.value} priority."
        else:
            return f"maintaining {first_impact.value} priority with additional clarifications."
    
    def _derive_implications(self, entries: List[ChangeLogEntry]) -> str:
        """Derive strategic implications from entry analysis."""
        implications = []
        
        # Analyze investment patterns
        investments = [e.investment_type for e in entries if e.investment_type != InvestmentType.NONE]
        if investments:
            investment_types = set(i.value for i in investments)
            implications.append(f"Requires {', '.join(investment_types)} investment.")
        
        # Analyze affected areas
        all_areas = set()
        for e in entries:
            all_areas.update(e.affected_areas)
        if all_areas:
            implications.append(f"Impacts: {', '.join(list(all_areas)[:3])}.")
        
        # Timeline implication
        deadlines = [m.date for e in entries for m in e.milestones 
                    if m.milestone_type == "deadline"]
        if deadlines:
            nearest = min(deadlines)
            days_until = (nearest - date.today()).days
            if days_until < 180:
                implications.append(f"Urgent: {days_until} days to primary deadline.")
        
        return " ".join(implications) if implications else "Continue monitoring."
    
    def _extract_developments(self, entries: List[ChangeLogEntry]) -> List[str]:
        """Extract key developments chronologically."""
        developments = []
        for entry in sorted(entries, key=lambda e: e.change_date):
            dev = f"{entry.reported_month.strftime('%B')}: {entry.title}"
            if entry.action_items:
                dev += f" ({len(entry.action_items)} action items)"
            developments.append(dev)
        return developments
    
    def _analyze_confidence_trend(self, entries: List[ChangeLogEntry]) -> str:
        """Analyze whether confidence is improving or declining."""
        if len(entries) < 2:
            return "stable"
        
        sorted_entries = sorted(entries, key=lambda e: e.updated_at)
        first_conf = sorted_entries[0].calculate_confidence_score()
        last_conf = sorted_entries[-1].calculate_confidence_score()
        
        diff = last_conf - first_conf
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        return "stable"
    
    def _consolidate_actions(self, entries: List[ChangeLogEntry]) -> List[Dict[str, Any]]:
        """Consolidate action items from all entries."""
        actions = []
        seen = set()
        
        for entry in entries:
            for action in entry.action_items:
                # Deduplicate similar actions
                action_key = action.lower()[:50]
                if action_key not in seen:
                    seen.add(action_key)
                    actions.append({
                        "action": action,
                        "priority": entry.impact_level.value,
                        "source_month": entry.reported_month.strftime("%B"),
                        "regulation": entry.regulation_code
                    })
        
        # Sort by priority
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        actions.sort(key=lambda a: priority_order.get(a["priority"], 99))
        return actions[:10]  # Limit to top 10
    
    def _consolidate_investments(self, entries: List[ChangeLogEntry]) -> List[Dict[str, Any]]:
        """Consolidate investment requirements."""
        investments = []
        
        for entry in entries:
            if entry.investment_type != InvestmentType.NONE:
                investments.append({
                    "type": entry.investment_type.value,
                    "area": ", ".join(entry.affected_areas[:2]),
                    "priority": entry.impact_level.value,
                    "regulation": entry.regulation_code
                })
        
        # Remove duplicates by type+area
        seen = set()
        unique = []
        for inv in investments:
            key = (inv["type"], inv["area"])
            if key not in seen:
                seen.add(key)
                unique.append(inv)
        
        return unique
    
    def _extract_strategic_themes(
        self,
        regulations: List[ConsolidatedRegulation]
    ) -> List[Dict[str, Any]]:
        """Extract cross-cutting strategic themes."""
        themes = []
        
        # Theme 1: Regulatory convergence
        critical_regs = [r for r in regulations if r.impact_level == ImpactLevel.CRITICAL]
        if len(critical_regs) >= 2:
            themes.append({
                "theme": "Regulatory Convergence",
                "description": f"Multiple critical regulations ({len(critical_regs)}) requiring simultaneous compliance efforts.",
                "regulations": [r.regulation_code for r in critical_regs],
                "strategic_implication": "Prioritize integrated compliance programs to address overlapping requirements."
            })
        
        # Theme 2: Timeline clustering
        deadlines = [(r.regulation_code, r.primary_deadline) for r in regulations if r.primary_deadline]
        if deadlines:
            deadlines.sort(key=lambda d: d[1])
            q2_deadlines = [d for d in deadlines if d[1].month in [4, 5, 6]]
            if len(q2_deadlines) >= 2:
                themes.append({
                    "theme": "Q2 Deadline Cluster",
                    "description": f"Multiple regulations with Q2 deadlines: {', '.join(d[0] for d in q2_deadlines)}",
                    "regulations": [d[0] for d in q2_deadlines],
                    "strategic_implication": "Resource allocation should prioritize Q2 deliverables."
                })
        
        # Theme 3: Investment pattern
        investment_regs = [r for r in regulations if r.investment_requirements]
        capex_count = sum(1 for r in investment_regs 
                         if any(i["type"] == "CAPEX" for i in r.investment_requirements))
        if capex_count >= 2:
            themes.append({
                "theme": "Capital Investment Wave",
                "description": f"{capex_count} regulations requiring capital expenditure.",
                "regulations": [r.regulation_code for r in investment_regs],
                "strategic_implication": "Coordinate CAPEX planning across facilities to optimize investment."
            })
        
        return themes
    
    def _assess_risks(self, regulations: List[ConsolidatedRegulation]) -> Dict[str, Any]:
        """Generate risk assessment from consolidated data."""
        return {
            "high_risk_regulations": [
                {
                    "code": r.regulation_code,
                    "risk": f"{r.impact_level.value} impact with approaching deadline"
                }
                for r in regulations
                if r.impact_level in (ImpactLevel.CRITICAL, ImpactLevel.HIGH)
                and r.primary_deadline
                and (r.primary_deadline - date.today()).days < 180
            ],
            "compliance_gaps": [],  # Would be populated from gap analysis
            "monitoring_required": [
                r.regulation_code for r in regulations
                if r.confidence_trend == "declining"
            ]
        }
    
    def _analyze_resources(self, regulations: List[ConsolidatedRegulation]) -> Dict[str, Any]:
        """Analyze resource implications."""
        # Count by investment type
        investment_counts = defaultdict(int)
        for r in regulations:
            for inv in r.investment_requirements:
                investment_counts[inv["type"]] += 1
        
        # Affected departments
        affected = set()
        for r in regulations:
            # Parse from regulation name and summary
            if "packaging" in r.regulation_name.lower():
                affected.update(["Procurement", "Packaging R&D"])
            if "reporting" in r.regulation_name.lower() or "CSRD" in r.regulation_code:
                affected.update(["Finance", "Sustainability"])
            if "supply" in r.strategic_implications.lower() or "EUDR" in r.regulation_code:
                affected.update(["Supply Chain", "Procurement"])
        
        return {
            "investment_summary": dict(investment_counts),
            "affected_departments": sorted(list(affected)),
            "estimated_effort": "High" if len([r for r in regulations if r.impact_level == ImpactLevel.CRITICAL]) > 1 else "Moderate"
        }
    
    def _count_by_impact(self, regulations: List[ConsolidatedRegulation]) -> Dict[str, int]:
        """Count regulations by impact level."""
        counts = defaultdict(int)
        for r in regulations:
            counts[r.impact_level.value] += 1
        return dict(counts)
    
    def _count_by_scope(self, regulations: List[ConsolidatedRegulation]) -> Dict[str, int]:
        """Count regulations by scope."""
        counts = defaultdict(int)
        for r in regulations:
            counts[r.scope.value] += 1
        return dict(counts)


# ═════════════════════════════════════════════════════════════════════════════
# OUTPUT & SERIALIZATION
# ═════════════════════════════════════════════════════════════════════════════

class QuarterlyOutputFormatter:
    """
    Formats quarterly consolidation output for various destinations.
    
    Primary destination: ReportLab PDF generation pipeline
    Secondary: JSON export for archival/API usage
    """
    
    @staticmethod
    def to_pdf_input(summary: QuarterlySummary) -> Dict[str, Any]:
        """
        Format for direct consumption by ReportLab PDF builder.
        
        Structure matches the expected input for build_quarterly_brief.py
        """
        return summary.to_pdf_format()
    
    @staticmethod
    def to_json(summary: QuarterlySummary, indent: int = 2) -> str:
        """Serialize to JSON for archival or API transmission."""
        data = {
            "quarter": summary.quarter,
            "reporting_period": summary.reporting_period,
            "generated_at": summary.generated_at.isoformat(),
            "regulations": [
                {
                    "code": r.regulation_code,
                    "name": r.regulation_name,
                    "scope": r.scope.value,
                    "impact": r.impact_level.value,
                    "status": r.latest_status,
                    "deadline": r.primary_deadline.isoformat() if r.primary_deadline else None,
                    "executive_summary": r.executive_summary,
                    "strategic_implications": r.strategic_implications,
                    "key_developments": r.key_developments,
                    "recommended_actions": r.recommended_actions,
                    "investment_requirements": r.investment_requirements,
                    "month_coverage": sorted(list(r.month_coverage)),
                    "confidence_trend": r.confidence_trend
                }
                for r in summary.regulations
            ],
            "themes": summary.themes,
            "risk_assessment": summary.risk_assessment,
            "resource_implications": summary.resource_implications,
            "stats": summary.stats
        }
        return json.dumps(data, indent=indent, default=str)
    
    @staticmethod
    def to_markdown(summary: QuarterlySummary) -> str:
        """Generate markdown summary for review/approval workflows."""
        lines = [
            f"# Quarterly Regulatory Consolidation: {summary.quarter}",
            f"",
            f"**Reporting Period:** {summary.reporting_period}",
            f"**Generated:** {summary.generated_at.strftime('%Y-%m-%d %H:%M')}",
            f"",
            "---",
            f"",
            "## Executive Summary",
            f"",
            summary._generate_executive_summary(),
            f"",
            "## Consolidated Regulations",
            f""
        ]
        
        for reg in summary.regulations:
            lines.extend([
                f"### {reg.regulation_code}: {reg.regulation_name}",
                f"",
                f"**Impact Level:** {reg.impact_level.value}",
                f"**Status:** {reg.latest_status}",
                f"**Primary Deadline:** {reg.primary_deadline.strftime('%B %d, %Y') if reg.primary_deadline else 'TBD'}",
                f"",
                f"**Executive Summary:**",
                f"> {reg.executive_summary}",
                f"",
                f"**Strategic Implications:**",
                f"> {reg.strategic_implications}",
                f"",
                "**Key Developments:**",
            ])
            for dev in reg.key_developments:
                lines.append(f"- {dev}")
            lines.append("")
        
        return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════

def load_entries_from_json(file_path: str) -> List[ChangeLogEntry]:
    """
    Load change log entries from a JSON file.
    
    Expected format: List of entry dictionaries matching ChangeLogEntry schema.
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    entries = []
    for item in data:
        # Parse sources
        sources = [
            SourceReference(
                id=s["id"],
                title=s["title"],
                url=s.get("url"),
                publisher=s.get("publisher"),
                publish_date=date.fromisoformat(s["publish_date"]) if s.get("publish_date") else None,
                access_date=date.fromisoformat(s["access_date"]),
                reliability_score=s.get("reliability_score", 0.8)
            )
            for s in item.get("sources", [])
        ]
        
        # Parse milestones
        milestones = [
            TimelineMilestone(
                date=date.fromisoformat(m["date"]),
                description=m["description"],
                milestone_type=m["milestone_type"],
                confirmed=m.get("confirmed", True)
            )
            for m in item.get("milestones", [])
        ]
        
        entry = ChangeLogEntry(
            id=item["id"],
            regulation_code=item["regulation_code"],
            regulation_name=item["regulation_name"],
            reported_month=date.fromisoformat(item["reported_month"]),
            change_date=date.fromisoformat(item["change_date"]),
            title=item["title"],
            description=item["description"],
            change_type=item["change_type"],
            scope=RegulationScope(item["scope"]),
            impact_level=ImpactLevel(item["impact_level"]),
            affected_areas=item.get("affected_areas", []),
            investment_type=InvestmentType(item.get("investment_type", "NONE")),
            status=ChangeStatus[item.get("status", "DRAFT")],
            sources=sources,
            related_entries=item.get("related_entries", []),
            milestones=milestones,
            executive_summary=item.get("executive_summary"),
            action_items=item.get("action_items", [])
        )
        entries.append(entry)
    
    return entries


def save_consolidation_output(summary: QuarterlySummary, output_dir: str) -> Dict[str, str]:
    """
    Save consolidation output in multiple formats.
    
    Returns dict mapping format name to file path.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    quarter_slug = summary.quarter.lower().replace(" ", "_")
    files = {}
    
    # JSON format
    json_path = output_path / f"consolidation_{quarter_slug}.json"
    with open(json_path, 'w') as f:
        f.write(QuarterlyOutputFormatter.to_json(summary))
    files["json"] = str(json_path)
    
    # Markdown format
    md_path = output_path / f"consolidation_{quarter_slug}.md"
    with open(md_path, 'w') as f:
        f.write(QuarterlyOutputFormatter.to_markdown(summary))
    files["markdown"] = str(md_path)
    
    return files


# ═════════════════════════════════════════════════════════════════════════════
# MAIN WORKFLOW FUNCTION
# ═════════════════════════════════════════════════════════════════════════════

def run_quarterly_consolidation(
    month1_entries: List[ChangeLogEntry],
    month2_entries: List[ChangeLogEntry],
    month3_entries: List[ChangeLogEntry],
    quarter: str,
    year: int
) -> QuarterlySummary:
    """
    Main workflow function: consolidate three months into quarterly view.
    
    This is the primary entry point for the consolidation workflow.
    
    Args:
        month1_entries: Change log entries from first month of quarter
        month2_entries: Change log entries from second month of quarter
        month3_entries: Change log entries from third month of quarter
        quarter: Quarter identifier ("Q1", "Q2", "Q3", "Q4")
        year: Year (e.g., 2026)
        
    Returns:
        QuarterlySummary ready for PDF generation
    """
    # Combine all entries
    all_entries = month1_entries + month2_entries + month3_entries
    
    # Run consolidation
    consolidator = QuarterlyConsolidator(quarter=quarter, year=year)
    summary = consolidator.consolidate(all_entries)
    
    return summary


# Example usage and testing
if __name__ == "__main__":
    # Demonstrate the workflow with sample data
    print("=" * 70)
    print("VISUSTA Quarterly Consolidation Module - Demo")
    print("=" * 70)
    
    # Create sample entries for Q1 2026
    sample_entries = [
        # January entries
        ChangeLogEntry(
            id="CHG-2026-001",
            regulation_code="PPWR",
            regulation_name="EU Packaging and Packaging Waste Regulation",
            reported_month=date(2026, 1, 1),
            change_date=date(2026, 1, 15),
            title="PPWR General Application Date Confirmed",
            description="The EU Packaging and Packaging Waste Regulation will apply from August 12, 2026.",
            change_type="deadline_confirmation",
            scope=RegulationScope.EU,
            impact_level=ImpactLevel.CRITICAL,
            affected_areas=["Packaging", "R&D"],
            investment_type=InvestmentType.CAPEX,
            status=ChangeStatus.VALIDATED,
            sources=[
                SourceReference(id="SRC-001", title="EUR-Lex Official Journal", reliability_score=1.0),
                SourceReference(id="SRC-002", title="European Commission Press Release", reliability_score=0.95)
            ],
            milestones=[TimelineMilestone(date=date(2026, 8, 12), description="General Application", milestone_type="deadline")],
            executive_summary="PPWR enters into force August 2026, requiring immediate packaging redesign efforts.",
            action_items=["Audit packaging portfolio", "Secure rPET supply contracts"]
        ),
        # February entries - evolution of PPWR story
        ChangeLogEntry(
            id="CHG-2026-015",
            regulation_code="PPWR",
            regulation_name="EU Packaging and Packaging Waste Regulation",
            reported_month=date(2026, 2, 1),
            change_date=date(2026, 2, 10),
            title="ZSVR 2025 Minimum Standard Published",
            description="German ZSVR published the 2025 Minimum Standard, providing bridge criteria to PPWR recyclability grades.",
            change_type="guidance",
            scope=RegulationScope.GERMANY,
            impact_level=ImpactLevel.HIGH,
            affected_areas=["Packaging", "Compliance"],
            investment_type=InvestmentType.AUDIT,
            status=ChangeStatus.VALIDATED,
            sources=[
                SourceReference(id="SRC-024", title="ZSVR Official Publication", reliability_score=0.95),
                SourceReference(id="SRC-025", title="Packaging World Analysis", reliability_score=0.8)
            ],
            executive_summary="German ZSVR standard provides interim guidance for PPWR recyclability assessment.",
            action_items=["Compare packaging against ZSVR standard", "Identify Grade D/E risks"]
        ),
        # March entries
        ChangeLogEntry(
            id="CHG-2026-032",
            regulation_code="EUDR",
            regulation_name="EU Deforestation Regulation",
            reported_month=date(2026, 3, 1),
            change_date=date(2026, 3, 5),
            title="EUDR Delay Confirmed - New December 2026 Deadline",
            description="European Commission proposes additional 12-month delay to EUDR application date.",
            change_type="deadline_change",
            scope=RegulationScope.EU,
            impact_level=ImpactLevel.MEDIUM,
            affected_areas=["Supply Chain", "IT Systems"],
            investment_type=InvestmentType.IT,
            status=ChangeStatus.VALIDATED,
            sources=[
                SourceReference(id="SRC-029", title="European Commission Proposal", reliability_score=0.95),
                SourceReference(id="SRC-030", title="Latham & Watkins Analysis", reliability_score=0.85)
            ],
            milestones=[
                TimelineMilestone(date=date(2026, 12, 30), description="New Application Date", milestone_type="deadline")
            ],
            executive_summary="EUDR delayed to December 2026, providing additional preparation time but maintaining core requirements.",
            action_items=["Continue data collection pilots", "Test EU Information System integration"]
        ),
    ]
    
    # Run consolidation
    consolidator = QuarterlyConsolidator(quarter="Q1", year=2026)
    summary = consolidator.consolidate(sample_entries)
    
    # Display results
    print(f"\n📊 Consolidation Results for {summary.quarter}")
    print(f"   Period: {summary.reporting_period}")
    print(f"\n📈 Statistics:")
    for key, value in summary.stats.items():
        print(f"   {key}: {value}")
    
    print(f"\n📋 Consolidated Regulations ({len(summary.regulations)}):")
    for reg in summary.regulations:
        print(f"\n   🔹 {reg.regulation_code}: {reg.regulation_name}")
        print(f"      Impact: {reg.impact_level.value} | Status: {reg.latest_status}")
        print(f"      Months covered: {', '.join(sorted(reg.month_coverage))}")
        print(f"      Confidence trend: {reg.confidence_trend}")
        if reg.primary_deadline:
            print(f"      Primary deadline: {reg.primary_deadline.strftime('%B %d, %Y')}")
    
    print(f"\n🎯 Strategic Themes ({len(summary.themes)}):")
    for theme in summary.themes:
        print(f"\n   📌 {theme['theme']}")
        print(f"      {theme['description']}")
        print(f"      Implication: {theme['strategic_implication']}")
    
    print("\n" + "=" * 70)
    print("Demo complete. Module ready for integration.")
    print("=" * 70)
