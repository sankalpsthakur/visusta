# Architecture

Visusta ESG Regulatory Intelligence Platform.

---

## System Identity

Purpose-built regulatory monitoring system for EU/German food manufacturers. Tracks legislative changes across 5 ESG topics (GHG, Packaging, Water, Waste, Social/Human Rights) for Hamburg and Rietberg facilities. Produces monthly impact reports and quarterly strategic briefs as auditable PDFs.

Zero cloud dependencies. Zero recurring API costs. Deterministic rule-based engine. Full client ownership of data, source code, and outputs.

---

## Architecture Overview

```
                     VISUSTA PLATFORM ARCHITECTURE
 ====================================================================

 ┌─────────────────────────────────────────────────────────────────┐
 │                    DELIVERY LAYER                               │
 │  app.py (Streamlit)  │  api/main.py (FastAPI)  │  CLI scripts  │
 └────────────┬─────────┴──────────┬──────────────┴───────┬───────┘
              │                    │                      │
 ┌────────────▼────────────────────▼──────────────────────▼───────┐
 │                    ORCHESTRATION LAYER                          │
 │  pipeline.py — 4 entry points:                                 │
 │    run_monthly_pipeline    generate_monthly_pdf                 │
 │    run_quarterly_pipeline  generate_quarterly_pdf               │
 └──────┬──────────────┬──────────────┬───────────────────────────┘
        │              │              │
 ┌──────▼──────┐ ┌─────▼─────┐ ┌─────▼──────────────────────────┐
 │  MONTHLY    │ │  ADAPTER  │ │  QUARTERLY                     │
 │  PIPELINE   │ │  LAYER    │ │  PIPELINE                      │
 │             │ │           │ │                                 │
 │ regulatory_ │ │ models.py │ │ quarterly_consolidator.py       │
 │ screening.py│ │ Monthly→Q │ │  ├─ ChangeValidator             │
 │  ├─ Screen  │ │ mapping   │ │  ├─ ConflictResolver            │
 │  ├─ Detect  │ │ tables    │ │  ├─ QuarterlyConsolidator       │
 │  ├─ Classify│ │           │ │  └─ QuarterlyOutputFormatter    │
 │  └─ Persist │ │           │ │                                 │
 └──────┬──────┘ └───────────┘ └──────┬──────────────────────────┘
        │                             │
 ┌──────▼─────────────────────────────▼──────────────────────────┐
 │                    REPORT GENERATION                           │
 │  build_monthly_report.py  │  build_quarterly_brief.py         │
 │  quarterly_pdf_integration.py                                  │
 │  report_engine.py (Jinja2)  │  generate_charts.py (matplotlib)│
 └──────┬─────────────────────────────┬──────────────────────────┘
        │                             │
 ┌──────▼─────────────────────────────▼──────────────────────────┐
 │                    PERSISTENCE LAYER                           │
 │  regulatory_data/states/{period}.json     (screening state)   │
 │  regulatory_data/changelogs/{period}.json (monthly changelog) │
 │  output/*.json, output/pdf/*.pdf          (generated reports) │
 │  charts/*.png                             (embedded visuals)  │
 └───────────────────────────────────────────────────────────────┘
        │
 ┌──────▼───────────────────────────────────────────────────────┐
 │                    CONFIGURATION                              │
 │  config/visusta.yaml — branding, validation, facilities      │
 │  config/__init__.py  — singleton loader, env override        │
 └──────────────────────────────────────────────────────────────┘
```

---

## Module Inventory

### Core Pipeline (6 files)

| Module | Lines | Responsibility |
|--------|-------|---------------|
| `regulatory_screening.py` | ~1400 | Monthly change detection. Compares current screening input against previous state. Produces categorized MonthlyChangelog (new_regulations, status_changes, content_updates, timeline_changes, metadata_updates, ended_regulations, carried_forward). 12 change types, 5 severity levels. |
| `quarterly_consolidator.py` | ~1500 | Quarterly aggregation engine. Validates entries (min 2 sources, 0.5+ confidence), resolves cross-month conflicts, deduplicates by regulation_code, extracts strategic themes, produces QuarterlySummary. |
| `models.py` | ~450 | Adapter layer bridging monthly and quarterly data models. MonthlyToQuarterlyAdapter maps severity->impact_level, geographic_scope->regulation_scope, change_type->string. JSON deserialization for changelog persistence. |
| `pipeline.py` | ~350 | Orchestrator. 4 public entry points connecting screening, adaptation, consolidation, and PDF generation. Handles file I/O and inter-module coordination. |
| `gap_analysis.py` | ~325 | Compliance auditor. Detects schema violations, jurisdiction errors, missing topic coverage, hardcoded narratives. Severity-rated findings (CRITICAL/HIGH/MEDIUM/LOW). |
| `generate_charts.py` | ~370 | Matplotlib chart generation. 6 regulatory visualizations at 200 dpi PNG for PDF embedding. |

### Report Generation (4 files)

| Module | Lines | Responsibility |
|--------|-------|---------------|
| `build_monthly_report.py` | ~1100 | ReportLab PDF builder for monthly impact reports (~8 pages). Brand-styled tables, executive summary, critical actions, topic sections. |
| `build_quarterly_brief.py` | ~1200 | ReportLab PDF builder for quarterly strategic briefs (~11 pages). Cover page, priority matrix, regulation sections, timeline, action roadmap. |
| `quarterly_pdf_integration.py` | ~800 | Bridge from QuarterlySummary to PDF flowables. ConsolidatedContentAdapter transforms data for ReportLab rendering. |
| `report_engine.py` | ~180 | Jinja2 template renderer. Renders narrative sections (executive_summary, critical_actions, coverage_intro) from templates/ directory. |

### Web/API Layer (3 files)

| Module | Lines | Responsibility |
|--------|-------|---------------|
| `app.py` | ~1100 | Streamlit dashboard. 6 pages: Dashboard, Monthly Report, Quarterly Brief, Regulatory Data, Configuration, Audit. Metric cards, topic status, PDF download. |
| `api/main.py` | ~280 | FastAPI REST backend. 11 endpoints for changelogs, states, report generation, screening, topics, audit, health, config. |
| `api/schemas.py` | ~45 | Pydantic request/response models for API. |

### Supporting (2 files)

| Module | Lines | Responsibility |
|--------|-------|---------------|
| `build_capabilities_brief.py` | ~1100 | PDF generator: "Visusta Functionality and Output Guide" (~9 pages). Sales/onboarding artifact. |
| `build_capabilities_one_pager.py` | ~250 | Single-page landscape PDF: "Agent-Orchestrated Intelligence Dashboard." Sales collateral. |

---

## Data Model

### Monthly Domain (regulatory_screening.py)

```
MonthlyScreeningInput
  ├─ screening_period: str (YYYY-MM)
  ├─ regulations: List[ScreeningInputItem]
  ├─ topics_covered: List[TopicCategory]
  └─ data_quality_flags: List[str]

MonthlyChangelog
  ├─ screening_period, generated_date, previous_period
  ├─ new_regulations: List[ChangelogEntry]
  ├─ status_changes: List[ChangelogEntry]
  ├─ content_updates: List[ChangelogEntry]
  ├─ timeline_changes: List[ChangelogEntry]
  ├─ metadata_updates: List[ChangelogEntry]
  ├─ ended_regulations: List[ChangelogEntry]
  ├─ carried_forward: List[ChangelogEntry]
  ├─ critical_actions: List[ChangelogEntry]
  ├─ topic_summaries: Dict[str, TopicSummary]
  └─ topic_change_statuses: Dict[str, TopicChangeStatus]
```

**Enumerations:**
- TopicCategory: ghg, packaging, water, waste, social_human_rights
- RegulationStatus: law_passed, amendment_in_progress, change_under_discussion, proposed, expired, repealed
- ChangeType: 12 types (new_regulation, status_advancing, law_being_amended, timeline_updated, content_updated, metadata_updated, law_expired, regulation_removed, no_change, carried_forward, ...)
- ChangeSeverity: critical, high, medium, low, info
- GeographicScope: global, regional, national, state, local

### Quarterly Domain (quarterly_consolidator.py)

```
ChangeLogEntry (Quarterly)
  ├─ id, regulation_code, regulation_name, reported_month
  ├─ change_date, title, description, change_type
  ├─ scope: RegulationScope (EU/DE/STATE/LOCAL/INT)
  ├─ impact_level: ImpactLevel (CRITICAL/HIGH/MEDIUM/LOW/NONE)
  ├─ affected_areas: List[str]
  ├─ investment_type: InvestmentType (CAPEX/OPEX/R&D/AUDIT/IT/NONE)
  ├─ status: ChangeStatus (DRAFT/PENDING/VALIDATED/SUPERSEDED/RETRACTED)
  ├─ sources: List[SourceReference]
  ├─ milestones: List[TimelineMilestone]
  ├─ action_items: List[str]
  └─ confidence_score: float (calculated)

ConsolidatedRegulation
  ├─ regulation_code, entries: List[ChangeLogEntry]
  ├─ strategic_implications, key_developments
  ├─ recommended_actions, month_coverage
  └─ confidence_trend: str (improving/stable/declining)

QuarterlySummary
  ├─ consolidated_regulations: List[ConsolidatedRegulation]
  ├─ period, quarter, year
  ├─ month_entries: Dict[str, List[ChangeLogEntry]]
  └─ summary_statistics: Dict
```

### Adapter Bridge (models.py)

Monthly ChangelogEntry -> Quarterly ChangeLogEntry via MonthlyToQuarterlyAdapter:
- severity -> impact_level (critical->CRITICAL, high->HIGH, ...)
- geographic_scope -> regulation_scope (regional->EU, national->DE, ...)
- change_type enum -> string
- topic -> affected_areas list
- regulation_id -> quarterly ID format (CHG-{period}-{regulation_id})

### Confidence Scoring

Formula: `(50% source reliability) + (30% validation status) + (20% information age)`
- Source: average reliability * count bonus (capped)
- Status: VALIDATED=1.0, PENDING=0.6, DRAFT=0.3, RETRACTED=0.0
- Age: linear decay over max_age_days (90)

### Validation Rules

| Rule | Threshold | Source |
|------|-----------|--------|
| Min sources per entry | 2 | visusta.yaml |
| Source reliability | >= 0.6 | visusta.yaml |
| Confidence score | >= 0.5 | visusta.yaml |
| Max entry age | 90 days | visusta.yaml |
| Min description length | 50 chars | visusta.yaml |
| Conflict resolution: impact | Maximum across months | consolidator |
| Conflict resolution: deadline | Most recent confirmed | consolidator |
| Conflict resolution: status | Most recent | consolidator |
| Conflict resolution: description | Longest from validated | consolidator |

---

## Data Flow

```
RAW REGULATORY SOURCES (EU Official Journal, Bundesgesetzblatt, Hamburg.de, ...)
        │
        ▼
[Manual JSON input: ScreeningInputItem[]]
        │
        ▼
RegulatoryScreeningModule.run_monthly_screening()
  ├─ Normalize input (jurisdiction filter, topic coverage)
  ├─ Load previous state from FileSystemRegulationStore
  ├─ Diff: compare fields, classify change type, calculate severity
  ├─ Generate MonthlyChangelog (categorized by change type)
  └─ Persist state + changelog → regulatory_data/
        │
        ▼
[regulatory_data/changelogs/{period}.json]  ← immutable monthly artifact
        │
        ▼ (3 months accumulated)
        │
MonthlyToQuarterlyAdapter.adapt_changelog()
  ├─ Map enums (severity→impact, scope→regulation_scope)
  ├─ Generate quarterly IDs
  └─ Create TimelineMilestones from dates
        │
        ▼
QuarterlyConsolidator.consolidate()
  ├─ Validate entries (6 rules)
  ├─ Group by regulation_code
  ├─ Resolve conflicts across months
  ├─ Extract strategic themes
  └─ Generate QuarterlySummary
        │
        ▼
Report Generators (ReportLab + Jinja2 + matplotlib)
  ├─ Render templates (executive_summary, critical_actions)
  ├─ Build PDF flowables (tables, callouts, charts)
  └─ Output branded PDF
        │
        ▼
[output/pdf/*.pdf] + [output/*.json]
```

---

## Persistence

All persistence is file-based JSON. No database.

| Path | Content | Mutability |
|------|---------|-----------|
| `regulatory_data/states/{YYYY-MM}.json` | Screening state snapshot | Written once per month |
| `regulatory_data/changelogs/{YYYY-MM}.json` | Monthly changelog | Written once per month |
| `regulatory_data/audits/gap_analysis_report.md` | Audit output | Regenerated on demand |
| `output/*.json` | Structured report data | Regenerated per build |
| `output/pdf/*.pdf` | Final deliverable PDFs | Regenerated per build |
| `charts/*.png` | Chart assets (6 files) | Regenerated per build |
| `config/visusta.yaml` | System configuration | Manual edit |

---

## External Dependencies

| Package | Version | Role |
|---------|---------|------|
| reportlab | 4.4.9 | PDF generation (core deliverable) |
| matplotlib | 3.10.8 | Chart generation (6 regulatory visualizations) |
| numpy | 2.4.2 | Numeric backend for matplotlib |
| pandas | 3.0.2 | Data manipulation |
| pydantic | 2.12.5 | API schema validation |
| fastapi | 0.135.3 | REST API |
| jinja2 | (implicit) | Template rendering |
| streamlit | (implicit) | Web dashboard |
| freezegun | (dev) | Test date freezing |

---

## API Surface

### FastAPI Endpoints (api/main.py)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | System health + data directory status |
| `/config` | GET | Current visusta.yaml configuration |
| `/changelogs` | GET | List available changelog periods |
| `/changelogs/{period}` | GET | Fetch specific monthly changelog |
| `/states` | GET | List available state periods |
| `/states/{period}` | GET | Fetch specific state snapshot |
| `/reports/monthly` | POST | Generate monthly PDF (period param) |
| `/reports/quarterly` | POST | Generate quarterly PDF (quarter + year) |
| `/screening/run` | POST | Trigger regulatory screening |
| `/topics` | GET | List ESG topics |
| `/audit` | GET | Run gap analysis |

### Streamlit Pages (app.py)

Dashboard, Monthly Report, Quarterly Brief, Regulatory Data, Configuration, Audit.

---

## Test Coverage

**130 tests total** (pytest + freezegun at 2026-02-15)

| Test File | Count | Module |
|-----------|-------|--------|
| test_regulatory_screening.py | 69 | Monthly screening: comparison, classification, severity, changelog generation, normalization, storage, topic status |
| test_quarterly_consolidator.py | 55 | Quarterly: confidence scoring, validation, conflict resolution, consolidation, output formatting |
| test_build_capabilities_brief.py | 1 | PDF artifact: page count >= 9, section content |
| test_build_capabilities_one_pager.py | 1 | PDF artifact: exactly 1 page, key messaging |

**Fixtures** (conftest.py): Factory functions (make_screening_item, make_monthly_screening, make_source, make_changelog_entry) with defaults that pass validators by design.

**Not tested**: pipeline.py orchestration, API endpoints, Streamlit app, report_engine templates, generate_charts, gap_analysis, models.py adapter, end-to-end multi-quarter flows.

---

## Configuration

Singleton via `config.get_config()`. Override path: `VISUSTA_CONFIG` env var.

```yaml
# config/visusta.yaml structure
branding:
  colors: {primary_dark, primary, primary_light, accent, alert_red, alert_amber, ...}
screening:
  allowed_countries: ["EU", "DE"]
  critical_enforcement_window_days: 90
  required_topics: [ghg, packaging, water, waste, social_human_rights]
validation:
  min_sources: 2
  reliability_threshold: 0.6
  confidence_threshold: 0.5
  max_age_days: 90
  min_description_length: 50
report:
  facilities: ["Hamburg", "Rietberg"]
  screening_period: "2026-02"
  quarter_months: ["2026-01", "2026-02", "2026-03"]
  quarter_label: "Q1 2026"
```

---

## Known Constraints

1. **File-based persistence only** -- no database, no concurrent write safety
2. **Manual data ingestion** -- regulatory sources entered as JSON, not automated
3. **Two incompatible data models** -- MonthlyChangelogEntry vs QuarterlyChangeLogEntry bridged by adapter, not unified
4. **Some hardcoded narratives** -- executive summary sections in PDF builders contain static text alongside template-rendered content
5. **No authentication** -- API and dashboard have no auth layer
6. **No CI/CD** -- no pipeline configuration, no automated deployment
7. **Chart data is static** -- generate_charts.py produces fixed visualizations, not data-driven from changelogs
