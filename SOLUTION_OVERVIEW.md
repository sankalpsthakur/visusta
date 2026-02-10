---
classification: CONFIDENTIAL
document: Solution Overview
version: 1.0
date: February 2026
prepared_by: visusta GmbH
---

<!-- visusta GmbH | visusta.ch | make visions real. -->

# Visusta ESG Regulatory Intelligence

**Solution Overview for Gerold and Team**

---

CONFIDENTIAL -- Prepared by visusta GmbH for internal use only.

---

## 1. Executive Summary

Visusta is a purpose-built ESG Regulatory Monitoring system that tracks legislative and regulatory changes across five core sustainability topics relevant to food manufacturing operations. The system continuously monitors the EU and German regulatory landscape, detects changes with a rule-based engine, and delivers structured, auditable reports on a monthly and quarterly cadence.

For your Hamburg and Rietberg facilities, the system currently tracks regulations across Greenhouse Gas emissions, Packaging, Water, Waste, and Social/Human Rights. It produces two primary deliverables:

- **Monthly Regulatory Impact Reports** (PDF, approximately 8 pages) -- technical changelogs with executive summaries, charts, and source references.
- **Quarterly Strategic Briefs** (PDF, approximately 11 pages) -- consolidated analysis with priority matrices, timeline visualizations, and investment guidance.

Every report is generated from structured data, validated against multiple sources, and fully traceable. There are no opaque AI-generated narratives, no cloud dependencies, and no recurring API costs. Your team retains 100% ownership of all data, source code, and generated outputs.

---

## 2. Solution Architecture

The system follows a linear data pipeline from regulatory sources through to published PDF reports. Each stage produces structured, inspectable artifacts.

```
                        VISUSTA DATA PIPELINE
 ===================================================================

 +---------------------+
 | Regulatory Sources   |   EU Official Journal, Bundesgesetzblatt,
 | (Government, Legal)  |   Hamburg.de, NRW state gazettes, IHK,
 +----------+-----------+   EUR-Lex, BAFA, ZSVR, legal analysis firms
            |
            v
 +---------------------+
 | Monthly Screening    |   Structured input (JSON):
 | Input                |   regulation_id, title, topic, status,
 +----------+-----------+   effective_date, geographic_scope, sources
            |
            v
 +---------------------+
 | Change Detection     |   Rule-based, field-by-field comparison:
 | Engine               |   12 change types, 5 severity levels,
 +----------+-----------+   confidence scoring, conflict resolution
            |
            v
 +---------------------+
 | Monthly Changelog    |   Structured output (JSON):
 | (Validated)          |   per-topic status, change entries,
 +----------+-----------+   executive summary, critical actions
            |
            v
 +----------+-----------+
 |                      |
 v                      v
 +-----------------+  +---------------------+
 | Monthly Report  |  | Quarterly           |
 | Generator       |  | Consolidator        |
 | (ReportLab)     |  | (3-month aggregate) |
 +--------+--------+  +----------+----------+
          |                      |
          v                      v
 +-----------------+  +---------------------+
 | Monthly PDF     |  | Quarterly PDF       |
 | Impact Report   |  | Strategic Brief     |
 | (~8 pages)      |  | (~11 pages)         |
 +-----------------+  +---------------------+

 -----------------------------------------------------------
 Quality Assurance Layer (runs at any stage):
 - Gap Analysis Auditor (jurisdiction checks, topic coverage)
 - Validation workflows (Draft -> Pending -> Validated)
 - Confidence scoring (min 2 sources, reliability weighting)
 -----------------------------------------------------------
```

---

## 3. Core Capabilities

### 3.1 ESG Topic Coverage

The system monitors five regulatory topic categories, each mapped to specific operational areas relevant to food manufacturing:

| Topic | Scope | Example Regulations |
|---|---|---|
| GHG (Greenhouse Gas) | Emissions reporting, carbon pricing, transition plans | CSRD, EU ETS, national GHG obligations |
| Packaging | Design for recycling, EPR, recycled content, minimization | PPWR, VerpackDG, EWKFondsG |
| Water | Wastewater fees, discharge limits, efficiency requirements | Hamburg municipal fees, EU Water Framework Directive |
| Waste | Circular economy, food waste, disposal requirements | NRW NKWS implementation, national waste hierarchy |
| Social / Human Rights | Supply chain due diligence, reporting, worker protections | LkSG, CSDDD, CSRD social standards |

### 3.2 Multi-Jurisdiction Monitoring

The system supports a hierarchical jurisdiction model:

| Level | Examples | Configuration |
|---|---|---|
| EU / Regional | EU PPWR, EUDR, CSRD, CSDDD | Applies to all Member State operations |
| German Federal | VerpackDG, LkSG, EWKFondsG | National regulations for all German facilities |
| German State | NRW Circular Economy Strategy, Hamburg state laws | State-specific requirements per facility location |
| Local / Municipal | Hamburg wastewater fees, municipal waste regulations | Site-specific requirements per facility |

Jurisdiction configuration is data-driven. Adding a new country, state, or municipality requires only a configuration update -- no code changes.

### 3.3 Automated Change Detection

The engine performs field-by-field comparison between monthly screening cycles and classifies every detected change into one of 12 change types:

| Change Type | Severity | Description |
|---|---|---|
| `NEW_REGULATION` | INFO / CRITICAL | First appearance in screening |
| `STATUS_PROMOTED_TO_LAW` | CRITICAL | Regulation enacted into law |
| `STATUS_ADVANCING` | HIGH | Moving from discussion to amendment phase |
| `LAW_BEING_AMENDED` | HIGH | Existing law under amendment |
| `TIMELINE_UPDATED` | MEDIUM / CRITICAL | Effective or enforcement dates changed |
| `CONTENT_UPDATED` | HIGH | Requirements or description modified |
| `METADATA_UPDATED` | LOW | Title, scope, or classification changed |
| `LAW_EXPIRED` | CRITICAL | Law reached end of life |
| `REGULATION_ENDED` | HIGH | Regulation repealed or superseded |
| `REGULATION_REMOVED` | HIGH | No longer found in screening sources |
| `NO_CHANGE` | INFO | No differences detected |
| `CARRIED_FORWARD` | INFO | Unchanged, carried to next period |

### 3.4 Severity-Based Prioritization

Every change is assigned one of five severity levels based on deterministic rules:

| Severity | Meaning | Example Trigger |
|---|---|---|
| CRITICAL | Immediate action required | Regulation promoted to law; enforcement date changed; imminent deadline |
| HIGH | Significant operational impact | Status advancing; content updated; regulation removed |
| MEDIUM | Plan accordingly | Timeline updated (non-enforcement); strategic alignment needed |
| LOW | Monitor | Metadata changes; minor administrative updates |
| INFO | Informational | New regulation under discussion; no change from prior period |

### 3.5 Confidence Scoring and Validation

Every change entry carries a confidence score (0.0 to 1.0) computed from three weighted factors:

| Factor | Weight | Calculation |
|---|---|---|
| Source reliability | 50% | Average reliability score of cited sources, scaled by source count (minimum 2 sources required) |
| Validation status | 30% | VALIDATED = 1.0, PENDING = 0.6, DRAFT = 0.3, SUPERSEDED = 0.2, RETRACTED = 0.0 |
| Information age | 20% | Linear decay over 90 days from change date |

---

## 4. Report Types

### 4.1 Monthly Regulatory Impact Report

**Format:** PDF, A4, approximately 8 pages
**Cadence:** Monthly
**Audience:** Regulatory affairs, operations, facility management

Each Monthly Impact Report contains:

| Section | Content |
|---|---|
| Cover Page | Branded cover with reporting period, classification, facility references |
| Executive Summary | Narrative overview of the month's most significant regulatory developments |
| Technical Screening Summary | Per-topic change/no-change status table, driven from the changelog JSON |
| Change Log Entries | Tabular listing of all detected changes with regulation ID, change type, and current status |
| Monthly Impact Overview | Severity-prioritized summary table with action items |
| Detailed Analysis Sections | In-depth coverage of individual regulations with tables, charts, and action callouts |
| Charts and Visualizations | Data-driven charts (fee adjustments, cost projections, levy comparisons) |
| References | Numbered source list with URLs and access dates |
| Disclaimer | Legal notice and data currency statement |

**Example content areas (February 2026):**
- Hamburg industrial wastewater and utility fee restructuring (+3.3%)
- German Packaging Law Implementation Act (VerpackDG) -- B2B EPR expansion
- LkSG reporting obligation abolition (retroactive)
- EWKFondsG single-use plastic fund data collection
- NRW Circular Economy Strategy alignment

### 4.2 Quarterly Strategic Brief

**Format:** PDF, A4, approximately 11 pages
**Cadence:** Quarterly
**Audience:** Executive leadership, board advisory, strategic planning

Each Quarterly Strategic Brief contains:

| Section | Content |
|---|---|
| Cover Page | Branded cover with quarter, strategic horizon, classification |
| Executive Summary | Medium-term strategic outlook synthesizing the quarter's developments |
| Quarterly Consolidation | Change log coverage table showing data availability across all 3 months |
| Per-Topic Consolidation | Highest observed change level per topic across the quarter |
| Regulatory Timeline | Gantt-style visualization of all compliance deadlines across the calendar year |
| Strategic Priority Matrix | Regulation-by-regulation priority table with deadlines, impact areas, and investment types |
| Deep-Dive Sections | Detailed analysis of each major regulation (PPWR, EUDR, CSRD, FCM, EmpCo) |
| Financial Impact | Consolidated cost driver table and capital investment requirements |
| Strategic Roadmap | Numbered action items with facility-specific recommendations |
| References | Full source bibliography |

**Cross-cutting analysis includes:**
- Regulatory convergence patterns (multiple deadlines clustering)
- Deadline clustering risk assessment
- Investment pattern analysis (CAPEX vs. OPEX vs. R&D)
- Confidence trend monitoring (improving, stable, declining)

---

## 5. Data Pipeline and Quality Assurance

### 5.1 Monthly Screening Workflow

```
Step 1: SCREENING INPUT
  Structured JSON with regulation entries covering all 5 topics
  (topics with no items are flagged, not omitted)

Step 2: CHANGE DETECTION
  Field-by-field comparison against previous month's state
  Classification into 12 change types with deterministic rules

Step 3: SEVERITY CLASSIFICATION
  Priority-ordered rules:
    Status changes > Timeline changes > Content changes > Metadata changes
  Enforcement date changes always escalate to CRITICAL

Step 4: CHANGELOG GENERATION
  Structured JSON output with:
    - Per-topic summaries and change statuses
    - Categorized change entries (new, status, content, timeline, ended, carried forward)
    - Critical action items
    - Executive summary narrative

Step 5: REPORT GENERATION
  Changelog JSON feeds directly into PDF builders (ReportLab)
  Charts generated from data (matplotlib)
```

### 5.2 Validation Rules

| Rule | Threshold | Purpose |
|---|---|---|
| Minimum source count | 2 sources per entry | Prevent single-source bias |
| Source reliability | Average >= 0.6 | Exclude low-quality sources |
| Confidence score | >= 0.5 for inclusion | Filter unreliable entries |
| Information age | <= 90 days | Ensure currency of data |
| Description completeness | >= 50 characters | Prevent empty or placeholder entries |
| Retraction check | Status != RETRACTED | Exclude withdrawn information |

### 5.3 Quarterly Consolidation

The quarterly consolidation engine aggregates three monthly changelogs and resolves conflicts:

| Conflict Type | Resolution Strategy |
|---|---|
| Deadline conflicts | Most recent validated deadline, weighted by confidence score |
| Status conflicts | Most recent validated entry |
| Impact assessment | Maximum impact level (most conservative) |
| Description conflicts | Longest description from a validated entry |

### 5.4 Gap Analysis Auditor

An automated audit module runs self-checks across the entire pipeline:

- **Wrong-jurisdiction detection:** Flags references to non-EU/DE jurisdictions (e.g., US municipal sources)
- **Topic coverage verification:** Ensures all 5 required topics are present in every screening cycle
- **Cross-jurisdiction validation:** Confirms all regulation entries have `applicable_countries` within scope
- **Reference quality:** Checks for URL presence and primary-source signals (EUR-Lex, Bundesgesetzblatt, parliamentary gazettes)
- **Data-driven builder verification:** Confirms PDF builders consume changelog JSON rather than hardcoded narratives

---

## 6. Configuration and Customization

The system is fully configurable through structured data files. No code changes are required for standard customizations.

| Configuration Area | Mechanism | Example |
|---|---|---|
| Country / jurisdiction | `allowed_countries` in config | `["EU", "DE"]` -- extensible to `["EU", "DE", "AT", "CH"]` |
| Topics monitored | `TopicCategory` enumeration | Add or remove ESG topics as needed |
| Severity rules | Configurable enforcement window | `critical_enforcement_window_days: 90` |
| Source reliability | Per-source reliability scores | Government gazettes: 1.0, legal analysis: 0.85 |
| Validation thresholds | `VALIDATION_MIN_SOURCES`, `CONFIDENCE_*_THRESHOLD` | Adjustable per deployment |
| Report branding | Brand colors, logos, footer text | Defined in report builder constants |
| Report templates | ReportLab page templates, styles, sections | Fully customizable PDF layout |

---

## 7. Human-in-the-Loop Controls

The system is designed around a human validation workflow. No report is published without explicit human oversight.

### 7.1 Validation Lifecycle

```
  DRAFT ----------> PENDING ----------> VALIDATED ----------> Published
    |                  |                    |
    |                  v                    |
    |              Manual Review            |
    |              (confidence check,       |
    |               source verification)    |
    |                                       |
    +------ RETRACTED (if found incorrect)  |
    |                                       |
    +------ SUPERSEDED (if newer info) -----+
```

### 7.2 Control Points

| Control | Description |
|---|---|
| Confidence thresholds | Entries below threshold are flagged for manual review |
| Manual override | Analysts can promote, demote, or retract any entry |
| Review-before-publish | Reports are generated in draft; human approval required before distribution |
| Critical action flagging | CRITICAL and HIGH severity entries are surfaced for immediate attention |
| Data quality monitoring | Gap analysis auditor flags missing topics, jurisdictions, or references |
| Source verification | Minimum 2-source requirement ensures no single-source reliance |

---

## 8. Data Ownership and Security

| Principle | Implementation |
|---|---|
| 100% client data ownership | All data, reports, source code, and generated artifacts belong to the client |
| No cloud dependencies | System runs entirely on local infrastructure; no external API calls required |
| No telemetry | No usage data, analytics, or telemetry is collected or transmitted |
| No data retention by visusta | Upon project handover, visusta retains no copies of client data |
| File-based storage | All state is stored as JSON files on the local filesystem |
| Infrastructure control | Runs on client-managed infrastructure; no third-party hosting |
| Access control | Only authorized team members have access to the system and its outputs |

---

## 9. Technology and Long-Term Costs

### 9.1 Technology Stack

| Component | Technology | License | Recurring Cost |
|---|---|---|---|
| Core language | Python 3.x | PSF (open source) | Free |
| PDF generation | ReportLab | BSD (open source) | Free |
| Chart generation | matplotlib | PSF (open source) | Free |
| Data models | Python dataclasses + JSON | Built-in | Free |
| Storage | File system (JSON) | N/A | Free |
| Version control | Git | GPL (open source) | Free |

### 9.2 Cost Structure

| Cost Category | Amount | Notes |
|---|---|---|
| Software licenses | EUR 0 | All components are open-source with permissive licenses |
| Cloud hosting | EUR 0 | Runs on local infrastructure |
| API costs (LLM, SaaS) | EUR 0 | No external API dependencies |
| Vendor lock-in risk | None | Standard Python; any developer can maintain or extend |
| Data egress / storage fees | EUR 0 | All data stored locally |

The system has been intentionally designed with zero recurring technology costs. There are no subscription fees, no per-query charges, no cloud compute bills, and no vendor lock-in. Any Python developer familiar with standard libraries can maintain and extend the system.

---

## 10. Engagement Structure

| Phase | Timeline | Activities | Deliverables |
|---|---|---|---|
| **Phase 1: Onboarding and Configuration** | Weeks 1--2 | Requirements alignment, jurisdiction configuration, source identification, topic validation | Configured system, validated source list, initial screening data |
| **Phase 2: Showcase Delivery** | Weeks 3--4 | First monthly report generation, quarterly brief template, chart generation, review cycle | First Monthly Impact Report (PDF), first Quarterly Strategic Brief (PDF), review session |
| **Phase 3: Iteration and Handover** | Weeks 5--8 | Refinements based on feedback, documentation completion, knowledge transfer, code handover | Final report templates, complete Git repository, build instructions, knowledge transfer sessions |
| **Phase 4: Support Period** | 90 days from acceptance | Bug fixing, debugging, configuration assistance | Issue resolution, configuration guidance |

---

## 11. Handover and Deliverables

Upon project completion, the client receives:

| Deliverable | Description |
|---|---|
| Complete Git repository | Full version history, all branches, all commits |
| Source code | All Python modules: screening engine, change detection, report builders, chart generators, consolidation engine, gap analysis auditor, PDF integration |
| Data schemas | JSON schemas for screening input, changelog output, consolidation data |
| Documentation | Build instructions, workflow guides, configuration reference |
| Example data | Sample monthly screening data, example changelogs, example consolidated outputs |
| Generated reports | All PDF reports produced during the engagement |
| Knowledge transfer | Recorded or live sessions covering architecture, workflows, and extension patterns |

---

## 12. Support Model

### 12.1 Support Period

A 90-day support period begins upon formal acceptance of the showcase delivery.

### 12.2 Scope

| In Scope | Out of Scope |
|---|---|
| Bug fixes in delivered code | New feature development |
| Debugging of pipeline issues | Additional jurisdiction onboarding beyond initial scope |
| Configuration assistance | Ongoing regulatory research or screening |
| Clarification of documentation | Integration with third-party systems not in original scope |
| Minor adjustments to report templates | Fundamental architecture changes |

### 12.3 Communication

| Element | Detail |
|---|---|
| Dedicated contact | Assigned project manager from visusta GmbH |
| Response time | Agreed upon at contract signing (recommended: 2 business days for non-critical, same day for critical) |
| Communication channel | As agreed (email, dedicated channel, or project management tool) |
| Issue tracking | Structured issue reporting via Git or agreed tool |

---

## 13. Payment Structure

| Milestone | Percentage | Trigger |
|---|---|---|
| Contract signing | 30% | Project kickoff |
| Showcase delivery and acceptance | 40% | Client acceptance of Phase 2 deliverables |
| Completion of support/debugging phase | 30% | End of 90-day support period |

---

## 14. Legal

| Term | Detail |
|---|---|
| **Data ownership** | 100% client ownership of all data, reports, source code, and generated artifacts from the first day of the engagement |
| **Intellectual property** | Full IP transfer to client upon final payment |
| **Governing law** | Swiss law, jurisdiction of Zurich |
| **Termination** | Either party may terminate after the showcase phase (Phase 2) if project objectives are not met, with payment only for completed phases |
| **Confidentiality** | All project materials, client data, and deliverables are treated as confidential |
| **Data processing** | No client data is processed outside of client-controlled infrastructure |

---

*This document is confidential and intended solely for the use of the intended recipient. Unauthorized distribution is prohibited.*

*visusta GmbH -- visusta.ch -- make visions real.*
