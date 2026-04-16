# MARS Docs Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring repository documentation in line with the current MARS implementation, verification status, and runtime workflows.

**Architecture:** This pass treats documentation as three independent surfaces: product and architecture positioning, operational/build guidance, and workflow/process references. Each surface is updated against the current FastAPI, Next.js, MARS routers, locale coverage, and verified test/build commands, then reconciled into a consistent repo-wide narrative.

**Tech Stack:** Markdown, FastAPI, Next.js 16, Playwright, pytest, SQLite, ReportLab, python-docx

---

### Task 1: Refresh Product And Architecture Docs

**Files:**
- Modify: `/Users/sankalp/Projects/visusta/Architecture.md`
- Modify: `/Users/sankalp/Projects/visusta/INTERNAL_DEV_HANDOVER.md`
- Modify: `/Users/sankalp/Projects/visusta/SOLUTION_OVERVIEW.md`
- Reference: `/Users/sankalp/Projects/visusta/api/main.py`
- Reference: `/Users/sankalp/Projects/visusta/api/routers/`
- Reference: `/Users/sankalp/Projects/visusta/mars/`

- [ ] Update system description from prototype-only language to current hybrid legacy + MARS state
- [ ] Document MARS major capabilities: templates, drafts, approvals, exports, sources, keywords, locales
- [ ] Replace outdated claims about missing API/frontend/tests/database/LLM layers
- [ ] Add current verified status where appropriate without inventing unverified metrics

### Task 2: Refresh Operational And Build Docs

**Files:**
- Modify: `/Users/sankalp/Projects/visusta/README_BUILD_INSTRUCTIONS.md`
- Modify: `/Users/sankalp/Projects/visusta/frontend/README.md`
- Optional modify: `/Users/sankalp/Projects/visusta/frontend/AGENTS.md` only if a MARS-specific instruction is necessary
- Reference: `/Users/sankalp/Projects/visusta/frontend/playwright.config.ts`
- Reference: `/Users/sankalp/Projects/visusta/requirements.txt`
- Reference: `/Users/sankalp/Projects/visusta/package` docs only if needed via `frontend/package.json`

- [ ] Rewrite backend/frontend startup steps to match current ports, API URL expectations, and Playwright config
- [ ] Add current build/test commands for backend, frontend build, and browser E2E
- [ ] Replace boilerplate Next.js README content with project-specific MARS guidance
- [ ] Keep instructions concise and copy-pasteable

### Task 3: Refresh Workflow And Process Docs

**Files:**
- Modify: `/Users/sankalp/Projects/visusta/QUARTERLY_CONSOLIDATION_WORKFLOW.md`
- Modify: `/Users/sankalp/Projects/visusta/regulatory_screening_workflow.md`
- Reference: `/Users/sankalp/Projects/visusta/api/routers/drafts.py`
- Reference: `/Users/sankalp/Projects/visusta/api/routers/exports.py`
- Reference: `/Users/sankalp/Projects/visusta/api/routers/sources.py`

- [ ] Preserve useful legacy flow details, but clearly distinguish legacy monthly/quarterly pipeline from new MARS draft-first workflow
- [ ] Add where sources, keywords, template versions, draft revisions, approvals, DOCX checkpoints, and PDF export jobs now fit
- [ ] Make user journeys explicit for manual management and agent-assisted proposals
- [ ] Avoid promising unsupported behavior

### Task 4: Reconcile Terminology And Verification

**Files:**
- Review all modified docs above together

- [ ] Standardize terms such as MARS, draft, revision, template version, export job, and locale
- [ ] Ensure docs consistently describe EU official language coverage for routed web locales and current dictionary status
- [ ] Ensure verification commands align with the current passing suite:
  - `pytest -q tests/`
  - `cd frontend && npm run build`
  - `cd frontend && npx playwright test --reporter=line`

### Task 5: Final Review

**Files:**
- Review all modified markdown files

- [ ] Check for contradictions between documents
- [ ] Check headings and formatting for readability
- [ ] Confirm that no document still claims there is no API, no frontend, no database, or no tests
- [ ] Summarize any remaining docs intentionally left unchanged
