"""
Pydantic request/response schemas for the Visusta API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Request bodies ─────────────────────────────────────────────────────────────

class MonthlyReportRequest(BaseModel):
    period: str = Field(..., example="2026-02", description="Period in YYYY-MM format")
    tone: Optional[str] = None
    depth: Optional[str] = None
    chart_mix: Optional[List[str]] = None
    section_order: Optional[List[str]] = None


class QuarterlyReportRequest(BaseModel):
    quarter: int = Field(..., ge=1, le=4, example=1, description="Quarter number (1-4)")
    year: int = Field(..., ge=2000, le=2100, example=2026, description="Four-digit year")
    tone: Optional[str] = None
    depth: Optional[str] = None
    chart_mix: Optional[List[str]] = None
    section_order: Optional[List[str]] = None


class ScreeningRunRequest(BaseModel):
    period: str = Field(..., example="2026-02", description="Period in YYYY-MM format")


# ── Facility schema ────────────────────────────────────────────────────────────

class FacilitySchema(BaseModel):
    name: str
    jurisdiction: str


# ── Sources / Thresholds / Preferences schemas ─────────────────────────────────

class SourceConfig(BaseModel):
    id: str = Field(..., description="Unique source identifier, e.g. 'eur_lex'")
    display_name: str = Field(..., description="Human-readable source name")
    url: Optional[str] = None
    frequency: str = Field(default="weekly", description="Polling frequency: daily or weekly")
    source_type: str = Field(default="gazette", description="gazette, agency, ministry, registry, legislature")


class Thresholds(BaseModel):
    critical_enforcement_window_days: int = 90
    min_confidence: float = 0.6
    min_sources_per_entry: int = 2


class ReportPreferences(BaseModel):
    tone: str = "executive"
    depth: str = "standard"
    chart_mix: List[str] = Field(
        default_factory=lambda: ["severity_heatmap", "enforcement_timeline", "topic_distribution"]
    )
    section_order: List[str] = Field(
        default_factory=lambda: [
            "executive_summary", "critical_actions", "topic_status",
            "change_log", "impact_summary", "references"
        ]
    )


# ── Client schemas ─────────────────────────────────────────────────────────────

class ClientCreate(BaseModel):
    client_id: Optional[str] = Field(None, description="Explicit client ID; slugified from display_name if omitted")
    display_name: str = Field(..., description="Human-readable client name")
    facilities: List[FacilitySchema] = Field(default_factory=list)
    allowed_countries: List[str] = Field(default_factory=lambda: ["EU"])
    required_topics: List[str] = Field(
        default_factory=lambda: ["ghg", "packaging", "water", "waste", "social_human_rights"]
    )
    branding: Optional[Dict[str, str]] = None
    created_at: Optional[str] = None


class ClientResponse(BaseModel):
    client_id: str
    display_name: str
    facilities: List[FacilitySchema] = Field(default_factory=list)
    allowed_countries: List[str] = Field(default_factory=list)
    required_topics: List[str] = Field(default_factory=list)
    branding: Optional[Dict[str, str]] = None
    created_at: Optional[str] = None
    sources: List[SourceConfig] = Field(default_factory=list)
    thresholds: Thresholds = Field(default_factory=Thresholds)
    report_preferences: ReportPreferences = Field(default_factory=ReportPreferences)


# ── Cross-client overview schemas ──────────────────────────────────────────────

class ClientSummary(BaseModel):
    client_id: str
    display_name: str
    last_screening: Optional[str] = None
    changes_detected: int = 0
    critical_count: int = 0


class OverviewResponse(BaseModel):
    clients: List[ClientSummary]


# ── Response bodies ────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    last_screening_date: Optional[str]
    config_status: str
    data_dir_exists: bool
    changelog_count: int
    state_count: int


class PeriodListResponse(BaseModel):
    periods: List[str]


class TopicsResponse(BaseModel):
    topics: List[str]


class FindingSchema(BaseModel):
    severity: str
    category: str
    location: str
    message: str
    evidence: Optional[str] = None


class AuditResponse(BaseModel):
    finding_count: int
    findings: List[FindingSchema]


# ── Evidence schemas ───────────────────────────────────────────────────────────

class EvidenceRecord(BaseModel):
    evidence_id: str
    client_id: str
    source_id: str
    source_name: str
    url: str
    access_date: str
    document_title: str
    snippet: str
    hash: str
    attached_by: str
    confidence: float
    topic: str = ""
    related_regulation_id: str = ""


class EvidenceCreate(BaseModel):
    url: str
    source_id: Optional[str] = None
    document_title: Optional[str] = None
    snippet: Optional[str] = None
    topic: Optional[str] = None
    related_regulation_id: Optional[str] = None


class EvidenceListResponse(BaseModel):
    evidence: List[EvidenceRecord]
    total: int
