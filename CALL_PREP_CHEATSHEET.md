# Call Prep Cheatsheet -- Gerold Demo/Sales Call

**INTERNAL ONLY -- DO NOT SHARE**
**Date:** TBD (propose 2pm CET)
**Prospect:** Gerold
**Product:** Visusta ESG Regulatory Intelligence Tool
**Goal:** Build trust, address all 16 questions, steer toward signed contract with 30% advance

---

## 1. Email Response Draft

Subject: **Re: Follow-up questions -- Visusta ESG Regulatory Intelligence**

> Hi Gerold,
>
> Thank you for the detailed and thoughtful questions -- they tell me you are evaluating this seriously, which is exactly the kind of diligence we appreciate.
>
> I would like to walk through all 16 points on a call. How does **[DATE] at 2pm CET** work for you? I expect about 60 minutes.
>
> In advance, a few key answers to the questions you will care about most:
>
> - **Data ownership:** 100% yours. The codebase, all regulatory data, and all generated reports belong to your organization. No vendor lock-in.
> - **Codebase:** Python, open-source libraries only (ReportLab, matplotlib). No proprietary dependencies. Full Git repo handover with documentation.
> - **Jurisdiction:** We are happy to agree on Zurich as governing jurisdiction.
>
> I will bring a concrete walkthrough of the current engine and a clear roadmap for the configuration layer that makes it operationally self-sufficient for your team.
>
> Looking forward to it.
>
> Best regards,
> Sankalp

**Why this works:** Concedes Zurich jurisdiction upfront (costs us nothing, builds trust immediately). Previews the strongest answers (data ownership, no lock-in, open-source stack). Frames the call around "walkthrough + roadmap" rather than "demo," which sets expectations correctly.

---

## 2. Gerold's 16 Questions -- Full Answers

### Q1: Concrete walkthrough of the tool

**Current state:**
- CLI-based Python system. No web UI, no dashboard.
- Run `python regulatory_screening.py` to execute monthly screening against JSON-based regulatory data.
- Run `python build_monthly_report.py` to generate a branded PDF report (A4, ~12 pages, cover page, charts, tables, references).
- Run `python build_quarterly_brief.py` to generate a quarterly strategic brief PDF (~18 pages).
- Run `python generate_charts.py` to produce 6 matplotlib charts embedded in reports.
- Data flows: JSON screening input --> change detection engine --> changelog JSON --> PDF builder --> branded PDF output.

**Strategic framing:**
"I will walk you through the complete pipeline live: from regulatory input data, through the change detection engine, to the final PDF output. You will see real reports generated for EU/German food manufacturing regulations -- GHG, Packaging, Water, Waste, Social/Human Rights."

**What to say:**
- Show the generated PDFs first (they look enterprise-grade -- cover pages, branded colors, charts, professional tables).
- Then show the screening engine and change detection logic.
- Frame it as "the intelligence engine is built and proven."

**What NOT to say:**
- Do not volunteer that the narrative sections in monthly reports are hardcoded in Python.
- Do not show the raw Python code unprompted. Only if asked.
- Do not say "CLI scripts" -- say "backend pipeline" or "processing engine."

---

### Q2: Where and how prompts can be configured

**Current state:**
- There are NO LLM prompts. The system is entirely rule-based.
- Change detection uses deterministic field-by-field comparison (status, dates, descriptions, requirements).
- Severity classification uses a priority matrix (CRITICAL/HIGH/MEDIUM/LOW/INFO).
- Narrative sections in monthly reports are hardcoded Python strings in `build_monthly_report.py`.
- Quarterly narratives use template-based consolidation from `quarterly_consolidator.py`.

**Strategic framing:**
"The current engine uses deterministic rule-based analysis -- no LLM dependency, no hallucination risk, no API cost variability. Prompts become relevant when we add the LLM layer for narrative generation, which is part of the engagement scope. The configuration layer will allow your team to define prompt templates, tone preferences, and topic-specific instructions through a config file or settings interface."

**What to say:**
- Emphasize that rule-based = reliable, auditable, deterministic.
- Position LLM integration as a "Phase 2 enhancement that the engagement delivers."
- The config layer will expose prompt templates as YAML/JSON configuration.

**What NOT to say:**
- Do not say "there are no prompts because there is no LLM."
- Do not say narratives are "hardcoded" -- say they are "template-driven" (the quarterly ones genuinely are).

---

### Q3: Where and how sources are defined, stored, managed

**Current state:**
- Sources are defined in two places:
  1. In `regulatory_data/states/*.json` -- each regulation has `applicable_countries`, `screening_source`, `references` fields.
  2. In PDF builder scripts as hardcoded reference lists (e.g., `refs = [...]` in `build_monthly_report.py` lines 791-803).
- The `ScreeningInputItem` dataclass includes `references: List[RegulatoryReference]` with `source_name`, `source_url`, `document_id`, `access_date`.
- Source validation exists in `quarterly_consolidator.py` via `SourceReference` with `reliability_score` (0.0-1.0).
- Storage: flat JSON files in `regulatory_data/states/` and `regulatory_data/changelogs/`.
- No UI for source management. Sources are added by editing JSON files or Python code.

**Strategic framing:**
"Sources are stored as structured data with full provenance -- source name, URL, document ID, access date, and reliability score. The engine tracks source reliability over time and uses it for confidence scoring. The engagement delivers a source management interface where your team can add, edit, and validate sources without touching code."

**What to say:**
- Show the `sample_monthly_data.json` file -- it has clean source structures with URLs, publishers, reliability scores.
- Emphasize the validation layer in `quarterly_consolidator.py` (min 2 sources, reliability thresholds).
- Frame source management UI as engagement scope.

**What NOT to say:**
- Do not mention that many report references are hardcoded in Python strings.
- Do not show `build_monthly_report.py` lines 791-803 (the hardcoded refs list).

---

### Q4: Where and how reporting output can be configured

**Current state:**
- PDF layout is defined in Python code using ReportLab (`build_monthly_report.py`, `build_quarterly_brief.py`).
- Brand colors are Python constants (e.g., `C_PRIMARY_DARK = HexColor('#0D3B26')`).
- Page templates, headers, footers, fonts, margins -- all in Python.
- Chart styles are in `generate_charts.py` (matplotlib).
- To change the report design, you edit Python files. No config file, no template system.

**Strategic framing:**
"The report templates are fully customizable. The engagement delivers a configuration layer where your team can adjust brand colors, logo, section ordering, chart styles, and narrative templates through a config file rather than editing code. The underlying ReportLab framework is extremely flexible -- it can produce any PDF design you need."

**What to say:**
- Show sample PDFs -- they are genuinely impressive (professional tables, charts, branded cover pages).
- "The design framework supports any layout your design team envisions."
- Frame the config layer as: "We extract the design parameters into a config file so your team can adjust without developer involvement."

**What NOT to say:**
- Do not say "you have to edit Python to change colors."
- Do not undersell the current PDF quality -- it is genuinely enterprise-grade.

---

### Q5: How a new country/radar is set up

**Current state:**
- Countries are filtered via `allowed_countries` config in `regulatory_screening.py` (line 1232): `"allowed_countries": ["EU", "DE"]`.
- Adding a new country means:
  1. Edit the `allowed_countries` list in the config dict.
  2. Add regulation entries for that country in the screening input JSON.
  3. The change detection engine processes them automatically.
- No UI, no settings page, no country wizard.

**Strategic framing:**
"Adding a new country is architecturally straightforward -- the engine already supports multi-jurisdiction tracking with the `applicable_countries` field on every regulation. Today, adding a country requires editing a config parameter. The engagement delivers a settings interface where your team selects target jurisdictions from a dropdown, and the system automatically scopes screening to those regions."

**What to say:**
- "The data model is already multi-jurisdiction. Each regulation carries its geographic scope (EU, national, state, local) and applicable countries."
- "Adding Switzerland, for example, would mean adding CH to the allowed list and sourcing Swiss regulatory data."
- Frame it as a data sourcing question, not a technical limitation.

**What NOT to say:**
- Do not say "you edit a Python dictionary."
- Do not promise instant country coverage -- sourcing regulatory data for a new country is the real work.

---

### Q6: Human-in-the-loop intervention points

**Current state:**
- Intervention points exist at several stages:
  1. **Screening input:** Human reviews/curates the monthly `MonthlyScreeningInput` JSON before running detection.
  2. **Change validation:** The `ChangeValidator` in `quarterly_consolidator.py` flags entries that fail quality checks (insufficient sources, low confidence, stale data).
  3. **Severity override:** Severity is auto-calculated but can be manually overridden in the JSON before PDF generation.
  4. **Narrative review:** The generated changelog (JSON/Markdown) can be reviewed before triggering PDF generation.
  5. **PDF review:** Final PDF is reviewed before distribution.
- Currently, intervention = editing JSON files or running scripts selectively.

**Strategic framing:**
"The workflow has five natural intervention points -- we designed it this way intentionally. Regulatory intelligence requires human judgment, especially for severity assessment and narrative framing. The engagement delivers a review interface at each intervention point: approve/reject changes, override severity, edit narratives before PDF generation."

**What to say:**
- Walk through the 5 intervention points clearly.
- "We believe in human-in-the-loop for regulatory content -- no fully autonomous publishing."
- Show the validation logic: min 2 sources, confidence scoring, data quality flags.

**What NOT to say:**
- Do not say "intervention means editing JSON files."

---

### Q7: Noise reduction and relevance

**Current state:**
- **Country filtering:** `allowed_countries` config filters out irrelevant jurisdictions (e.g., US regulations excluded when scope is EU/DE).
- **Topic coverage:** All 5 mandatory topics are always reported, even if "no change" -- prevents blind spots.
- **Change detection:** Only actual field-level differences trigger change entries. Unchanged regulations are "carried forward" with INFO severity.
- **Severity classification:** 5-level system (CRITICAL/HIGH/MEDIUM/LOW/INFO) ensures attention goes to what matters.
- **Confidence scoring:** `calculate_confidence_score()` weights source reliability (50%), validation status (30%), and data freshness (20%).
- **Gap analysis:** `gap_analysis.py` detects wrong-jurisdiction references (e.g., Hamburg, Michigan vs Hamburg, Germany), missing topic coverage, non-actionable references.

**Strategic framing:**
"Noise reduction is built into the architecture at multiple levels: jurisdiction filtering, change-type classification, severity ranking, and confidence scoring. The engine only surfaces what changed and why it matters. The gap analysis module runs automated audits to catch wrong-jurisdiction data or missing coverage."

**What to say:**
- Show the gap analysis report -- it catches real issues (wrong Hamburg references, missing primary sources).
- "The system distinguishes between 'something changed' and 'something changed that requires action.'"
- Mention the severity matrix: only CRITICAL and HIGH items require immediate attention.

**What NOT to say:**
- Do not oversell the sophistication -- it is rule-based filtering, not ML-based relevance ranking.

---

### Q8: Data ownership (100% theirs)

**Current state:**
- All data is stored as local JSON files in `regulatory_data/`.
- All code is Python with open-source dependencies only (ReportLab, matplotlib, no proprietary SDKs).
- No cloud dependency. No SaaS. No telemetry.
- Full Git repo handover.

**Strategic framing:**
"100% yours. The code, the data, the reports -- everything runs on your infrastructure. There is no cloud dependency, no vendor lock-in, no ongoing license fees for the core engine. You own the IP."

**What to say:**
- "This is not SaaS. You own the codebase outright after handover."
- "Open-source stack: Python, ReportLab (BSD license), matplotlib (PSF license). No proprietary components."
- "Your data never leaves your infrastructure."

**What NOT to say:**
- Nothing to hide here. This is the strongest answer. Lean into it.

---

### Q9: Access rights (only them)

**Current state:**
- No access control system exists because there is no multi-user system. It is CLI scripts run locally.
- After handover, only their team has access to the repo, data, and outputs.
- No telemetry, no phone-home, no analytics collection.

**Strategic framing:**
"After handover, access is entirely under your control. The system runs on your infrastructure -- there is no external access point. We recommend implementing role-based access through your existing IT infrastructure (e.g., Git permissions for code, file system permissions for data)."

**What to say:**
- "No external access. No telemetry. No analytics collection."
- "Access control integrates with your existing IT policies."

**What NOT to say:**
- Do not volunteer that there is no built-in RBAC -- frame it as "integrates with your existing access controls."

---

### Q10: Codebase and tools (long-term costs)

**Current state:**
- **Language:** Python 3.14
- **Dependencies:** ReportLab (PDF generation), matplotlib (charts), standard library (json, dataclasses, pathlib, difflib, enum)
- **No database:** JSON file storage
- **No infrastructure costs:** Runs on any machine with Python installed
- **No license fees:** All dependencies are open-source
- **Ongoing costs if LLM is added:** API costs for OpenAI/Anthropic (variable, usage-based)

**Strategic framing:**
"The long-term cost structure is minimal. No license fees, no infrastructure costs beyond a standard server. Python is the world's most popular language -- your team will never struggle to find developers. The only variable cost is LLM API usage if you choose to add AI-generated narratives, and even that can be capped with usage limits."

**What to say:**
- "Python + open-source = zero ongoing license costs."
- "Any Python developer can maintain and extend this codebase."
- "If you add LLM narratives, typical monthly API cost for this volume is EUR 50-200."

**What NOT to say:**
- Do not dwell on "no database" -- if asked, say "the current data volume is best served by file storage; database integration is straightforward if needed at scale."

---

### Q11: LLMs used and API costs

**Current state:**
- **No LLMs are currently integrated.** Zero. None.
- All narrative content is either:
  - Hardcoded in Python (monthly report sections)
  - Template-generated from structured data (quarterly consolidation)
  - Rule-based (change summaries, action suggestions)

**Strategic framing:**
"The current engine is intentionally LLM-free -- this means zero hallucination risk, zero API cost variability, and full auditability. The architecture is designed to accommodate LLM integration as an enhancement layer. The engagement scope includes building the LLM integration for narrative generation, with configurable prompt templates and human review before publishing."

**What to say:**
- "Today: zero LLM dependency. Fully deterministic."
- "The engagement adds LLM-powered narrative generation as an optional layer."
- "We recommend Claude or GPT-4 for regulatory narrative quality. Estimated cost: EUR 50-200/month for typical usage."
- "Every LLM-generated narrative goes through human review before publishing."

**What NOT to say:**
- Do NOT say "narratives are hardcoded in Python."
- Do not imply the system currently uses AI for analysis. It does not.
- If pressed: "The narratives in the current demo reports were authored by our regulatory analysts to demonstrate output quality. The engagement automates this with LLM + human review."

---

### Q12: Support model (they want 90 days, we proposed 30)

**Current state:**
- No existing support infrastructure. This would be the first client deployment.

**Strategic framing:**
Concede 90 days. It costs little and builds significant trust. Scope it clearly.

**What to say:**
- "We are happy to extend to 90 days of post-delivery support."
- "Let us define what support covers: bug fixes, configuration assistance, and operational questions. Feature requests beyond the agreed scope would be a separate engagement."
- "We propose weekly check-in calls during the first 30 days, then bi-weekly for the remaining 60."

**What NOT to say:**
- Do not fight over 30 vs 90 days. Concede it. The goodwill is worth more than the cost.

---

### Q13: Code handover (form, docs, repos)

**Current state:**
- Code lives in a Git repository.
- Existing documentation: `regulatory_screening_workflow.md` (technical design doc, 1750 lines), `README_BUILD_INSTRUCTIONS.md`, `QUARTERLY_CONSOLIDATION_WORKFLOW.md`.
- No inline code documentation beyond module-level docstrings.

**Strategic framing:**
"Full Git repository handover with complete documentation. This includes: architecture documentation, API reference, operational runbooks, deployment guide, and configuration reference. The codebase follows standard Python conventions and is well-structured."

**What to say:**
- "Private Git repository transferred to your organization."
- "Documentation package: architecture guide, operational runbook, configuration reference, developer onboarding guide."
- "We walk your team through the codebase in a dedicated handover session (2-3 hours)."

**What NOT to say:**
- Do not show the current state of documentation (it is technical design docs, not operational docs). Promise the operational docs as part of deliverables.

---

### Q14: Terminate after showcase if performance not met

**Current state:**
- This is a reasonable ask from their side.

**Strategic framing:**
"Absolutely. The milestone structure is designed for this. The 40% showcase payment is contingent on acceptance criteria we define together on this call. If the showcase does not meet the agreed criteria, you are not obligated to proceed."

**What to say:**
- "Let us define 3-5 measurable acceptance criteria right now."
- Suggest criteria like:
  1. Engine successfully detects changes across all 5 regulatory topics
  2. Monthly PDF report generated with correct data, branding, and references
  3. Quarterly brief consolidates 3 months of data correctly
  4. New country can be added via configuration (not code changes)
  5. Source management works through config interface
- "The showcase is your decision gate."

**What NOT to say:**
- Do not resist this point. It is standard and reasonable.

---

### Q15: Final payment after debugging phase

**Current state:**
- This aligns with the payment structure: 30% upfront, 40% showcase, 30% after debugging.

**Strategic framing:**
"Agreed. The final 30% is released after the debugging phase, which is defined as [X] weeks of operational testing where your team runs the system on real data and we fix any issues. Let us define 'debugging complete' as: zero open critical bugs, all acceptance criteria verified in production, and your team confirms operational readiness."

**What to say:**
- "The debugging phase protects you. We fix anything that does not meet spec."
- "We propose a 4-week debugging window."
- Define "done" clearly: no open critical/high bugs, acceptance criteria met, team sign-off.

**What NOT to say:**
- Do not leave "debugging phase" undefined. Scope it on the call.

---

### Q16: Jurisdiction (they want Zurich, we proposed Singapore)

**Current state:**
- We proposed Singapore (standard for our contracts). They want Zurich.

**Strategic framing:**
Concede immediately. This is a free trust-builder.

**What to say:**
- "We are happy to agree on Zurich as the governing jurisdiction."
- Say it early in the call, casually. "By the way, on jurisdiction -- Zurich works for us."
- Do not make it a negotiation point. Give it away.

**What NOT to say:**
- Do not explain why you originally proposed Singapore. Just concede.

---

## 3. Objection Handling Matrix

| Objection | Response | What NOT to Say |
|-----------|----------|-----------------|
| "30 days support is too short" | "Agreed. Let's do 90 days, scoped to bug fixes and operational support. Feature requests are a separate conversation." | Do not argue for 30 days. Concede immediately. |
| "We need to see it with OUR data first" | "Absolutely. That is what the showcase milestone is for. We configure the system with your regulatory scope, run it on your data, and you evaluate the output before the 40% payment." | Do not say "we can show you a demo with sample data." They want THEIR data. |
| "What if LLM landscape changes?" | "The engine is LLM-agnostic. The architecture has a clean abstraction layer -- swapping from GPT-4 to Claude to an open-source model is a config change, not a rewrite. You are never locked into one provider." | Do not mention that no LLM is currently integrated. |
| "Code quality concerns" | "The codebase follows standard Python conventions with type hints, dataclasses, and clear separation of concerns. We include a handover session where your developers review the code with us. And the 90-day support covers any quality issues you find." | Do not say "we can show you the code now" unless you have cleaned it up. |
| "Why 30% upfront?" | "The advance covers initial setup: configuring the engine for your regulatory scope, setting up the data pipeline, and building the first report templates. It de-risks both sides -- you get a working system early, and we can commit dedicated resources." | Do not say "it is standard." Explain the value they get for the advance. |
| "Singapore jurisdiction is a dealbreaker" | "Done. Zurich it is." (Smile, move on.) | Do not negotiate. Do not explain. Just agree. |
| "How do we add new regulations?" | "Today, a regulatory analyst adds new entries to the screening input -- it is structured data with clear fields. The engagement delivers a source management interface that makes this self-service for non-technical users." | Do not say "you edit a JSON file." |
| "Scalability concerns" | "The current architecture handles hundreds of regulations across multiple jurisdictions. For enterprise scale (thousands of regulations, real-time monitoring), the engagement includes performance optimization. The Python stack scales well with standard techniques." | Do not volunteer that it is file-based JSON storage. If pressed, say "we can add database backing when volume requires it." |
| "Can we modify PDF design?" | "Completely customizable. The PDF framework supports any design -- custom branding, layout, charts, tables. The engagement includes a configuration layer so your design team can adjust templates without developer involvement." | Do not say "you edit Python code." |
| "This seems like just scripts, not a product" | "What you are seeing is the intelligence engine -- the core IP. The engagement delivers the usability layer on top: configuration interface, source management, report customization, and LLM integration. Think of it as: engine built, dashboard and config layer are the engagement scope." | Do not get defensive. Acknowledge the observation and reframe. |
| "Where is the frontend/UI?" | "The frontend is part of the engagement deliverables. The engine is backend-first by design -- regulatory intelligence is a data processing problem. The UI wraps the engine for day-to-day operation. We scope the UI based on your team's workflow in the first two weeks." | Do not say "there is no frontend." Say "the frontend is part of the engagement scope." |
| "How do non-technical users operate this?" | "The engagement delivers exactly this: a configuration and operation layer that non-technical users can use. Source management, report scheduling, severity review -- all through an interface, not code. The 90-day support period ensures your team is fully autonomous." | Do not say "right now they would need to run Python scripts." |

---

## 4. Strategic Positioning

### The 3-Layer Architecture Pitch

```
Layer 3: FRONTEND / UI           <-- Engagement scope (optional Phase 2)
         Dashboard, report viewer, source manager

Layer 2: CONFIGURATION LAYER     <-- Engagement scope (primary)
         Prompt templates, source management, report config,
         country/jurisdiction setup, LLM integration

Layer 1: INTELLIGENCE ENGINE     <-- BUILT AND PROVEN
         Change detection, severity classification,
         PDF generation, quarterly consolidation,
         gap analysis, confidence scoring
```

**Narrative:**
"The intelligence engine -- Layer 1 -- is built, tested, and producing enterprise-grade reports today. What the engagement delivers is Layer 2: the configuration and usability layer that makes the engine self-service for your team. Layer 3 (frontend) is optional and can be scoped based on your team's needs."

### Why This Benefits the Client

1. **They own the core IP.** The engine is theirs. No vendor lock-in. No ongoing license.
2. **Open-source stack.** Any Python developer can maintain and extend it. No proprietary dependencies.
3. **Deterministic intelligence.** Rule-based change detection = auditable, reproducible, no hallucination risk.
4. **LLM-optional.** They can add AI narratives when ready, or stay fully deterministic.
5. **Proven output quality.** The generated PDFs are genuinely enterprise-grade (branded, charts, tables, references).

### Key Proof Points

- 5 regulatory topics tracked: GHG, Packaging, Water, Waste, Social/Human Rights
- 2 report types: Monthly Impact Report (operational) + Quarterly Strategic Brief (executive)
- 6 professional charts generated per reporting cycle
- Multi-jurisdiction support: EU + Germany (state-level: Hamburg, NRW)
- Change detection with 11 classification types and 5 severity levels
- Source validation with confidence scoring (reliability weights, multi-source requirements)
- Gap analysis module (wrong-jurisdiction detection, missing coverage, non-actionable references)

---

## 5. Next Steps to Steer Toward

### Payment Structure

| Milestone | Payment | Trigger |
|-----------|---------|---------|
| Contract signing | 30% | Signed contract |
| Showcase delivery + acceptance | 40% | Client accepts against defined criteria |
| Debugging phase completion | 30% | Zero critical bugs, team sign-off |

### Concessions to Make Early (Trust Builders)

1. **Zurich jurisdiction** -- Concede immediately, first 5 minutes of the call.
2. **90-day support** -- Concede, scoped to bug fixes and operational questions.
3. **Terminate at showcase** -- Agree clearly. Define acceptance criteria together.

### Things to Negotiate

1. **Acceptance criteria** -- Define 3-5 measurable criteria on the call. Propose:
   - Change detection works across all 5 topics with their regulatory scope
   - Monthly PDF generated with correct data and their branding
   - Quarterly brief consolidates 3 months correctly
   - New jurisdiction addable via configuration
   - Source management operational (add/edit/validate sources)

2. **Implementation timeline** -- 8-12 weeks
   - Weeks 1-2: Scope definition, regulatory data sourcing, config setup
   - Weeks 3-6: Configuration layer build, LLM integration, source management
   - Weeks 7-8: Showcase delivery
   - Weeks 9-12: Debugging phase

3. **Team assignment** -- Offer to assign:
   - Dedicated PM for weekly status updates
   - Designer for report templates (if they want custom PDF design)
   - Developer for ongoing support during debugging phase

### Close the Call With

- "Let me send you a summary of what we agreed today, including the acceptance criteria and timeline."
- "I will prepare the contract with Zurich jurisdiction and 90-day support and send it by [date]."
- "Can we schedule the showcase for [date, ~8 weeks out]?"

---

## 6. Key Talking Points

Quick-reference bullets for during the call:

**Opening (2 min):**
- "Thank you for the thorough questions. It shows you are evaluating this seriously."
- "Let me address jurisdiction first -- Zurich works perfectly for us."
- "And on support -- 90 days is fine. Let us define scope together."

**Engine Demo (15 min):**
- Show generated PDFs FIRST. They look impressive. Lead with output quality.
- "This is a real February 2026 report covering EU and German food manufacturing regulations."
- "The engine tracks 5 regulatory domains: GHG, Packaging, Water, Waste, Social/Human Rights."
- "Change detection runs monthly. Every regulation is compared field-by-field against last month."
- "Severity classification: CRITICAL, HIGH, MEDIUM, LOW, INFO -- your team only acts on what matters."

**Architecture (5 min):**
- "Three layers: Engine (built), Configuration (engagement scope), Frontend (optional Phase 2)."
- "You own everything. Python, open-source, no lock-in."
- "Zero LLM dependency today. AI narratives are an enhancement we add during the engagement."

**Addressing the Gap Honestly (5 min):**
- "Today, the engine runs as a backend pipeline. The engagement delivers the operational layer."
- "Your team needs to configure, not code. That is what we build."
- "The acceptance criteria at showcase ensure you only pay for what works."

**Commercial (10 min):**
- "30/40/30 payment structure. Showcase is your decision gate."
- "8-12 week timeline. Showcase at week 7-8."
- "90-day support, scoped to bugs and operational questions."
- "Let us define 3-5 acceptance criteria right now."

**Close (5 min):**
- "I will send a written summary and draft contract by [date]."
- "Showcase target: [date]."
- "Any questions I have not covered?"

**If things go sideways:**
- If Gerold pushes hard on "this is just scripts" -- "You are right that the current interface is technical. That is exactly what the engagement solves. The intelligence is in the engine; the engagement wraps it for your team."
- If Gerold asks to see code -- "Happy to. Let me share the screen." Show `regulatory_screening.py` (it is the most impressive module -- clean dataclasses, enums, type hints, 1360 lines of structured code).
- If Gerold asks about competitors -- "The alternative is a SaaS subscription where you do not own the data or the code. We give you the asset."
- If Gerold goes silent -- "What is your biggest concern right now? I would rather address it directly."
