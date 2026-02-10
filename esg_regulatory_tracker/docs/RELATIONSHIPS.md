# Data Model Relationships

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        QUARTERLY REPORT (Q-2024-Q3)                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ Executive       │  │ Consolidated    │  │ Topic Summaries │         │
│  │ Summary         │  │ Regulations[]   │  │ (5 topics)      │         │
│  └─────────────────┘  └────────┬────────┘  └─────────────────┘         │
│                                │                                         │
│           ┌────────────────────┼────────────────────┐                   │
│           │                    │                    │                   │
│           ▼                    ▼                    ▼                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ Monthly Sources │  │ Status Evolution│  │ Consolidated    │         │
│  │ (3 months)      │  │ (track changes) │  │ Details         │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
           ▼                        ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ MONTHLY REPORT   │    │ MONTHLY REPORT   │    │ MONTHLY REPORT   │
│ (M-2024-07)      │    │ (M-2024-08)      │    │ (M-2024-09)      │
│                  │    │                  │    │                  │
│ ┌──────────────┐ │    │ ┌──────────────┐ │    │ ┌──────────────┐ │
│ │ Changes[]    │ │    │ │ Changes[]    │ │    │ │ Changes[]    │ │
│ │ ┌──────────┐ │ │    │ │ ┌──────────┐ │ │    │ │ ┌──────────┐ │ │
│ │ │Change    │ │ │    │ │ │Change    │ │ │    │ │ │Change    │ │ │
│ │ │(RegChg)  │◀┼─┼────┼─┼▶│(RegChg)  │◀┼─┼────┼─┼▶│(RegChg)  │ │ │
│ │ └──────────┘ │ │    │ │ └──────────┘ │ │    │ │ └──────────┘ │ │
│ │ ┌──────────┐ │ │    │ │ ┌──────────┐ │ │    │ │ ┌──────────┐ │ │
│ │ │Change    │ │ │    │ │ │Change    │ │ │    │ │ │Change    │ │ │
│ │ │(RegChg)  │ │ │    │ │ │(RegChg)  │ │ │    │ │ │(RegChg)  │ │ │
│ │ └──────────┘ │ │    │ │ └──────────┘ │ │    │ │ └──────────┘ │ │
│ └──────────────┘ │    │ └──────────────┘ │    │ └──────────────┘ │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

## Key Relationships

### 1. Monthly → Monthly (Temporal)

```
M-2024-08.previous_report_id ──────▶ M-2024-07
M-2024-09.previous_report_id ──────▶ M-2024-08
```

**Purpose**: Enable month-over-month diff calculations

### 2. Monthly → Quarterly (Aggregation)

```
Q-2024-Q3.source_monthly_reports = ["M-2024-07", "M-2024-08", "M-2024-09"]
```

**Purpose**: Traceability from quarterly summaries to source data

### 3. Regulation → Regulation (Versioning)

```
GHG-EU-CSRD-2024 (v2)
  └─ diff_from_previous.previous_change_id ────▶ GHG-EU-CSRD-2024 (v1)
```

**Purpose**: Track evolution of individual regulations

### 4. Change → Change (Unchanged Carry-forward)

For unchanged regulations, the same `regulation_id` appears in consecutive months with:
- New `change_id` (unique per instance)
- Same `version_sequence`
- `change_type`: "UNCHANGED"
- `diff_from_previous`: null

### 5. Quarterly Consolidation → Monthly Sources

```json
{
  "regulation_id": "GHG-EU-CSRD-2024",
  "monthly_sources": [
    { "month": 7, "change_id": "uuid-jul", "change_type": "UNCHANGED" },
    { "month": 8, "change_id": "uuid-aug", "change_type": "UNCHANGED" },
    { "month": 9, "change_id": "uuid-sep", "change_type": "UPDATED" }
  ],
  "quarterly_summary": {
    "status_evolution": [
      { "month": 7, "status": "Law Passed", "change_id": "uuid-jul" },
      { "month": 8, "status": "Law Passed", "change_id": "uuid-aug" },
      { "month": 9, "status": "Law Passed", "change_id": "uuid-sep" }
    ]
  }
}
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA COLLECTION                              │
│  Research teams monitor regulatory sources across jurisdictions     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         MONTHLY PROCESSING                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ Identify    │─▶│ Classify    │─▶│ Diff vs     │─▶│ Generate   │ │
│  │ Changes     │  │ (NEW/UPDATE)│  │ Previous    │  │ M-YYYY-MM  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      QUARTERLY CONSOLIDATION                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ Aggregate   │─▶│ Deduplicate │─▶│ Validate    │─▶│ Generate   │ │
│  │ 3 Months    │  │ by Reg ID   │  │ & Review    │  │ Q-YYYY-QN  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PUBLICATION & DISTRIBUTION                      │
│  • PDF Report Generation                                            │
│  • API Access to JSON Data                                          │
│  • Alert Notifications for Critical Changes                         │
└─────────────────────────────────────────────────────────────────────┘
```

## Cross-Reference Matrix

### Regulation Relationships

Regulations can reference other regulations:

```json
"related_regulations": [
  {
    "regulation_id": "GHG-EU-NFRD-2014",
    "relationship_type": "Supersedes"
  },
  {
    "regulation_id": "GHG-EU-ETS-2023",
    "relationship_type": "Complements"
  }
]
```

**Relationship Types**:
- `Amends`: This regulation modifies the referenced one
- `Supersedes`: This regulation replaces the referenced one
- `Complements`: Works alongside the referenced regulation
- `Conflicts`: Potentially contradictory to the referenced regulation
- `References`: Cites or builds upon the referenced regulation

### Topic Distribution

Each regulation belongs to exactly one topic, but can have cross-topic impacts:

```json
{
  "topic": "Packaging",  // Primary topic
  "tags": ["plastic", "recycling", "epr", "waste-reduction"]  // Cross-topic tags
}
```

## Referential Integrity Rules

1. **regulation_id Consistency**: Same `regulation_id` always refers to the same regulation across all time periods

2. **change_id Uniqueness**: Each `change_id` appears in exactly one monthly report

3. **Monthly Continuity**: Every regulation in month N should either:
   - Appear in month N-1 (as UNCHANGED or UPDATED)
   - Be new (change_type: NEW)

4. **Quarterly Coverage**: Each quarterly report must reference exactly 3 monthly reports

5. **Status Validity**: Status transitions must follow logical flow:
   - `Change Under Discussion` → `Amendment in Progress` → `Law Passed`
   - (Reverse transitions possible for repeals)
