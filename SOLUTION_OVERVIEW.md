---
classification: CONFIDENTIAL
document: Solution Overview
version: 1.1
date: April 2026
prepared_by: visusta GmbH
---

<!-- visusta GmbH | visusta.ch | make visions real. -->

# Visusta ESG Regulatory Intelligence

**Solution Overview for Gerold and Team**

---

CONFIDENTIAL -- Prepared by visusta GmbH for internal use only.

---

## 1. Executive Summary

Visusta is a purpose-built ESG regulatory intelligence system for food manufacturers. It tracks legislative and regulatory change across five sustainability topics, detects month-over-month deltas with a rule-based screening engine, and produces auditable monthly and quarterly reports.

For Hamburg and Rietberg, the system covers Greenhouse Gas emissions, Packaging, Water, Waste, and Social / Human Rights. It produces two core deliverables:

- Monthly Regulatory Impact Reports for operational follow-up
- Quarterly Strategic Briefs for leadership planning

The platform now also includes MARS, a draft studio and app-state layer that manages locales, keywords, source proposals, templates, drafts, revisions, approvals, and exports. MARS gives the system a real working backend and user workflow, not just report generation scripts.

---

## 2. Solution Architecture

Visusta is built as a hybrid platform:

- the legacy pipeline continues to handle screening, changelog generation, charting, report rendering, and gap analysis
- MARS adds SQLite-backed application state and draft management
- the FastAPI backend exposes the system through client-scoped routes
- the Next.js frontend package provides the user interface layer

### Data Flow

1. Regulatory sources are collected and normalized into monthly screening input.
2. The screening engine compares the current month with the prior state.
3. The changelog is stored as an immutable monthly artifact.
4. The quarterly consolidator combines three months into a strategic view.
5. MARS manages templates, drafts, translations, approvals, and exports around that content.
6. PDFs and DOCX exports are generated from the approved draft state.

### Persistence Model

- Legacy screening artifacts remain in JSON on disk.
- MARS app state lives in `data/visusta.db`.
- Generated PDFs, DOCX files, and charts are written to output directories per client.

---

## 3. Core Capabilities

### ESG Topic Coverage

Visusta tracks five regulatory topic categories relevant to food manufacturing:

| Topic | Typical Coverage |
|---|---|
| GHG | Emissions reporting, carbon pricing, transition planning |
| Packaging | Recyclability, EPR, recycled content, minimization |
| Water | Wastewater fees, discharge limits, efficiency requirements |
| Waste | Circular economy, food waste, disposal requirements |
| Social / Human Rights | Supply chain due diligence, reporting, worker protections |

### Multi-Jurisdiction Monitoring

The system supports EU, German federal, German state, and municipal contexts. The locale catalog currently exposes 24 EU official languages, and client locale settings define the primary, enabled, and fallback locales for each tenant.

### Automated Change Detection

The monthly engine classifies field-level changes into deterministic buckets such as new regulation, status change, content update, timeline change, metadata update, expired law, removed regulation, no change, and carried forward.

### MARS Workflow

MARS adds the operational layer that makes the platform usable:

- locale settings
- keyword rules
- source proposals
- report templates and versions
- draft creation and revision history
- conversational draft editing
- translation and localization
- approval states
- PDF and DOCX exports

### LLM-Assisted Drafting

The platform includes an LLM interface for draft composition, translation, chat editing, and source suggestion. The current implementation uses deterministic stubs by default so the system remains testable and predictable.

---

## 4. Report Types

### Monthly Regulatory Impact Report

**Format:** PDF
**Cadence:** Monthly
**Audience:** Regulatory affairs, operations, facility management

Typical contents:

- cover page
- executive summary
- per-topic screening summary
- change log entries
- monthly impact overview
- detailed analysis sections
- charts and visualizations
- references and disclaimer

### Quarterly Strategic Brief

**Format:** PDF
**Cadence:** Quarterly
**Audience:** Executive leadership and board advisory

Typical contents:

- cover page
- executive summary
- quarterly consolidation table
- per-topic consolidation
- regulatory timeline
- strategic priority matrix
- deep-dive sections
- financial impact summary
- strategic roadmap
- references

### Draft Studio Output

MARS also supports draft-oriented deliverables:

- templates for report structure
- revisions for version control
- approval states for review workflows
- exports for PDF and DOCX handoff

---

## 5. Quality Assurance

Visusta now has a real test and verification surface:

- backend tests: `pytest -q tests/`
- frontend build: `cd frontend && npm run build`
- frontend E2E: `cd frontend && npx playwright test --reporter=line`

The verification surface covers the legacy screening and consolidation pipeline, the MARS database and API layers, the agents, and the export path.

---

## 6. Delivery Notes

- The system is local-first by default.
- Legacy JSON artifacts remain part of the current implementation.
- SQLite now powers the MARS state layer.
- LLM backends remain swappable.
- The frontend package exists as a separate Next.js workspace.
