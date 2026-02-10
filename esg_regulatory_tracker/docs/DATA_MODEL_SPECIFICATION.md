# ESG Regulatory Change Tracking System - Data Model Specification

## Overview

This document defines the data model for tracking ESG regulatory changes across five topics: GHG, Packaging, Water, Waste, and Social/Human Rights. The system supports monthly technical changelogs and quarterly consolidated reports with diff capabilities.

## Core Concepts

### 1. Regulation Identity

Each regulation has two identifiers:
- **`regulation_id`**: Persistent identifier that remains constant across all versions of a regulation (e.g., `GHG-EU-CSRD-2024`)
- **`change_id`**: Unique identifier for each specific change instance (UUID format, changes every month even for unchanged regulations)

### 2. Version Tracking

- **`version_sequence`**: Incremental version number (1 = new regulation, >1 = update)
- **`change_type`**: Classification relative to previous period:
  - `NEW`: First appearance in tracking system
  - `UPDATED`: Existing regulation with material changes
  - `UNCHANGED`: Carried forward from previous period with no changes
  - `DEPRECATED`: Regulation no longer in force

### 3. Reporting Periods

**Monthly Changelog** (`M-YYYY-MM`):
- Technical, granular tracking
- All changes (new, updated, unchanged) included
- Individual change records with full details
- Validation workflow status tracked

**Quarterly Report** (`Q-YYYY-QN`):
- Consolidated, validated summary
- Deduplicated regulations (one entry per `regulation_id`)
- Status evolution across three months
- Executive summaries and trend analysis

## Data Structures

### RegulatoryChange Entry (Single Change)

```json
{
  "change_id": "uuid",                    // Unique instance identifier
  "regulation_id": "GHG-EU-CSRD-2024",    // Persistent regulation identifier
  "version_sequence": 2,                  // Version number
  "topic": "GHG",                         // One of 5 topics
  "status": "Law Passed",                 // Status level
  "change_type": "UPDATED",               // NEW/UPDATED/UNCHANGED/DEPRECATED
  "jurisdiction": {                       // Geographic scope
    "country_code": "EU",
    "country_name": "European Union",
    "level": "International",
    "region": null
  },
  "title": "...",                         // Official title
  "description": "...",                   // Full description
  "effective_date": "2024-10-01",         // When effective
  "compliance_deadline": "2025-01-01",    // Compliance deadline
  "reporting_period": {                   // When tracked
    "year": 2024,
    "month": 9,
    "quarter": 3
  },
  "diff_from_previous": {                 // Only for UPDATED
    "previous_change_id": "uuid",
    "fields_changed": [...],
    "change_summary": "..."
  }
}
```

### Monthly Changelog

```json
{
  "report_id": "M-2024-09",
  "reporting_period": {
    "year": 2024,
    "month": 9,
    "quarter": 3
  },
  "summary": {
    "total_changes": 8,
    "new_regulations": 2,
    "updated_regulations": 2,
    "unchanged_regulations": 4,
    "by_topic": { "GHG": 2, ... },
    "by_status": { "Law Passed": 3, ... }
  },
  "changes": [...],         // Array of RegulatoryChange entries
  "diff_summary": {         // Changes since last month
    "has_changes": true,
    "added_count": 2,
    "modified_count": 1,
    "removed_count": 0,
    "highlights": [...]
  }
}
```

### Quarterly Consolidated Report

```json
{
  "report_id": "Q-2024-Q3",
  "reporting_period": {
    "year": 2024,
    "quarter": 3,
    "months_covered": [7, 8, 9]
  },
  "report_metadata": {
    "source_monthly_reports": ["M-2024-07", "M-2024-08", "M-2024-09"],
    "validation": {
      "validated_by": "analyst@visusta.com",
      "validation_status": "Approved"
    }
  },
  "executive_summary": {
    "overview": "...",
    "critical_alerts": [...],
    "trend_analysis": {...}
  },
  "consolidated_regulations": [
    {
      "regulation_id": "GHG-EU-CSRD-2024",
      "topic": "GHG",
      "current_status": "Law Passed",
      "quarterly_summary": {
        "first_appearance": "2024-01-15",
        "status_evolution": [
          { "month": 7, "status": "...", "change_id": "..." },
          { "month": 8, "status": "...", "change_id": "..." },
          { "month": 9, "status": "...", "change_id": "..." }
        ]
      },
      "monthly_sources": [...],
      "priority_score": 10,
      "action_required": "Immediate"
    }
  ],
  "topic_summaries": {      // Aggregated by topic
    "GHG": { "total_regulations": 2, ... },
    "Packaging": {...},
    ...
  }
}
```

## Change Detection Approach

### Monthly Diff Calculation

For each monthly changelog, compare against the previous month:

```python
def calculate_monthly_diff(current_month, previous_month):
    current_regulations = {c['regulation_id']: c for c in current_month['changes']}
    previous_regulations = {c['regulation_id']: c for c in previous_month['changes']}
    
    added = []
    modified = []
    unchanged = []
    removed = []
    
    # Check each regulation in current month
    for reg_id, change in current_regulations.items():
        if reg_id not in previous_regulations:
            change['change_type'] = 'NEW'
            added.append(change)
        elif has_material_changes(change, previous_regulations[reg_id]):
            change['change_type'] = 'UPDATED'
            change['diff_from_previous'] = compute_diff(change, previous_regulations[reg_id])
            modified.append(change)
        else:
            change['change_type'] = 'UNCHANGED'
            unchanged.append(change)
    
    # Check for removed regulations
    for reg_id, change in previous_regulations.items():
        if reg_id not in current_regulations:
            removed.append(change)
    
    return {
        'added': added,
        'modified': modified,
        'unchanged': unchanged,
        'removed': removed
    }
```

### Material Change Detection

A regulation is considered "UPDATED" if any of these fields differ:
- `status` (e.g., "Change Under Discussion" → "Law Passed")
- `effective_date` or `compliance_deadline`
- `description` (significant changes)
- `key_requirements` (added, removed, or modified)
- `title` (substantial changes, not just formatting)

Fields that do NOT trigger an update:
- `validation_status` (internal workflow)
- `recorded_at` (timestamp)
- Minor formatting in `description`

### Quarterly Consolidation

Monthly reports are consolidated quarterly:

1. **Deduplication**: Group by `regulation_id`
2. **Status Evolution**: Track status changes across three months
3. **Change Type Summary**:
   - If appeared in any month as `NEW` → "New this quarter"
   - If any month has `UPDATED` → "Updated this quarter"
   - If all months are `UNCHANGED` → "Stable"

## Topic Coverage

| Topic | Code | Description |
|-------|------|-------------|
| Greenhouse Gas | GHG | Emissions reporting, carbon pricing, climate disclosure |
| Packaging | PKG | EPR, recyclability, plastic bans, reuse requirements |
| Water | WTR | Conservation, water quality, extraction permits, ZLD |
| Waste | WST | Segregation, circular economy, hazardous waste |
| Social/Human Rights | SOC | Supply chain due diligence, labor rights, diversity |

## Status Levels

| Status | Description |
|--------|-------------|
| Law Passed | Enacted legislation with binding force |
| Amendment in Progress | Draft regulations or amendments under formal review |
| Change Under Discussion | Early stage proposals, consultations, white papers |

## Validation Workflow

```
Draft → Under Review → Validated → Published
```

- **Monthly**: Technical team records changes as "Draft" or "Under Review"
- **Quarterly**: Analysts validate and consolidate for executive reporting

## File Organization

```
esg_regulatory_tracker/
├── schemas/
│   ├── regulatory_change_schema.json    # Single entry schema
│   ├── monthly_changelog_schema.json    # Monthly report schema
│   └── quarterly_report_schema.json     # Quarterly report schema
├── examples/
│   ├── regulatory_changes_examples.json # Sample entries (all topics)
│   ├── monthly/
│   │   └── monthly_changelog_2024_09.json
│   └── quarterly/
│       └── quarterly_report_Q3_2024.json
└── docs/
    └── DATA_MODEL_SPECIFICATION.md      # This document
```

## PDF Generation Support

The data model supports PDF generation through:

1. **Hierarchical structure**: Executive summary → Topic summaries → Detail sections
2. **Priority scoring**: `priority_score` (1-10) indicates prominence in report
3. **Action classifications**: `action_required` field supports visual highlighting
4. **Rich metadata**: Sources, tags, and related regulations for appendices

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-10-01 | Initial data model specification |
