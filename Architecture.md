# Architecture

Visusta ESG Regulatory Intelligence Platform.

---

## System Identity

Visusta is a hybrid regulatory intelligence system for EU and German food manufacturers. The legacy monthly and quarterly pipeline still produces screening states, changelogs, charts, reports, and gap audits. MARS adds a SQLite-backed draft studio for locale settings, keywords, source proposals, templates, drafts, revisions, approvals, and exports. The backend is FastAPI, the frontend is a Next.js package with Playwright coverage, and LLM usage is abstracted behind stubbed agent interfaces so production Claude/OpenAI backends can be swapped in later.

---

## Stack At A Glance

- Legacy pipeline: `regulatory_screening.py`, `quarterly_consolidator.py`, `pipeline.py`, `build_monthly_report.py`, `build_quarterly_brief.py`, `generate_charts.py`, `gap_analysis.py`
- API layer: `api/main.py` plus routers for clients, locales, keywords, sources, templates, drafts, and exports
- MARS core: `db/`, `mars/`, and `agents/`
- Frontend: `frontend/` Next.js package with build and Playwright test tooling
- Persistence: legacy JSON artifacts plus SQLite app state

---

## Legacy Pipeline

The original pipeline still handles regulatory screening and report production.

- `regulatory_screening.py` compares the current month to the previous month and emits a categorized `MonthlyChangelog`
- `quarterly_consolidator.py` aggregates three monthly changelogs, validates entries, resolves conflicts, and produces a `QuarterlySummary`
- `models.py` bridges the monthly and quarterly schemas with explicit mapping logic
- `pipeline.py` orchestrates the screening and report-generation entry points
- `build_monthly_report.py` and `build_quarterly_brief.py` render the PDF deliverables
- `generate_charts.py` provides the chart assets embedded in reports
- `gap_analysis.py` audits jurisdiction coverage, topic coverage, and hardcoded content risks

The pipeline remains file-oriented for its core screening artifacts, which keeps the monthly output auditable and easy to inspect.

---

## MARS Layer

MARS is the app-state layer that sits beside the legacy reporting pipeline.

### Data Store

- `db/connection.py` opens `data/visusta.db`
- `db/migrate.py` runs migrations and seeds the app
- The schema includes 12 tables: `locales`, `client_locale_settings`, `industry_profiles`, `keyword_rules`, `source_proposals`, `report_templates`, `template_versions`, `client_template_overrides`, `report_drafts`, `draft_revisions`, `draft_chat_messages`, `approval_states`, and `export_jobs`
- 24 EU official languages are seeded in the locale catalog

### Business Logic

- `mars/draft_lifecycle.py` enforces draft status transitions
- `mars/section_model.py` serializes `DraftSection` objects and diffs section sets
- `mars/docx_import.py` imports DOCX files into draft sections
- `mars/docx_export.py` exports draft sections to DOCX
- `mars/pdf_export.py` exports approved draft sections to PDF

### Agents

- `agents/llm.py` defines the LLM interface and a deterministic `StubLLM`
- `agents/draft_composer.py` turns changelog and evidence data into draft sections
- `agents/translation_agent.py` localizes sections into a target locale
- `agents/draft_chat.py` applies conversational edits to sections
- `agents/source_scout.py` proposes new sources and persists evidence

The agents are real code paths, but they are intentionally backend-agnostic. The current implementation ships with a stub LLM so tests and local runs stay deterministic.

---

## API Surface

### FastAPI App

- `api/main.py` creates the app, applies CORS, mounts static charts and output, runs migrations on startup, and includes all routers
- `/api/health` reports config and data-directory status
- `/api/clients` and `/api/overview` provide client registry and cross-client summaries

### Client Routes

- `api/routers/clients.py` exposes client detail, changelog/state access, report generation, screening runs, audits, topics, source config, thresholds, preferences, and evidence records
- `api/routers/locales.py` exposes the locale catalog and per-client locale settings
- `api/routers/keywords.py` manages keyword rules and preview matching
- `api/routers/sources.py` manages source proposals and impact previews
- `api/routers/templates.py` manages templates, versions, section updates, theme updates, cloning, and publishing
- `api/routers/drafts.py` manages draft CRUD, revision history, compose, translate, chat, and approval state transitions
- `api/routers/exports.py` manages PDF and DOCX export jobs plus DOCX import

### Frontend Surface

- The frontend package exists as a separate Next.js workspace
- `frontend/package.json` defines `dev`, `build`, `start`, and `lint`
- Playwright E2E runs from `frontend/e2e/`

---

## Persistence

Persistence is hybrid.

| Path | Content | Mutability |
|------|---------|-----------|
| `regulatory_data/states/{YYYY-MM}.json` | Screening state snapshot | Written once per month |
| `regulatory_data/changelogs/{YYYY-MM}.json` | Monthly changelog | Written once per month |
| `regulatory_data/audits/gap_analysis_report.md` | Audit output | Regenerated on demand |
| `data/visusta.db` | MARS app state, locales, templates, drafts, approvals, exports | Transactional SQLite |
| `output/*.json` | Structured report data | Regenerated per build |
| `output/pdf/*.pdf` | Final deliverable PDFs | Regenerated per build |
| `charts/*.png` | Chart assets | Regenerated per build |
| `config/visusta.yaml` | System configuration | Manual edit |

---

## External Dependencies

| Package | Role |
|---------|------|
| reportlab | PDF generation |
| matplotlib | Chart generation |
| numpy | Numeric backend for matplotlib |
| pandas | Data manipulation |
| pydantic | API schema validation |
| fastapi | REST API |
| jinja2 | Template rendering |
| sqlite3 | MARS persistence |
| python-docx | DOCX import/export |
| freezegun | Deterministic tests |

Frontend tooling lives in `frontend/package.json`:

- Next.js 16
- React 19
- Playwright
- Tailwind CSS 4
- Recharts

---

## Data Model

### Monthly Domain

`regulatory_screening.py` still drives the monthly domain model:

- `MonthlyScreeningInput` contains the screening period, regulation list, topic coverage, and quality flags
- `MonthlyChangelog` groups results into new, status, content, timeline, metadata, ended, and carried-forward buckets
- Topics remain the five ESG categories: GHG, Packaging, Water, Waste, and Social/Human Rights

### Quarterly Domain

`quarterly_consolidator.py` still produces the quarterly domain model:

- `ChangeLogEntry` carries regulation code, scope, impact level, status, sources, milestones, action items, and confidence score
- `ConsolidatedRegulation` groups quarterly entries by regulation code
- `QuarterlySummary` contains consolidated regulations, period metadata, and summary statistics

### Adapter Bridge

`models.py` maps the monthly changelog schema into the quarterly schema:

- severity maps to impact level
- geographic scope maps to regulation scope
- topic maps to affected areas
- regulation identifiers are re-keyed for quarterly output

---

## Test Coverage

The repo now has real automated coverage instead of a prototype-only stub.

- Backend tests: `pytest -q tests/`
- Frontend build: `cd frontend && npm run build`
- Frontend E2E: `cd frontend && npx playwright test --reporter=line`

Coverage spans the legacy screening and consolidation pipeline, MARS database and model behavior, API integration, agent workflows, and the PDF export path.

---

## Current Constraints

1. Legacy JSON artifacts are still the source of truth for monthly screening and quarterly consolidation.
2. Manual data ingestion is still part of the workflow, even though agent proposals help with sources.
3. Two different changelog models still exist, bridged by an adapter rather than unified.
4. Some report content is still template- or string-driven, so not every narrative is fully data-generated yet.
5. There is no authentication layer yet.
6. There is no CI/CD pipeline in the repo yet.
7. Chart generation still uses fixed visualizations rather than fully data-driven dashboards.
8. The LLM layer still defaults to `StubLLM`; production backend integration remains a swap-in step.
9. Frontend page-level docs should be checked against the `frontend/` source before making route-specific claims.
