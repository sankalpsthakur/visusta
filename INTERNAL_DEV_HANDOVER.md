# VISUSTA -- Internal Development Handover

**CLASSIFICATION: INTERNAL -- DEVELOPMENT TEAM ONLY**

Date: February 2026
Author: Sankalp (Architecture & Client Comms)
Status: Active development -- pre-productization phase

---

## 1. Project Overview

### What Visusta Is

Visusta is a regulatory intelligence tool for food manufacturers. It tracks EU and German sustainability regulations across five topics (GHG, Packaging, Water, Waste, Social/Human Rights), detects changes month-over-month, and produces branded PDF reports for executive leadership.

### Client Context

- **Industry:** Food manufacturing
- **Facilities:** Hamburg and Rietberg (NRW), Germany
- **Regulatory scope:** EU-wide + German federal + state-level (Hamburg, NRW)
- **Report cadence:** Monthly impact reports + Quarterly strategic briefs
- **Audience:** Executive leadership, regulatory affairs, operations

### What We've Sold

A regulatory monitoring and reporting system that:
1. Ingests regulatory data from multiple sources
2. Detects changes against the previous month's baseline
3. Generates per-topic change/no-change status (required monthly deliverable)
4. Consolidates 3 months into a quarterly strategic view
5. Produces branded PDF reports with charts, tables, and references

### What Currently Exists

An engineering prototype. The data models and change detection logic are solid. The PDF output is production-quality visually but hardcoded. There is no API, no database, no frontend, no LLM integration, and no test suite.

---

## 2. Codebase Map

### File Inventory

| File | Lines | Purpose | Key Classes/Functions |
|------|------:|---------|----------------------|
| `regulatory_screening.py` | 1,360 | Monthly change detection engine | `RegulatoryScreeningModule`, `RegulationStore` (Protocol), `ScreeningSource` (Protocol), `FileSystemRegulationStore` |
| `quarterly_consolidator.py` | 1,310 | 3-month aggregation, validation, conflict resolution | `QuarterlyConsolidator`, `ChangeValidator`, `ConflictResolver`, `QuarterlyOutputFormatter` |
| `build_monthly_report.py` | 867 | Monthly PDF generation (ReportLab) | `build_pdf()`, `build_cover()`, `build_content()`, `build_styles()` |
| `build_quarterly_brief.py` | 855 | Quarterly strategic brief PDF | `build_pdf()`, `build_cover()`, `build_content()`, `build_styles()` |
| `quarterly_pdf_integration.py` | 738 | Adapter: consolidator output -> PDF builder | `ConsolidatedContentAdapter`, `build_quarterly_brief_from_consolidation()` |
| `generate_charts.py` | 281 | 6 matplotlib charts for reports | `chart_hamburg_fees()`, `chart_ppwr_grading()`, `chart_regulatory_timeline()`, etc. |
| `gap_analysis.py` | 322 | Self-audit for data quality | `run_audit()`, `AuditReport`, checks for wrong-jurisdiction refs, missing topics, hardcoded content |
| `sample_monthly_data.json` | 238 | Example quarterly consolidation input | 4 entries: PPWR, Hamburg-WW, VerpackDG, LkSG |

### Data Flow

```
                                     +--> FileSystemRegulationStore (regulatory_data/states/*.json)
                                     |
ScreeningSource(s) --> RegulatoryScreeningModule.run_monthly_screening()
                                     |
                                     +--> MonthlyChangelog --> FileSystemRegulationStore (regulatory_data/changelogs/*.json)
                                                          |
                                                          +--> build_monthly_report.py --> PDF
                                                          |
3x MonthlyChangelog --> QuarterlyConsolidator.consolidate()
                                     |
                                     +--> QuarterlySummary --> ConsolidatedContentAdapter --> build_quarterly_brief.py --> PDF
                                     |
                                     +--> QuarterlyOutputFormatter --> JSON + Markdown exports
```

### Directory Structure

```
visusta/
  regulatory_screening.py          # Core engine
  quarterly_consolidator.py        # Quarterly aggregation
  build_monthly_report.py          # Monthly PDF
  build_quarterly_brief.py         # Quarterly PDF
  quarterly_pdf_integration.py     # Adapter layer
  generate_charts.py               # Chart generation
  gap_analysis.py                  # Self-audit tool
  sample_monthly_data.json         # Example input
  regulatory_data/
    states/                        # Monthly screening snapshots (YYYY-MM.json)
    changelogs/                    # Generated changelogs (YYYY-MM.json)
    audits/                        # Gap analysis output
  charts/                          # Generated chart PNGs
```

### Data Models (4 Layers)

**Layer 1 -- Input** (`regulatory_screening.py:83-123`)
```python
@dataclass
class ScreeningInputItem:
    regulation_id: str
    title: str
    topic: TopicCategory          # GHG | PACKAGING | WATER | WASTE | SOCIAL_HUMAN_RIGHTS
    description: str
    requirements_summary: str
    current_status: RegulationStatus  # LAW_PASSED | AMENDMENT_IN_PROGRESS | ...
    effective_date: Optional[date]
    enforcement_date: Optional[date]
    geographic_scope: GeographicScope  # GLOBAL | REGIONAL | NATIONAL | STATE | LOCAL
    applicable_countries: List[str]
    confidence_score: float
    # ... more fields
```

**Layer 2 -- Change Detection** (`regulatory_screening.py:139-209`)
```python
@dataclass
class ChangelogEntry:
    regulation_id: str
    change_type: ChangeType       # NEW_REGULATION | STATUS_PROMOTED_TO_LAW | TIMELINE_UPDATED | ...
    severity: ChangeSeverity      # CRITICAL | HIGH | MEDIUM | LOW | INFO
    changes: List[ChangeDetail]   # field-level diffs
    action_required: Optional[str]

@dataclass
class MonthlyChangelog:
    new_regulations: List[ChangelogEntry]
    status_changes: List[ChangelogEntry]
    content_updates: List[ChangelogEntry]
    # ... 7 categorized lists
    topic_change_statuses: Dict[TopicCategory, TopicChangeStatus]  # The required monthly deliverable
    executive_summary: str
```

**Layer 3 -- Quarterly Consolidation** (`quarterly_consolidator.py:121-360`)
```python
@dataclass
class ChangeLogEntry:          # NOTE: Different class, same-ish name. See Risk #2 below.
    id: str
    regulation_code: str
    impact_level: ImpactLevel  # CRITICAL | HIGH | MEDIUM | LOW | NONE
    status: ChangeStatus       # DRAFT | PENDING | VALIDATED | SUPERSEDED | RETRACTED
    sources: List[SourceReference]
    milestones: List[TimelineMilestone]
    executive_summary: Optional[str]   # <-- LLM integration point
    action_items: List[str]            # <-- LLM integration point

@dataclass
class QuarterlySummary:
    regulations: List[ConsolidatedRegulation]
    themes: List[Dict]         # Cross-cutting strategic themes
    risk_assessment: Dict
    resource_implications: Dict
```

**Layer 4 -- PDF Output** (`build_monthly_report.py`, `build_quarterly_brief.py`)
- ReportLab `BaseDocTemplate` with cover + content page templates
- Custom `build_styles()` function defines all typography
- `pro_table()`, `callout_box()`, `status_badge()` reusable components
- Charts embedded as PNG images from `charts/` directory

---

## 3. Architecture & Extension Points

### Protocol-Based Abstractions (Already Implemented)

**ScreeningSource** (`regulatory_screening.py:262-267`)
```python
class ScreeningSource(Protocol):
    def fetch_screening_data(self, period: str) -> MonthlyScreeningInput:
        ...
```
Plug in new data sources here. The module aggregates from all registered sources, deduplicates by `regulation_id`, and keeps the highest-confidence entry.

**RegulationStore** (`regulatory_screening.py:250-259`)
```python
class RegulationStore(Protocol):
    def get_previous_state(self, period: str) -> MonthlyScreeningInput:
        ...
    def save_state(self, period: str, screening: MonthlyScreeningInput) -> None:
        ...
```
Swap `FileSystemRegulationStore` for a database-backed implementation here. The protocol requires only two methods.

### Narrative Generation Points (LLM Integration)

1. **`executive_summary` field on `MonthlyChangelog`** (`regulatory_screening.py:197`) -- Currently generated by `_generate_executive_summary()` at line 991, which produces a bullet-point summary. Replace with LLM call.

2. **`executive_summary` field on `ChangeLogEntry`** (`quarterly_consolidator.py:163`) -- Optional field, populated manually in sample data. This is where LLM-generated per-regulation narratives go.

3. **`action_items` field on `ChangeLogEntry`** (`quarterly_consolidator.py:164`) -- Currently manual. LLM can suggest action items based on regulation context.

4. **`_build_narrative()` in `QuarterlyConsolidator`** (`quarterly_consolidator.py:718-749`) -- Builds executive summaries and strategic implications from entry progression. Currently rule-based string concatenation. Prime target for LLM replacement.

### Configuration Extension Points

**Module config dict** (`regulatory_screening.py:429-438`)
```python
module = RegulatoryScreeningModule(
    store=store,
    config={
        "critical_enforcement_window_days": 90,
        "allowed_countries": ["EU", "DE"],
    }
)
```
Add new config options here. Currently supports `critical_enforcement_window_days` and `allowed_countries`.

**Topic and Geographic Enums** (`regulatory_screening.py:26-51`)
```python
class TopicCategory(Enum):
    GHG = "ghg"
    PACKAGING = "packaging"
    WATER = "water"
    WASTE = "waste"
    SOCIAL_HUMAN_RIGHTS = "social_human_rights"

class GeographicScope(Enum):
    GLOBAL = "global"
    REGIONAL = "regional"
    NATIONAL = "national"
    STATE = "state"
    LOCAL = "local"
```
Add new topics or geographic levels by extending these enums. The screening module iterates `TopicCategory` to ensure all topics are reported on.

### Branding Extension Points

**`build_styles()` in PDF builders** (`build_monthly_report.py:156-221`, `build_quarterly_brief.py:117-152`)
- All brand colors defined as module-level constants (lines 27-39 in both files)
- All paragraph styles, fonts, and spacing in one function
- Change branding by modifying these two locations

**Reusable PDF components:**
- `pro_table()` -- enterprise table with header styling and alternating rows
- `callout_box()` -- green-bordered callout with accent color parameter
- `status_badge()` -- colored badge for regulation status indicators

---

## 4. Gap Analysis & Build Plan

### Detailed Gap Table

| Capability | Current State | Client Expects | Priority | Effort | Approach |
|-----------|--------------|----------------|----------|--------|----------|
| Report narratives | Hardcoded Python strings in `build_monthly_report.py` (lines 411-419, 521-536, 591-607, etc.) | Dynamic, data-driven or LLM-generated | **P0** | M | Replace hardcoded text with Jinja2 templates; add Claude API fallback |
| Country/topic config | Python enums (`TopicCategory`, `GeographicScope`) + config dict | UI or config file management | **P0** | S | Extract to YAML config; validate on startup |
| Source management | JSON files on disk (`regulatory_data/states/`, `regulatory_data/changelogs/`) | Structured DB or management interface | **P1** | M | Implement `RegulationStore` protocol with SQLite/PG backend |
| Report generation | CLI scripts (`python build_monthly_report.py`) | API endpoint or simple web UI | **P1** | M | FastAPI wrapper around existing `build_pdf()` functions |
| Approval workflow | `status` field exists on `ChangeLogEntry` (DRAFT/PENDING/VALIDATED/SUPERSEDED/RETRACTED) but no enforcement | Review -> Approve -> Publish flow | **P1** | M | Add state machine enforcement; API endpoints for transitions |
| Prompt/narrative config | N/A | Editable prompt templates | **P1** | S | YAML-based prompt templates with variable interpolation |
| Frontend/dashboard | None | At minimum: config management UI | **P2** | L | Streamlit for speed; React if polish needed |
| Database | JSON files | PostgreSQL or SQLite for production | **P2** | M | SQLAlchemy models mirroring existing dataclasses |
| LLM integration | None | Claude API for narrative drafting | **P2** | M | Claude API wrapper with template fallback |
| Authentication | None | Basic auth for multi-user access | **P3** | S | FastAPI middleware; JWT tokens |
| Testing | None -- zero tests | Comprehensive test suite | **P0** | L | pytest; unit tests for change detection, integration tests for PDF |

### Dependency Graph

```
Config Files (P0) ----+
                       |
Narratives (P0) ------+--> Database (P2) --> Frontend (P2)
                       |
Tests (P0) -----------+
                       |
Source Mgmt (P1) -----+--> API (P1) --> Approval Workflow (P1)
                       |
LLM Integration (P2) -+--> Prompt Config (P1)
                       |
Auth (P3) ------------+--> Frontend (P2)
```

---

## 5. Sprint Plan

### Sprint 1 (Weeks 1-2): Foundation

| Task | Details | Effort | Owner |
|------|---------|--------|-------|
| Extract config to YAML | Move `TopicCategory`, `GeographicScope`, `allowed_countries`, `critical_enforcement_window_days`, brand colors to `config/visusta.yaml`. Validate on startup. | S | Backend |
| Replace hardcoded narratives with templates | Jinja2 templates for monthly report sections. Each section gets a template file under `templates/monthly/`. Data context passed from changelog. | M | Backend |
| Add test suite | pytest. Priority: `_compare_regulations()`, `_classify_change_type()`, `_calculate_severity()`, `_generate_changelog()`. Mock `FileSystemRegulationStore`. | L | Backend |
| Database persistence layer | New `SqliteRegulationStore` implementing `RegulationStore` protocol. Tables: `screening_states`, `changelogs`, `regulations`. Migration script. | M | Backend |
| Config file schema | JSON Schema or Pydantic model for config validation. Countries, topics, sources, thresholds, branding. | S | Backend |

**Sprint 1 deliverable:** System runs from config file instead of hardcoded values. Reports generated from templates. Core logic has test coverage. Data persists in SQLite.

### Sprint 2 (Weeks 3-4): Dynamic Reports

| Task | Details | Effort | Owner |
|------|---------|--------|-------|
| FastAPI report generation API | `POST /reports/monthly` (period, country, topics) -> PDF. `POST /reports/quarterly` (quarter, year) -> PDF. `GET /changelogs/{period}` -> JSON. | M | Backend |
| Parameterize PDF generation | `build_monthly_report.py` accepts period, country filter, topic filter as arguments instead of constants. Remove `SCREENING_PERIOD = "2026-02"` hardcoding. | M | Backend |
| LLM integration for narratives | Claude API wrapper. Input: changelog data context + prompt template. Output: executive summary, section narratives, action items. Retry + fallback to Jinja2 templates if API fails. | M | Backend |
| Prompt template management | Store prompt templates in `config/prompts/`. System prompt + data context + generation instructions. Editable without code changes. | S | Backend |

**Sprint 2 deliverable:** API-driven report generation. Claude generates narratives with template fallback. Reports parameterized by period/country/topic.

### Sprint 3 (Weeks 5-6): Management Layer

| Task | Details | Effort | Owner |
|------|---------|--------|-------|
| Source management CRUD | API endpoints for managing regulatory sources. `POST/GET/PUT/DELETE /sources`. Replaces manual JSON file management. | M | Backend |
| Approval workflow | State machine: `DRAFT -> REVIEW -> APPROVED -> PUBLISHED`. API endpoints for transitions. Only `APPROVED` entries appear in reports. Audit log for transitions. | M | Backend |
| Basic web UI | Configuration management: countries, topics, sources, thresholds. Report trigger + download. Approval queue. Streamlit recommended for speed. | L | Frontend |
| Country/radar setup wizard | Guided flow: select country -> select topics -> configure sources -> set thresholds -> generate first report. | M | Frontend |

**Sprint 3 deliverable:** Web-based configuration and report management. Approval workflow enforced. Source CRUD.

### Sprint 4 (Weeks 7-8): Polish & Handover

| Task | Details | Effort | Owner |
|------|---------|--------|-------|
| End-to-end testing | Test with client's real regulatory portfolio across all 5 topics. Validate change detection accuracy. | M | QA |
| Docker packaging | `Dockerfile` + `docker-compose.yml`. SQLite for single-user, PG for multi-user. Environment variable configuration. | S | Backend |
| Performance testing | Measure: PDF generation time, changelog processing time, LLM latency. Target: <10s for monthly report, <30s for quarterly. | S | Backend |
| Documentation | API docs (auto-generated from FastAPI). Deployment guide. Runbook for common operations. | M | Backend |
| Client knowledge transfer | Walkthrough sessions. Configuration guide. Troubleshooting guide. | M | PM |

**Sprint 4 deliverable:** Dockerized, tested, documented system ready for client deployment.

---

## 6. Technical Decisions Needed

| Decision | Options | Recommendation | Rationale |
|----------|---------|----------------|-----------|
| Database | PostgreSQL vs SQLite | **SQLite** for v1, PG if multi-user needed | Single-user system initially. Protocol-based store means we can swap later with zero change detection logic changes. |
| Frontend | Streamlit vs React vs API-only | **Streamlit** for Sprint 3, evaluate React for v2 | Python-native, fast to build, good enough for config management. Client can use API directly if they prefer. |
| LLM | Claude API vs OpenAI vs local | **Claude API** (Sonnet for drafts, Opus for final) | Best quality for regulatory text. Cost is negligible (~$0.01-0.05/section). Client provides their own API key. |
| Hosting | Client infra vs managed cloud | **Client's choice** -- we provide Docker | Package as container. Client deploys where they want. We provide docker-compose for local and cloud variants. |
| Config format | YAML vs JSON vs TOML | **YAML** | Human-readable, supports comments, widely understood. JSON for data interchange, YAML for config. |
| Template engine | Jinja2 vs Mako vs string.Template | **Jinja2** | Industry standard, good for both HTML-like templates and text generation. Already in most Python environments. |
| API framework | FastAPI vs Flask vs Django | **FastAPI** | Async, auto-docs, Pydantic integration, modern Python. |
| Testing | pytest vs unittest | **pytest** | Simpler syntax, better fixtures, widely adopted. |

---

## 7. LLM Integration Architecture

### Where to Add LLM Calls

```
1. Monthly Executive Summary
   regulatory_screening.py:991  _generate_executive_summary()
   Input:  MonthlyChangelog (topic summaries, critical actions, stats)
   Output: 2-3 paragraph executive summary

2. Per-Regulation Narrative (Quarterly)
   quarterly_consolidator.py:718  _build_narrative()
   Input:  List[ChangeLogEntry] for one regulation, sorted chronologically
   Output: executive_summary + strategic_implications strings

3. Action Item Suggestions
   regulatory_screening.py:1102  _suggest_action_for_new()
   regulatory_screening.py:1112  _suggest_action_for_change()
   Input:  ChangelogEntry + regulation context
   Output: Specific, actionable recommendation string

4. Quarterly Strategic Themes
   quarterly_consolidator.py:873  _extract_strategic_themes()
   Input:  List[ConsolidatedRegulation]
   Output: Cross-cutting theme identification + implications
```

### Prompt Template Structure

```yaml
# config/prompts/monthly_executive_summary.yaml
system: |
  You are a regulatory intelligence analyst specializing in EU and German
  sustainability frameworks for food manufacturers. Write for executive
  leadership. Be precise, cite specific regulations, and highlight
  actionable implications.

user: |
  Generate an executive summary for the {{period}} monthly regulatory
  screening report.

  SCREENING STATISTICS:
  - Total regulations tracked: {{total_tracked}}
  - New regulations: {{new_count}}
  - Changes detected: {{changes_count}} ({{critical_count}} critical)

  CRITICAL ACTIONS:
  {% for action in critical_actions %}
  - {{action.regulation_id}}: {{action.summary}} [{{action.severity}}]
  {% endfor %}

  PER-TOPIC STATUS:
  {% for topic, status in topic_statuses.items() %}
  - {{topic}}: {% if status.changed %}CHANGED ({{status.level}}){% else %}No change{% endif %}
  {% endfor %}

  Write 2-3 paragraphs. First paragraph: headline changes and their
  business impact. Second paragraph: topic-level overview. Third paragraph
  (if critical items exist): urgent actions required.
```

### Fallback Strategy

```python
async def generate_narrative(context: dict, prompt_name: str) -> str:
    """Generate narrative with LLM, falling back to template."""
    try:
        prompt = load_prompt_template(prompt_name)
        rendered = jinja2.Template(prompt.user).render(**context)
        response = await claude_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            system=prompt.system,
            messages=[{"role": "user", "content": rendered}],
            max_tokens=1024,
        )
        return response.content[0].text
    except Exception:
        # Fallback: Jinja2 template-only generation (no LLM)
        fallback = load_fallback_template(prompt_name)
        return jinja2.Template(fallback).render(**context)
```

### Cost Estimation

| Report Type | Sections Needing LLM | Est. Tokens (in+out) | Cost per Report |
|------------|---------------------|---------------------|-----------------|
| Monthly | Executive summary + 5 topic narratives | ~4,000 in + ~2,000 out | ~$0.02 (Sonnet) |
| Quarterly | Exec summary + per-regulation narratives (6-8) + themes | ~8,000 in + ~4,000 out | ~$0.05 (Sonnet) |
| Monthly (Opus quality) | Same | Same tokens | ~$0.20 |

Client provides their own API key. We build the integration; they pay per-use.

---

## 8. Risk Areas

### Risk 1: Hardcoded Content in PDF Builders (HIGH)

`build_monthly_report.py` has substantial hardcoded narrative content. Lines 411-419 (executive summary), 521-536 (Hamburg fees section), 591-607 (NRW circular economy), 631-646 (VerpackDG), 706-721 (LkSG). These are written as Python string literals, not generated from data.

**Impact:** Cannot generate reports for different periods without code changes.
**Mitigation:** Sprint 1 -- Replace with Jinja2 templates. The `build_content()` function (~420 lines) needs significant refactoring.

### Risk 2: Two Different ChangeLogEntry Dataclasses (MEDIUM)

- `regulatory_screening.py:139` -- `ChangelogEntry` (monthly change detection output)
- `quarterly_consolidator.py:121` -- `ChangeLogEntry` (quarterly consolidation input)

These have different field names, different enum types, and different semantics. The quarterly consolidator expects its own `ChangeLogEntry` with fields like `regulation_code`, `impact_level`, `sources`, `milestones`. The monthly screener produces `ChangelogEntry` with `regulation_id`, `severity`, `change_type`.

**Impact:** No automated pipeline from monthly output to quarterly input. Manual data transformation required.
**Mitigation:** Sprint 1 -- Unify into a single model or build an explicit adapter. The `quarterly_pdf_integration.py` adapter partially bridges this but doesn't cover the data model mismatch.

### Risk 3: No Test Suite (HIGH)

Zero tests. The change detection logic (`_compare_regulations`, `_classify_change_type`, `_calculate_severity`) is complex with many edge cases (12 change types, 5 severity levels, status transition rules). Refactoring without tests is dangerous.

**Impact:** Any modification risks breaking change detection accuracy.
**Mitigation:** Sprint 1 -- Write tests before refactoring. Priority test targets:
- `_compare_regulations()` -- field-by-field comparison
- `_classify_change_type()` -- priority-based classification with 12 possible outputs
- `_calculate_severity()` -- conditional severity assignment
- `_generate_changelog()` -- full workflow with new/changed/removed/carried-forward entries
- `QuarterlyConsolidator.consolidate()` -- validation + grouping + conflict resolution

### Risk 4: PDF Generation Tightly Coupled (MEDIUM)

The PDF builders directly construct ReportLab flowables with hardcoded column widths, spacings, and content. `build_content()` in `build_monthly_report.py` is a single 420-line function mixing data, layout, and content.

**Impact:** Adding new sections, changing layout, or supporting different report formats requires deep changes.
**Mitigation:** Sprint 1 -- Introduce a report content model (list of typed sections) that the PDF builder consumes. Decouple "what to show" from "how to render it."

### Risk 5: Client Expectations Gap (HIGH)

Current state: engineering toolkit requiring Python knowledge to operate.
Client expects: product-like experience with config UI, approval workflows, and polished reports.

**Impact:** Client demos require significant preparation. Any config change requires a developer.
**Mitigation:** Sprint 2 (API) + Sprint 3 (UI) close this gap. Manage expectations on timeline.

### Risk 6: Confidence Score Calculation Assumes "Today" (LOW)

`ChangeLogEntry.calculate_confidence_score()` at `quarterly_consolidator.py:166-201` uses `date.today()` for age calculation. This means the same entry produces different confidence scores on different days, making test results non-deterministic.

**Impact:** Flaky tests, inconsistent validation results across runs.
**Mitigation:** Inject a reference date parameter. Minor fix but worth noting.

---

## 9. Deployment & Operations

### Current Setup

```bash
# Clone and install
git clone <repo>
cd visusta
python -m venv .venv
source .venv/bin/activate
pip install reportlab matplotlib

# Generate charts
python generate_charts.py

# Run monthly screening (creates regulatory_data/)
python regulatory_screening.py

# Build monthly PDF
python build_monthly_report.py

# Build quarterly PDF
python build_quarterly_brief.py

# Run gap analysis
python gap_analysis.py
```

### Target Docker Setup (Sprint 4)

```dockerfile
FROM python:3.14-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Config from environment or mounted volume
ENV VISUSTA_CONFIG=/app/config/visusta.yaml
ENV VISUSTA_DB_URL=sqlite:///data/visusta.db

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
services:
  visusta:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./output:/app/output
    environment:
      - VISUSTA_CONFIG=/app/config/visusta.yaml
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

### Monitoring Recommendations

- **Logging:** Structured JSON logging (Python `logging` + `python-json-logger`). Log every screening run, every PDF generation, every LLM call.
- **Health check:** `GET /health` endpoint returning DB connectivity, last successful screening date, LLM API availability.
- **Alerting:** Notify if monthly screening hasn't run by the 5th of the month. Notify on LLM API failures (>3 consecutive).
- **Data backup:** SQLite file backup daily. For PG, standard pg_dump schedule.

### Dependencies (Current)

```
reportlab          # PDF generation
matplotlib         # Chart generation
# That's it. No other third-party dependencies.
```

### Dependencies (Target)

```
reportlab          # PDF generation
matplotlib         # Chart generation
fastapi            # API framework
uvicorn            # ASGI server
sqlalchemy         # Database ORM
alembic            # DB migrations
jinja2             # Template engine
anthropic          # Claude API client
pyyaml             # Config parsing
pydantic           # Data validation
pytest             # Testing
httpx              # Test client
```

---

## 10. Team Allocation Recommendation

| Role | Allocation | Sprint Coverage | Key Responsibilities |
|------|-----------|----------------|---------------------|
| Backend Engineer (Python, FastAPI, DB) | Full-time | Sprints 1-4 | Config extraction, DB layer, API, LLM integration, template engine |
| Frontend Engineer (Streamlit or React) | 50% | Sprint 3-4 | Config UI, approval queue, report download, setup wizard |
| PM | Throughout | Sprints 1-4 | Client comms, sprint planning, acceptance criteria, demo prep |
| Designer | Spot | Sprint 1 (templates) + Sprint 3 (UI) | PDF template design, Streamlit/React UI design |
| Sankalp | Architecture oversight | Throughout | Architecture decisions, client comms, code review, technical direction |

### Onboarding Path for New Engineers

1. Read this document
2. Run the example workflow: `python regulatory_screening.py`
3. Read `regulatory_screening.py` top-to-bottom -- focus on `RegulatoryScreeningModule.run_monthly_screening()` (line 442)
4. Read `quarterly_consolidator.py` -- focus on `QuarterlyConsolidator.consolidate()` (line 601)
5. Generate a PDF: `python generate_charts.py && python build_monthly_report.py`
6. Open the PDF and trace each section back to the code
7. Run `python gap_analysis.py` and read the output
8. Read `sample_monthly_data.json` to understand the quarterly input format

---

## Appendix: Key Line References

Quick-reference for the most important code locations:

| What | File | Line |
|------|------|------|
| ScreeningSource protocol | `regulatory_screening.py` | 262 |
| RegulationStore protocol | `regulatory_screening.py` | 250 |
| FileSystemRegulationStore | `regulatory_screening.py` | 274 |
| Main screening workflow | `regulatory_screening.py` | 442 |
| Change detection core | `regulatory_screening.py` | 524 |
| Field comparison | `regulatory_screening.py` | 600 |
| Change type classification | `regulatory_screening.py` | 675 |
| Severity calculation | `regulatory_screening.py` | 715 |
| Executive summary generation | `regulatory_screening.py` | 991 |
| Topic change status (monthly deliverable) | `regulatory_screening.py` | 911 |
| Confidence score calculation | `quarterly_consolidator.py` | 166 |
| Validation rules | `quarterly_consolidator.py` | 366 |
| Conflict resolution | `quarterly_consolidator.py` | 467 |
| Quarterly consolidation entry point | `quarterly_consolidator.py` | 601 |
| Narrative builder | `quarterly_consolidator.py` | 718 |
| PDF styles (monthly) | `build_monthly_report.py` | 156 |
| PDF content (monthly) -- hardcoded sections start here | `build_monthly_report.py` | 405 |
| PDF styles (quarterly) | `build_quarterly_brief.py` | 117 |
| PDF content (quarterly) -- hardcoded sections start here | `build_quarterly_brief.py` | 282 |
| Content adapter (consolidator -> PDF) | `quarterly_pdf_integration.py` | 68 |
| Brand color constants | `build_monthly_report.py` | 27 |
| Gap analysis auditor | `gap_analysis.py` | 277 |
