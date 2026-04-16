# VISUSTA -- Internal Development Handover

**CLASSIFICATION: INTERNAL -- DEVELOPMENT TEAM ONLY**

Date: April 2026
Author: Sankalp (Architecture & Client Comms)
Status: Active development with working backend, MARS layer, and frontend package

---

## 1. Project Overview

### What Visusta Is

Visusta is a regulatory intelligence platform for food manufacturers. It tracks EU and German sustainability regulations across five topics, detects month-over-month changes, and produces monthly impact reports plus quarterly strategic briefs.

### Client Context

- Industry: food manufacturing
- Facilities: Hamburg and Rietberg, Germany
- Scope: EU, German federal, and German state-level regulations
- Cadence: monthly impact reports and quarterly strategic briefs
- Audience: executive leadership, regulatory affairs, and operations

### What We Sold

The deliverable is a working regulatory monitoring and reporting system that:

- ingests regulatory data from multiple sources
- detects changes against the previous month
- generates the monthly per-topic change/no-change deliverable
- consolidates three months into a quarterly strategic view
- produces branded PDFs with charts, tables, and references

### What Exists Today

This is no longer a prototype-only codebase. The repo now has:

- a FastAPI backend in `api/main.py`
- client-scoped API routers for locales, keywords, sources, templates, drafts, and exports
- a SQLite-backed MARS layer in `db/` and `mars/`
- LLM-backed agent hooks with deterministic `StubLLM` defaults
- a real pytest suite under `tests/`
- a Next.js frontend package with Playwright E2E coverage

---

## 2. Codebase Map

### Legacy Pipeline

- `regulatory_screening.py` handles monthly change detection and changelog generation
- `quarterly_consolidator.py` handles 3-month aggregation, validation, and conflict resolution
- `pipeline.py` orchestrates the monthly and quarterly entry points
- `build_monthly_report.py` and `build_quarterly_brief.py` render the PDF deliverables
- `generate_charts.py` creates the report charts
- `gap_analysis.py` audits topic coverage, jurisdiction scope, and narrative quality

### MARS Layer

- `db/connection.py` and `db/migrate.py` provide the SQLite app-state layer
- `mars/draft_lifecycle.py` enforces draft status transitions
- `mars/section_model.py` handles section serialization and diffing
- `mars/docx_import.py` and `mars/docx_export.py` handle DOCX round-tripping
- `mars/pdf_export.py` exports approved draft sections to PDF

### API Layer

- `api/main.py` is the FastAPI app factory
- `api/routers/clients.py` exposes the legacy client workflow
- `api/routers/locales.py` manages the locale catalog and client locale settings
- `api/routers/keywords.py` manages keyword rules and previews
- `api/routers/sources.py` manages source proposals
- `api/routers/templates.py` manages template CRUD and versions
- `api/routers/drafts.py` manages draft composition, translation, chat, and approvals
- `api/routers/exports.py` manages PDF/DOCX exports and DOCX import

### Agents

- `agents/llm.py` defines the LLM interface abstraction
- `agents/draft_composer.py` turns changelog and evidence data into draft sections
- `agents/translation_agent.py` localizes sections
- `agents/draft_chat.py` applies conversational edits to draft sections
- `agents/source_scout.py` proposes sources and stores evidence

### Frontend and Tests

- `frontend/` contains the Next.js package
- `frontend/e2e/` contains the Playwright specs
- `tests/` contains the backend, MARS, agent, and pipeline test coverage

---

## 3. Current Behavior

### Legacy Monthly and Quarterly Flow

The legacy pipeline still matters. It remains the source of truth for monthly screening output and quarterly consolidation.

1. Monthly screening produces a structured changelog and state snapshot.
2. Quarterly consolidation consumes three monthly changelogs and resolves conflicts.
3. PDF builders render the monthly report and quarterly brief.
4. Gap analysis audits the result set for coverage and narrative issues.

### MARS Behavior

MARS is the operational app layer around the reporting workflow.

- locale settings are stored per client
- keyword rules can be created, updated, previewed, and soft-deleted
- source proposals can be suggested and reviewed
- templates support versions, section updates, and theme updates
- drafts support revisions, composition, translation, chat, and approval state transitions
- exports support PDF and DOCX output

### LLM Integration

LLM integration is real, but it is still stubbed by default.

- the agents depend on `LLMInterface`
- `StubLLM` keeps local runs and tests deterministic
- production Claude/OpenAI implementations can be swapped in without changing the calling code

---

## 4. Operational Notes

### Backend Verification

- `pytest -q tests/`

This covers the legacy screening and consolidation pipeline, the MARS database and models, API integration, agent behavior, and the PDF export path.

### Frontend Verification

- `cd frontend && npm run build`
- `cd frontend && npx playwright test --reporter=line`

### API Entry Points

- `GET /api/health`
- `GET /api/clients`
- `GET /api/overview`
- `GET/POST` routes under `/api/clients/{client_id}/...`
- MARS routes for locales, keywords, source proposals, templates, drafts, and exports

---

## 5. Risks And Gaps

- No authentication is implemented yet.
- Some report narratives are still template- or string-driven.
- The LLM layer still uses `StubLLM` in local/test flows.
- The frontend source tree should be checked before page-level documentation changes.
- Legacy JSON artifacts still coexist with SQLite, so docs should always distinguish app state from screening artifacts.

---

## 6. Handoff Notes

- Keep the legacy pipeline docs and the MARS docs in sync.
- When a new API route is added, update both the router-level doc references and the tests.
- When a new report section or draft state is added, update the architecture doc, internal handover, and solution overview together.
- Do not describe the system as prototype-only anymore; it now has a working API, database, tests, and MARS workflow.
