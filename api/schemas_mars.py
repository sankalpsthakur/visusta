"""
Pydantic models for the MARS (Multilingual Adaptive Report Studio) API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


# ── Locales ────────────────────────────────────────────────────────────────────

class LocaleResponse(BaseModel):
    code: str
    name: str
    native_name: str
    is_active: bool


class ClientLocaleSettings(BaseModel):
    client_id: str
    primary_locale: str
    enabled_locales: List[str]
    fallback_locale: str = "en"
    updated_at: Optional[str] = None


class ClientLocaleSettingsUpdate(BaseModel):
    primary_locale: Optional[str] = None
    enabled_locales: Optional[List[str]] = None
    fallback_locale: Optional[str] = None


# ── Keyword rules ──────────────────────────────────────────────────────────────

class KeywordRuleCreate(BaseModel):
    phrase: str
    locale: str = "en"
    weight: float = Field(default=1.0, ge=0.0, le=10.0)
    category: Optional[str] = None


class KeywordRuleResponse(BaseModel):
    id: int
    client_id: str
    phrase: str
    locale: str
    weight: float
    category: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str


class KeywordPreviewRequest(BaseModel):
    phrases: List[str]
    locale: str = "en"
    sample_text: str


class KeywordPreviewResponse(BaseModel):
    matches: List[Dict[str, Any]]   # [{phrase, start, end, context}]
    match_count: int


# ── Source proposals ───────────────────────────────────────────────────────────

class SourceProposalResponse(BaseModel):
    id: int
    client_id: str
    url: str
    title: Optional[str] = None
    publisher: Optional[str] = None
    rationale: Optional[str] = None
    status: str
    proposed_by: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    created_at: str
    updated_at: str


class SourceProposalAction(BaseModel):
    action: Literal["approve", "reject", "pause"]
    reviewer: str
    note: Optional[str] = None


class SourceProposalImpactRecord(BaseModel):
    regulation_id: str
    title: str
    topic: str


class SourceProposalImpactResponse(BaseModel):
    proposal_id: int
    estimated_matches: int
    sample_regulations: List[SourceProposalImpactRecord]
    coverage_delta: float


# ── Templates ──────────────────────────────────────────────────────────────────

class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    industry_profile_id: Optional[int] = None
    base_locale: str = "en"


class TemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    industry_profile_id: Optional[int] = None
    base_locale: str
    current_version: int
    is_published: bool
    created_by: Optional[str] = None
    created_at: str
    updated_at: str


class TemplateVersionCreate(BaseModel):
    sections_json: List[Dict[str, Any]] = Field(default_factory=list)
    theme_tokens: Dict[str, Any] = Field(default_factory=dict)
    changelog_note: Optional[str] = None
    created_by: Optional[str] = None


class TemplateVersionResponse(BaseModel):
    id: int
    template_id: int
    version_number: int
    sections_json: List[Dict[str, Any]]
    theme_tokens: Dict[str, Any]
    changelog_note: Optional[str] = None
    created_by: Optional[str] = None
    created_at: str


class TemplateCloneRequest(BaseModel):
    name: str
    description: Optional[str] = None


class TemplateSectionInput(BaseModel):
    section_id: str
    heading: str
    order: int = 0
    prompt_template: str = ""
    chart_types: List[str] = Field(default_factory=list)
    max_tokens: int = 1000
    required: bool = False


class TemplateSectionsUpdate(BaseModel):
    sections: List[TemplateSectionInput] = Field(default_factory=list)
    changelog: Optional[str] = None
    created_by: Optional[str] = None


class TemplateThemeUpdate(BaseModel):
    tokens: Dict[str, Any] = Field(default_factory=dict)
    changelog: Optional[str] = None
    created_by: Optional[str] = None


# ── Draft sections ─────────────────────────────────────────────────────────────

class SectionBlock(BaseModel):
    block_id: str
    block_type: str      # e.g. 'paragraph', 'chart', 'table', 'heading'
    content: Any         # type depends on block_type
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    """A source reference with an optional URL.

    Accepts both the new dict shape and the legacy plain-string shape so
    revisions persisted before this schema change keep deserializing.
    """

    label: str
    url: Optional[str] = None


class DraftSection(BaseModel):
    section_id: str
    heading: str
    locale: str
    blocks: List[SectionBlock] = Field(default_factory=list)
    facts: List[str] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    translation_status: Optional[str] = None   # None | 'pending' | 'done' | 'failed'
    approval_status: Optional[str] = None      # None | 'pending' | 'approved' | 'rejected' | 'needs_revision'

    @field_validator("citations", mode="before")
    @classmethod
    def _coerce_citations(cls, value: Any) -> Any:
        """Accept legacy List[str] citations alongside the new List[Citation] shape.

        Old revision blobs were written as plain strings like
        "Stortinget — Norwegian Parliament" or "Title — https://...". They are
        coerced to ``{"label": <string>, "url": None}`` here so Pydantic's
        standard validation can then build ``Citation`` objects. New dict-shaped
        entries pass through untouched.
        """
        if not isinstance(value, list):
            return value
        coerced: List[Any] = []
        for item in value:
            if isinstance(item, str):
                coerced.append({"label": item, "url": None})
            elif isinstance(item, dict):
                coerced.append(item)
            elif item is None:
                continue
            else:
                coerced.append({"label": str(item), "url": None})
        return coerced


# ── Draft revisions ────────────────────────────────────────────────────────────

class RevisionResponse(BaseModel):
    id: int
    draft_id: int
    revision_number: int
    authored_by: Optional[str] = None
    note: Optional[str] = None
    created_at: str


class RevisionDetailResponse(RevisionResponse):
    sections: List[DraftSection]


# ── Drafts ─────────────────────────────────────────────────────────────────────

class DraftCreate(BaseModel):
    title: str
    template_version_id: Optional[int] = None
    period: Optional[str] = None
    primary_locale: str = "en"
    created_by: Optional[str] = None


class DraftResponse(BaseModel):
    id: int
    client_id: str
    template_version_id: Optional[int] = None
    title: str
    period: Optional[str] = None
    primary_locale: str
    status: str
    current_revision_id: Optional[int] = None
    created_by: Optional[str] = None
    created_at: str
    updated_at: str


class DraftDetailResponse(DraftResponse):
    current_revision: Optional[RevisionDetailResponse] = None


# ── Chat ───────────────────────────────────────────────────────────────────────

class ChatMessageCreate(BaseModel):
    role: Literal["user", "assistant", "system"] = "user"
    content: str
    section_id: Optional[str] = None


class DraftBlockInput(BaseModel):
    type: str = "paragraph"
    content: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SectionEditRequest(BaseModel):
    blocks: Optional[List[DraftBlockInput]] = None
    facts: Optional[List[str]] = None
    citations: Optional[List[str]] = None
    revision_note: Optional[str] = None


class ChatMessageResponse(BaseModel):
    id: int
    draft_id: int
    section_id: Optional[str] = None
    role: str
    content: str
    revision_id: Optional[int] = None
    created_at: str


# ── Approval ───────────────────────────────────────────────────────────────────

class ApprovalAction(BaseModel):
    section_id: str
    status: Literal["approved", "rejected", "needs_revision"]
    reviewer: str
    comment: Optional[str] = None


class ApprovalStateResponse(BaseModel):
    id: int
    draft_id: int
    section_id: str
    status: str
    reviewer: Optional[str] = None
    comment: Optional[str] = None
    revision_id: Optional[int] = None
    created_at: str
    updated_at: str


# ── Exports ────────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    format: Literal["pdf", "docx"]
    locale: Optional[str] = None
    revision_id: Optional[int] = None
    requested_by: Optional[str] = None


class ExportJobResponse(BaseModel):
    id: int
    draft_id: int
    revision_id: Optional[int] = None
    format: str
    locale: Optional[str] = None
    status: str
    output_path: Optional[str] = None
    error: Optional[str] = None
    requested_by: Optional[str] = None
    created_at: str
    updated_at: str


class DocxImportResponse(BaseModel):
    draft_id: int
    revision_id: int
    sections_imported: int
    warnings: List[str] = Field(default_factory=list)
