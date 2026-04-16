# Quarterly Regulatory Consolidation Workflow

## Overview

This document preserves the legacy workflow for consolidating 3 months of regulatory change logs into a strategic quarterly brief.

It should now be read next to the current MARS draft-first layer. The live app centers on templates, draft revisions, approvals, source proposals, keyword rules, DOCX checkpoints, and export jobs. The quarterly consolidation path remains useful history, but it is not the primary authoring flow in the current API.

## Architecture

```
┌──────────────────────┐
│ Monthly changelog    │
│ inputs / JSON / DB   │
└─────────┬────────────┘
          │
          ▼
┌──────────────────────────┐       ┌─────────────────────────────┐
│ Legacy quarterly         │       │ Current MARS draft layer    │
│ consolidation pipeline   │       │                             │
│ validation               │       │ templates → draft creation  │
│ aggregation              │       │ changelog + evidence input  │
│ conflict resolution      │       │ compose / translate         │
│ narrative synthesis      │       │ section approvals           │
└─────────┬────────────────┘       │ export jobs / DOCX import   │
          │                        └──────────┬──────────────────┘
          ▼                                   ▼
┌──────────────────────────┐       ┌─────────────────────────────┐
│ QuarterlySummary         │       │ Draft revision history      │
│ / strategic brief data   │       │ and export artifacts        │
└─────────┬────────────────┘       └──────────┬──────────────────┘
          │                                   │
          ▼                                   ▼
┌──────────────────────────┐       ┌─────────────────────────────┐
│ ReportLab PDF builder    │       │ DOCX immediate export       │
│ (legacy quarterly path)  │       │ PDF async, approval-gated   │
└──────────────────────────┘       └─────────────────────────────┘
```

## Key Components

### 1. Data Models (`quarterly_consolidator.py`)

#### ChangeLogEntry
The atomic unit of the consolidation workflow. Represents a single regulatory change observation from monthly tracking.

```python
@dataclass
class ChangeLogEntry:
    id: str                           # Unique identifier
    regulation_code: str              # e.g., "PPWR", "EUDR"
    regulation_name: str              # Full name
    reported_month: date              # Month this was reported
    change_date: date                 # When change occurred
    title: str                        # Short title
    description: str                  # Full description
    change_type: str                  # e.g., "deadline_change"
    scope: RegulationScope            # EU, DE, STATE, LOCAL
    impact_level: ImpactLevel         # CRITICAL, HIGH, MEDIUM, LOW
    affected_areas: List[str]         # e.g., ["Packaging", "R&D"]
    investment_type: InvestmentType   # CAPEX, OPEX, R&D, etc.
    status: ChangeStatus              # DRAFT, PENDING, VALIDATED
    sources: List[SourceReference]    # Citations
    milestones: List[TimelineMilestone]
    executive_summary: Optional[str]  # Pre-written narrative
    action_items: List[str]           # Specific actions
```

#### ConsolidatedRegulation
The output of consolidation for a single regulation across the quarter.

```python
@dataclass
class ConsolidatedRegulation:
    regulation_code: str
    regulation_name: str
    scope: RegulationScope
    impact_level: ImpactLevel         # Aggregated/resolved
    latest_status: str
    primary_deadline: Optional[date]  # Resolved from conflicts
    executive_summary: str            # Synthesized narrative
    strategic_implications: str       # Cross-cutting analysis
    key_developments: List[str]       # Chronological progression
    recommended_actions: List[Dict]
    investment_requirements: List[Dict]
    source_entries: List[str]         # IDs of source entries
    month_coverage: Set[str]          # Which months contributed
    confidence_trend: str             # improving/stable/declining
```

#### QuarterlySummary
The complete quarterly consolidation output.

```python
@dataclass
class QuarterlySummary:
    quarter: str                      # e.g., "Q1 2026"
    reporting_period: str             # e.g., "January - March 2026"
    regulations: List[ConsolidatedRegulation]
    themes: List[Dict]                # Cross-cutting themes
    risk_assessment: Dict
    resource_implications: Dict
    stats: Dict                       # Validation statistics
```

### 2. Validation Logic

#### ChangeValidator
Implements business rules for "validated" changes:

```python
validator = ChangeValidator(
    min_sources=2,              # Minimum reliable sources
    min_confidence=0.5,         # Minimum confidence score
    max_age_days=90             # Maximum entry age
)

is_valid, issues = validator.validate(entry)
```

**Validation Rules:**
1. **Source Count**: Minimum 2 independent sources
2. **Source Reliability**: Average reliability >= 0.6
3. **Confidence Score**: Composite score >= 0.5
4. **Not Retracted**: Status != RETRACTED
5. **Complete Description**: Minimum 50 characters
6. **Date Validity**: Entry age <= 90 days

**Confidence Score Calculation:**
```
confidence = (source_reliability * source_count_bonus * 0.5) +
             (status_score * 0.3) +
             (age_factor * 0.2)
```

### 3. Consolidation Rules

#### ConflictResolver
Handles conflicting information across months using resolution strategies:

| Conflict Type | Resolution Strategy |
|---------------|---------------------|
| **Deadlines** | Most recent validated deadline with highest confidence |
| **Status** | Status from most recent validated entry |
| **Impact** | Maximum impact (most conservative: CRITICAL > HIGH > MEDIUM > LOW) |
| **Description** | Longest description from validated entry (most complete) |

#### Narrative Synthesis
Transforms tracking entries into strategic narrative:

**Input:** Multiple monthly entries for PPWR

**Output:** ConsolidatedRegulation with:
- `executive_summary`: "PPWR evolved over the quarter: escalating from MEDIUM to CRITICAL priority."
- `strategic_implications`: "Requires CAPEX investment. Impacts: Packaging, R&D. Urgent: 180 days to deadline."
- `key_developments`: ["January: Date Confirmed", "February: Standard Published", "March: Guidance Updated"]

### 4. Output Structure

#### Supported quarterly report generation

The supported path is the existing pipeline entrypoint:

```python
from pipeline import generate_quarterly_pdf

pdf_path = generate_quarterly_pdf(
    client_id="gerold-foods",
    quarter="Q1",
    year=2026,
)
```

Older adapter-style integration notes referred to helper classes and wrapper
functions that are no longer part of the live codebase.

#### Current MARS draft and export flow

The live application does not generate quarterly briefs directly from this consolidation path. Instead:

1. A draft is created from a template version.
2. `POST /api/clients/{client_id}/drafts/{draft_id}/compose` creates a new revision from template sections, changelog entries, and evidence.
3. Sections can be edited, translated, and approved.
4. Export jobs are created from a draft revision.
5. DOCX exports complete immediately.
6. PDF exports are queued asynchronously and require the draft to be `approved` or already `exported`.
7. `POST /api/clients/{client_id}/drafts/{draft_id}/exports/import-docx` creates a new revision from an uploaded DOCX checkpoint.

## Workflow Steps

### Step 1: Data Collection (Monthly)

Each month, regulatory changes are captured as `ChangeLogEntry` records for the legacy consolidation pipeline. The current MARS draft composer also consumes changelog JSON files as draft input:

```json
{
  "id": "CHG-2026-015",
  "regulation_code": "PPWR",
  "regulation_name": "EU Packaging and Packaging Waste Regulation",
  "reported_month": "2026-02-01",
  "change_date": "2026-02-10",
  "title": "ZSVR 2025 Minimum Standard Published",
  "description": "...",
  "impact_level": "HIGH",
  "status": "VALIDATED",
  "sources": [...],
  "action_items": [...]
}
```

### Step 2: Validation

```python
validator = ChangeValidator()
results = validator.batch_validate(all_entries)

# Results:
# - valid: List[ChangeLogEntry]
# - invalid: List[{entry, issues}]
# - by_status: Count by status
# - by_regulation: Count by regulation
```

### Step 3: Aggregation

Group validated entries by `regulation_code`:

```python
by_regulation = {
    "PPWR": [entry_jan, entry_feb, entry_mar],
    "EUDR": [entry_jan, entry_mar],
    "VerpackDG": [entry_feb]
}
```

### Step 4: Consolidation Per Regulation

For each regulation group:

1. **Resolve Conflicts**: Apply `ConflictResolver` strategies
2. **Build Narrative**: Synthesize `executive_summary` and `strategic_implications`
3. **Extract Developments**: Create chronological `key_developments` list
4. **Consolidate Actions**: Deduplicate and prioritize `recommended_actions`
5. **Analyze Confidence**: Calculate `confidence_trend`

### Step 5: Current MARS Draft-First Layer

The live system uses the monthly changelog as an input artifact rather than a final reporting product.

Relevant current behaviors:

| Area | Current behavior |
|------|------------------|
| Templates | Drafts may reference a template version; if none is set, draft composition falls back to a default 3-section template. |
| Draft composition | Composing a draft creates a new revision, stores it as `current_revision_id`, and clears approvals. |
| Revisions | Revisions are sequential and are the unit exported to DOCX or PDF. |
| Approvals | Section approvals are stored per revision and roll the draft status toward `approval` and `approved`. |
| Exports | DOCX exports complete immediately. PDF exports are queued and only allowed on `approved` or `exported` drafts. |
| DOCX checkpoints | Imported DOCX files create a new revision and become the current revision. |
| Sources | Source proposals are reviewed separately through the source-proposals router. |
| Keywords | Keyword rules are client-scoped and can be previewed against sample text. |

### Step 5: Cross-Cutting Analysis

Extract strategic themes across all regulations:

```python
themes = [
    {
        "theme": "Regulatory Convergence",
        "description": "Multiple critical regulations requiring simultaneous compliance",
        "regulations": ["PPWR", "EUDR", "FCM"],
        "strategic_implication": "Prioritize integrated compliance programs"
    },
    {
        "theme": "Q2 Deadline Cluster",
        "description": "Multiple regulations with Q2 deadlines",
        "regulations": ["PPWR", "FCM"],
        "strategic_implication": "Resource allocation should prioritize Q2"
    }
]
```

### Step 6: PDF Generation

```python
# Transform to PDF format
adapter = ConsolidatedContentAdapter(summary, styles)

# Build story
story = []
story.extend(adapter.build_executive_summary())
story.extend(adapter.build_priority_matrix())
story.extend(adapter.build_regulation_sections())
# ... additional sections

# Generate PDF
doc.build(story)
```

## Transition from Tracking to Reporting

### Tracking Mode (Monthly)

**Characteristics:**
- Granular, detailed entries
- Source citations required
- Status tracking (DRAFT → PENDING → VALIDATED)
- Technical descriptions
- Individual action items
- Confidence scores calculated

**Example:**
```python
ChangeLogEntry(
    id="CHG-2026-015",
    title="ZSVR 2025 Minimum Standard Published",
    description="Detailed technical description...",
    status=ChangeStatus.VALIDATED,
    sources=[source1, source2],
    action_items=["Audit packaging", "Review suppliers"]
)
```

### Reporting Mode (Quarterly)

**Characteristics:**
- Strategic narrative synthesis
- Conflict resolution applied
- Executive summaries
- Cross-cutting themes
- Consolidated action priorities
- Confidence trends (improving/stable/declining)

## Current System Notes

- The current API exposes draft CRUD, compose, translate, section edit, chat, approval, source proposal, keyword, and export endpoints.
- Quarterly consolidation can still describe the legacy data model and reporting logic, but it should not imply that the live app emits quarterly brief PDFs directly from that pipeline.
- Treat DOCX export/import as revision checkpoints, not as a separate document management system.
- Treat PDF export as the final approval-gated output of a draft revision, not as a quarterly consolidator output.

**Example:**
```python
ConsolidatedRegulation(
    regulation_code="PPWR",
    executive_summary="PPWR evolved from MEDIUM to CRITICAL priority...",
    strategic_implications="Requires CAPEX + R&D investment...",
    key_developments=[
        "January: General application confirmed",
        "February: ZSVR standard published",
        "March: [development]"
    ],
    confidence_trend="improving"
)
```

### Transition Mapping

| Tracking Input | Transformation | Reporting Output |
|----------------|----------------|------------------|
| Multiple monthly entries | Aggregation + Conflict Resolution | Single consolidated regulation view |
| Individual action items | Deduplication + Prioritization | Top 5 recommended actions |
| Source citations | Reliability scoring | Confidence score + trend |
| Technical descriptions | Narrative synthesis | Executive summary |
| Isolated observations | Pattern recognition | Strategic themes |
| Raw deadlines | Conflict resolution | Primary deadline |

## Functions Reference

### Core Consolidation Functions

```python
# Main workflow entry point
def run_quarterly_consolidation(
    month1_entries: List[ChangeLogEntry],
    month2_entries: List[ChangeLogEntry],
    month3_entries: List[ChangeLogEntry],
    quarter: str,
    year: int
) -> QuarterlySummary

# Validation
def validate(entry: ChangeLogEntry) -> Tuple[bool, List[str]]
def batch_validate(entries: List[ChangeLogEntry]) -> Dict[str, Any]

# Conflict resolution
def resolve_conflict(
    entries: List[ChangeLogEntry],
    conflict_type: str
) -> Any

# Narrative synthesis
def build_narrative(entries: List[ChangeLogEntry]) -> Dict[str, str]
def extract_developments(entries: List[ChangeLogEntry]) -> List[str]
def analyze_confidence_trend(entries: List[ChangeLogEntry]) -> str
```

### Supported PDF Entry Point

```python
def generate_quarterly_pdf(
    client_id: str,
    quarter: str,
    year: int,
    changelogs: Optional[Dict[str, MonthlyChangelog]] = None,
    output_path: Optional[str] = None,
    preferences: Optional[Dict[str, Any]] = None,
) -> str
```

## Usage Example

```python
# 1. Load monthly data
from quarterly_consolidator import load_entries_from_json

jan_entries = load_entries_from_json("data/2026-01_changes.json")
feb_entries = load_entries_from_json("data/2026-02_changes.json")
mar_entries = load_entries_from_json("data/2026-03_changes.json")

# 2. Run consolidation
from quarterly_consolidator import run_quarterly_consolidation

summary = run_quarterly_consolidation(
    jan_entries, feb_entries, mar_entries,
    quarter="Q1",
    year=2026
)

# 3. Save intermediate outputs
from quarterly_consolidator import save_consolidation_output

files = save_consolidation_output(summary, "output/Q1_2026")
# Generates: consolidation_q1_2026.json, consolidation_q1_2026.md

# 4. Generate PDF via the supported pipeline entrypoint
from pipeline import generate_quarterly_pdf

pdf_path = generate_quarterly_pdf(
    client_id="gerold-foods",
    quarter="Q1",
    year=2026,
    output_path="output/Visusta_Quarterly_Q1_2026.pdf"
)
```

## Integration Points

### With Existing PDF Pipeline

The consolidation workflow integrates with `build_quarterly_brief.py` through:

1. **ContentAdapter**: Transforms data models to ReportLab flowables
2. **Style Compatibility**: Uses existing paragraph styles
3. **Component Reuse**: Leverages existing `pro_table()`, `callout_box()`, `status_badge()`
4. **Template Compatibility**: Uses existing page templates

### With Monthly Reports

Monthly reports feed into quarterly consolidation:

```
build_monthly_report.py → JSON export → quarterly_consolidator.py
```

Recommended: Add JSON export to monthly report generation:

```python
def export_monthly_to_json(entries: List[ChangeLogEntry], filepath: str):
    """Export monthly entries for quarterly consolidation."""
    with open(filepath, 'w') as f:
        json.dump([e.to_dict() for e in entries], f, indent=2)
```

## File Structure

```
visusta/
├── quarterly_consolidator.py         # Core consolidation logic
├── sample_monthly_data.json          # Example input format
├── QUARTERLY_CONSOLIDATION_WORKFLOW.md  # This document
├── build_quarterly_brief.py          # Existing PDF builder
├── build_monthly_report.py           # Existing monthly builder
└── charts/                           # Chart assets
```

## Quality Assurance

### Validation Checklist

Before quarterly brief publication:

- [ ] All entries have minimum 2 sources
- [ ] No RETRACTED entries included
- [ ] All CRITICAL impact entries have confirmed deadlines
- [ ] Narrative synthesized for all regulations
- [ ] Confidence trend calculated
- [ ] Duplicate actions removed
- [ ] Cross-cutting themes identified
- [ ] PDF renders without errors

### Confidence Thresholds

| Use Case | Minimum Confidence | Rationale |
|----------|-------------------|-----------|
| Executive summary | 0.7 | High confidence for narrative claims |
| Deadline commitments | 0.8 | Deadline slippage is high risk |
| Investment decisions | 0.75 | Financial implications require certainty |
| Action items | 0.6 | Operational guidance can be provisional |

## Future Enhancements

1. **Database Integration**: Replace JSON files with SQL database
2. **API Integration**: Connect to regulatory data APIs
3. **Machine Learning**: Automated impact classification
4. **Version Control**: Track regulation changes over time
5. **Collaborative Review**: Multi-user validation workflow
6. **Automated Monitoring**: Scheduled re-validation of entries
