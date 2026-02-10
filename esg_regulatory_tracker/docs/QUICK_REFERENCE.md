# ESG Regulatory Tracker - Quick Reference

## Field Reference

### Required Fields (RegulatoryChange)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `change_id` | UUID | Unique instance ID | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| `regulation_id` | String | Persistent regulation ID | `GHG-EU-CSRD-2024` |
| `topic` | Enum | One of 5 topics | `GHG`, `Packaging`, `Water`, `Waste`, `Social/Human Rights` |
| `status` | Enum | Current status | `Law Passed`, `Amendment in Progress`, `Change Under Discussion` |
| `jurisdiction.country_code` | String | ISO 3166-1 alpha-2 | `EU`, `US`, `IN`, `GB`, `DE` |
| `jurisdiction.level` | Enum | Jurisdiction level | `Federal`, `State`, `Regional`, `International` |
| `title` | String | Official title | `Corporate Sustainability Reporting Directive` |
| `description` | String | Full description | `Updated technical implementation...` |
| `effective_date` | Date | When effective | `2024-10-01` |
| `reporting_period` | Object | Tracked period | `{year: 2024, month: 9, quarter: 3}` |
| `recorded_at` | DateTime | Timestamp | `2024-09-20T10:30:00Z` |

### Change Type Determination

| Scenario | `change_type` | `version_sequence` | Notes |
|----------|---------------|-------------------|-------|
| First appearance | `NEW` | 1 | New regulation_id in system |
| Material changes | `UPDATED` | >1 | Status, dates, requirements changed |
| No changes | `UNCHANGED` | same | Carried forward from previous month |
| Regulation expired | `DEPRECATED` | n/a | No longer in force |

### ID Patterns

| Report Type | Pattern | Example |
|-------------|---------|---------|
| Monthly | `M-YYYY-MM` | `M-2024-09` |
| Quarterly | `Q-YYYY-QN` | `Q-2024-Q3` |
| Regulation | `{TOPIC}-{CC}-{SHORTNAME}-{YEAR}` | `GHG-EU-CSRD-2024` |

## Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Monthly Data   │────▶│  Validation     │────▶│  Monthly Report │
│  Collection     │     │  & Review       │     │  (M-2024-09)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                              ┌────────────────────────┘
                              ▼
                    ┌─────────────────┐
                    │  Quarterly      │
                    │  Consolidation  │
                    └─────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Quarterly      │
                    │  Report         │
                    │  (Q-2024-Q3)    │
                    └─────────────────┘
```

## Topic Status Matrix

| Topic | Law Passed | Amendment in Progress | Change Under Discussion |
|-------|-----------:|----------------------:|------------------------:|
| GHG | CSRD (EU), Carbon Market (CN) | | GX League (JP) |
| Packaging | AGEC (FR), Simpler Recycling (UK) | SB 54 (CA-US) | |
| Water | | | Conservation Bill (IN) |
| Waste | Simpler Recycling (UK) | | |
| Social/Human Rights | | LkSG Expansion (DE) | Decent Work (BR) |

## Validation Checklist

### Before Saving Monthly Changelog

- [ ] `report_id` follows `M-YYYY-MM` pattern
- [ ] All `change_id` values are unique within report
- [ ] `change_type` correctly assigned based on previous month
- [ ] For `UPDATED` changes, `diff_from_previous` is populated
- [ ] Topic values match one of: GHG, Packaging, Water, Waste, Social/Human Rights
- [ ] Status values match one of: Law Passed, Amendment in Progress, Change Under Discussion
- [ ] Country codes are valid ISO 3166-1 alpha-2
- [ ] Dates are in ISO 8601 format (YYYY-MM-DD)

### Before Publishing Quarterly Report

- [ ] `report_id` follows `Q-YYYY-QN` pattern
- [ ] All three monthly reports referenced in `source_monthly_reports`
- [ ] Regulations deduplicated (one entry per `regulation_id`)
- [ ] `status_evolution` includes all three months
- [ ] `priority_score` calculated (1-10)
- [ ] Executive summary includes critical alerts for score >= 8
- [ ] Validation status is "Approved"

## Common Patterns

### Adding a New Regulation

```json
{
  "change_id": "uuid-v4-new",
  "regulation_id": "TOPIC-CC-NAME-YYYY",
  "version_sequence": 1,
  "topic": "GHG",
  "status": "Change Under Discussion",
  "change_type": "NEW",
  "diff_from_previous": null
}
```

### Updating an Existing Regulation

```json
{
  "change_id": "uuid-v4-new",
  "regulation_id": "EXISTING-REG-ID",
  "version_sequence": 2,
  "change_type": "UPDATED",
  "diff_from_previous": {
    "previous_change_id": "uuid-of-previous",
    "fields_changed": [
      {
        "field": "status",
        "old_value": "Change Under Discussion",
        "new_value": "Law Passed",
        "change_type": "modified"
      }
    ],
    "change_summary": "Status updated from draft to enacted"
  }
}
```

### Carrying Forward Unchanged

```json
{
  "change_id": "uuid-v4-new",
  "regulation_id": "EXISTING-REG-ID",
  "version_sequence": 1,  // same as previous
  "change_type": "UNCHANGED",
  "diff_from_previous": null
}
```

## Priority Score Guidelines

| Score | Criteria | Action Level |
|-------|----------|--------------|
| 10 | Immediate compliance required (< 6 months) | Immediate |
| 9 | Significant expansion of covered companies | Near-term |
| 8 | Major jurisdiction, medium-term deadline | Near-term |
| 7 | Important but longer timeline | Monitor |
| 6 | Discussion phase in major economy | Monitor |
| 5 | Limited scope or distant deadline | Monitor |
| 1-4 | Minor updates, informational | None |
