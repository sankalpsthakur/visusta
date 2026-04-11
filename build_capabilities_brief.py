#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Sequence

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


PAGE_W, PAGE_H = A4
OUTPUT_PATH = Path("output/pdf/Visusta_Functionality_And_Output_Guide.pdf")

C_BRAND = colors.HexColor("#0D3B26")
C_BRAND_DARK = colors.HexColor("#08271A")
C_ACCENT = colors.HexColor("#B7D77A")
C_TEXT = colors.HexColor("#1D2A24")
C_MUTED = colors.HexColor("#5C6E66")
C_BORDER = colors.HexColor("#D6DED9")
C_ROW = colors.HexColor("#F5F8F6")
C_NOTE_BG = colors.HexColor("#EEF5E7")
C_WARN_BG = colors.HexColor("#F7F2E8")
C_WHITE = colors.white


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {}

    styles["title"] = ParagraphStyle(
        "title",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=28,
        textColor=C_WHITE,
        alignment=TA_LEFT,
        spaceAfter=8,
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#DCE9E1"),
        spaceAfter=6,
    )
    styles["h1"] = ParagraphStyle(
        "h1",
        parent=base["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=21,
        textColor=C_BRAND,
        spaceBefore=10,
        spaceAfter=7,
    )
    styles["h2"] = ParagraphStyle(
        "h2",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=C_TEXT,
        spaceBefore=8,
        spaceAfter=5,
    )
    styles["body"] = ParagraphStyle(
        "body",
        parent=base["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=C_TEXT,
        spaceAfter=6,
    )
    styles["small"] = ParagraphStyle(
        "small",
        parent=styles["body"],
        fontSize=8.2,
        leading=11,
        textColor=C_MUTED,
        spaceAfter=4,
    )
    styles["table_header"] = ParagraphStyle(
        "table_header",
        parent=styles["body"],
        fontName="Helvetica-Bold",
        fontSize=8.4,
        leading=10,
        textColor=C_WHITE,
        alignment=TA_CENTER,
    )
    styles["table_cell"] = ParagraphStyle(
        "table_cell",
        parent=styles["body"],
        fontSize=8.6,
        leading=11,
        spaceAfter=0,
    )
    styles["note_title"] = ParagraphStyle(
        "note_title",
        parent=styles["body"],
        fontName="Helvetica-Bold",
        textColor=C_BRAND_DARK,
        spaceAfter=4,
    )
    styles["note_body"] = ParagraphStyle(
        "note_body",
        parent=styles["body"],
        spaceAfter=0,
    )
    return styles


def build_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    col_widths: Sequence[float],
    styles: dict[str, ParagraphStyle],
) -> Table:
    data = [[Paragraph(h, styles["table_header"]) for h in headers]]
    for row in rows:
        data.append([Paragraph(cell, styles["table_cell"]) for cell in row])

    table = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), C_BRAND),
                ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
                ("BACKGROUND", (0, 1), (-1, -1), C_WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_ROW, C_WHITE]),
                ("GRID", (0, 0), (-1, -1), 0.35, C_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def build_note(title: str, body: str, styles: dict[str, ParagraphStyle], background: colors.Color) -> Table:
    box = Table(
        [[Paragraph(title, styles["note_title"])], [Paragraph(body, styles["note_body"])]],
        colWidths=[160 * mm],
        hAlign="LEFT",
    )
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("BOX", (0, 0), (-1, -1), 0.6, C_BRAND),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return box


def on_cover(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(C_BRAND)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(C_BRAND_DARK)
    canvas.rect(0, 0, PAGE_W, 18 * mm, fill=1, stroke=0)
    canvas.setFillColor(C_ACCENT)
    canvas.rect(20 * mm, PAGE_H - 53 * mm, 58 * mm, 2.3 * mm, fill=1, stroke=0)
    canvas.restoreState()


def on_page(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(C_BORDER)
    canvas.line(22 * mm, PAGE_H - 15 * mm, PAGE_W - 22 * mm, PAGE_H - 15 * mm)
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.setFillColor(C_BRAND)
    canvas.drawString(22 * mm, PAGE_H - 11 * mm, "visusta - Functionality and Output Guide")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(C_MUTED)
    canvas.drawRightString(PAGE_W - 22 * mm, 11 * mm, f"Page {doc.page}")
    canvas.drawString(22 * mm, 11 * mm, "Repository-grounded capability brief")
    canvas.restoreState()


def add_paragraphs(story: list, lines: Iterable[str], style: ParagraphStyle) -> None:
    for line in lines:
        story.append(Paragraph(line, style))


def build_story(styles: dict[str, ParagraphStyle]) -> list:
    story: list = []

    story.append(Spacer(1, 62 * mm))
    story.append(Paragraph("Visusta Functionality and Output Guide", styles["title"]))
    story.append(
        Paragraph(
            "Detailed description of what the current repository does today, what the output looks like, "
            "what quality controls you can rely on, and which capabilities are still later-scope extensions.",
            styles["subtitle"],
        )
    )
    story.append(Spacer(1, 6 * mm))
    story.append(
        Paragraph(
            "Basis: current repository artifacts as of April 3, 2026. This brief distinguishes implemented behavior "
            "from roadmap material so the reader can separate dependable present-state functionality from proposed future work.",
            styles["subtitle"],
        )
    )
    story.append(Spacer(1, 18 * mm))
    story.append(
        Paragraph(
            "Current output in scope: monthly impact report PDF, quarterly strategic brief PDF, structured JSON screening/changelog artifacts, "
            "matplotlib charts, and a markdown gap-analysis audit.",
            styles["subtitle"],
        )
    )
    story.append(Spacer(1, 55 * mm))
    story.append(
        Paragraph(
            "Prepared from: SOLUTION_OVERVIEW.md, INTERNAL_DEV_HANDOVER.md, CALL_PREP_CHEATSHEET.md, "
            "regulatory_screening.py, quarterly_consolidator.py, gap_analysis.py, build_monthly_report.py, "
            "build_quarterly_brief.py, and the sample PDFs in this repo.",
            styles["small"],
        )
    )
    story.append(NextPageTemplate("content"))
    story.append(PageBreak())

    story.append(Paragraph("Executive summary", styles["h1"]))
    add_paragraphs(
        story,
        [
            "The current repo already implements a deterministic ESG regulatory monitoring engine for five mandatory topics: GHG, Packaging, Water, Waste, and Social / Human Rights. It produces branded monthly and quarterly PDFs and persists structured screening data, changelogs, and audit outputs on the local filesystem.",
            "The most important reliability point is that the current reporting path is not LLM-driven. Change detection, severity ranking, filtering, and most of the narrative assembly are rule-based or hardcoded. That keeps the present-state system auditable and reproducible, but it also means some sample report text and references are still embedded in Python rather than generated dynamically from structured data.",
            "The repo does not currently include a frontend, an API, direct PDF or document upload, website crawling, or a multi-LLM quality-control layer. Those items appear in the design and handover material as later-scope extensions, not as shipped functionality in the current codebase.",
        ],
        styles["body"],
    )
    story.append(
        build_note(
            "Bottom line",
            "You can rely on deterministic monitoring logic, structured local artifacts, auditable source metadata, and polished PDF output. "
            "You should not assume self-service uploads, automated crawling, dynamic end-to-end bibliography assembly in every report, "
            "or different-LLM cross-checking because those are not implemented today.",
            styles,
            C_NOTE_BG,
        )
    )
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("Implemented today", styles["h1"]))
    story.append(
        build_table(
            ["Capability", "What exists now", "What you can rely on"],
            [
                [
                    "Monthly Regulatory Impact Report",
                    "An A4 PDF with executive summary, technical screening summary, change-log tables, impact overview, detailed regulation sections, charts, references, and disclaimer.",
                    "A polished monthly report can be generated today and the sample repository output demonstrates the layout and section pattern.",
                ],
                [
                    "Quarterly Strategic Brief",
                    "An A4 PDF with consolidation coverage, per-topic overview, timeline, strategic priority matrix, deep-dive sections, financial impact, roadmap, and references.",
                    "A board-style quarterly brief exists today, with both a hardcoded sample builder and an adapter path from consolidated structured data.",
                ],
                [
                    "Structured artifacts",
                    "Monthly screening states and changelogs are stored as JSON. Gap analysis findings are written to markdown. Charts are exported as PNG files.",
                    "The pipeline is inspectable and rerunnable. The PDFs are not the only output.",
                ],
                [
                    "Topic and jurisdiction model",
                    "Five mandatory topics are enforced in every monthly run, with EU, federal, state, and local scope values and `allowed_countries` filtering.",
                    "The radar is already multi-jurisdiction in its data model, even though user-facing configuration is not productized yet.",
                ],
                [
                    "Pluggable ingestion hooks",
                    "The screening module defines `ScreeningSource` and `RegulationStore` protocols for multiple sources and alternative persistence backends.",
                    "The architecture is prepared for additional sources and storage implementations, but the repo does not bundle a rich connector catalog yet.",
                ],
            ],
            [39 * mm, 75 * mm, 63 * mm],
            styles,
        )
    )
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("Quality checks and hallucination control", styles["h1"]))
    add_paragraphs(
        story,
        [
            "The current implementation controls hallucination risk primarily by avoiding generative AI in the core reporting path. Monthly change detection compares structured states field by field, carries unchanged regulations forward explicitly, and uses deterministic severity rules rather than free-form generation.",
            "The quarterly layer adds explicit validation logic before an entry is treated as reliable. That validator checks source count, average source reliability, composite confidence score, data freshness, and retraction status.",
            "If LLM narratives are added later, the handover plan recommends Claude-based drafting with template fallback and human review before publishing. That future design is sensible, but it is not present-state behavior today.",
        ],
        styles["body"],
    )
    story.append(
        build_note(
            "LLM note",
            "Different-LLM cross-checking to prevent hallucination is not implemented in the current repo. "
            "Today the dependable control is deterministic logic plus source validation and manual review, not model arbitration.",
            styles,
            C_WARN_BG,
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(
        build_table(
            ["Control", "Current behavior", "Practical effect"],
            [
                [
                    "Field-level diff engine",
                    "Compares the new screening state with the prior period and classifies only real changes.",
                    "Reduces invented deltas and keeps unchanged items visible as carried forward rather than silently disappearing.",
                ],
                [
                    "Country and scope filtering",
                    "`allowed_countries` filters the monthly dataset and the audit checks for cross-jurisdiction leakage.",
                    "Reduces irrelevant noise from out-of-scope geographies.",
                ],
                [
                    "Topic coverage enforcement",
                    "All five topics are always reported and missing-topic inputs create data-quality flags.",
                    "Prevents silent blind spots where a topic disappears from the report entirely.",
                ],
                [
                    "Source thresholds",
                    "Quarterly validation requires at least 2 sources, average source reliability of at least 0.6, confidence of at least 0.5, and age of at most 90 days.",
                    "Weak or stale entries are excluded from validated reporting.",
                ],
                [
                    "Confidence-aware deduplication",
                    "When multiple screening sources provide the same regulation, the highest-confidence item is kept.",
                    "Suppresses duplicate noise while preserving the strongest available record.",
                ],
                [
                    "Gap analysis audit",
                    "The audit flags wrong-jurisdiction references, missing URLs, missing primary-source signals, missing topic coverage, and non-data-driven builders.",
                    "Provides a conservative review layer that catches data-quality and provenance issues before trust is misplaced.",
                ],
            ],
            [33 * mm, 69 * mm, 75 * mm],
            styles,
        )
    )
    story.append(PageBreak())

    story.append(Paragraph("Source handling and referencing", styles["h1"]))
    add_paragraphs(
        story,
        [
            "Source provenance exists at two levels. In the monthly screening model, a regulation can carry source name, source URL, document ID, access date, screening source, and confidence score. In the quarterly consolidation model, sources also carry publisher and reliability score, which feeds the confidence calculation.",
            "The report outputs show references as numbered bibliographies. The sample monthly and quarterly PDFs end with visible source lists that include URLs and access-date wording. That means the reports are readable as audit artifacts, not just narrative memos.",
            "One important limitation: the sample PDF builders still embed some references directly in Python. So the repo demonstrates strong reference presentation, but fully dynamic bibliography generation from end to end is only partially implemented today.",
        ],
        styles["body"],
    )
    story.append(
        build_table(
            ["Source input or reference type", "Supported today", "How it works or where it stops"],
            [
                [
                    "Official web pages and gazettes by URL",
                    "Yes",
                    "URLs can be stored on source objects and appear in the report bibliography.",
                ],
                [
                    "Official document IDs and regulation codes",
                    "Yes",
                    "Monthly references store `document_id`; quarterly entries and report sections also use stable regulation/source identifiers.",
                ],
                [
                    "Multiple references per regulation",
                    "Yes",
                    "The data models accept lists of references and the quarterly validator expects at least two sources for validated entries.",
                ],
                [
                    "Structured JSON screening files",
                    "Yes",
                    "This is the main ingestion path in the current repo.",
                ],
                [
                    "Pluggable source connectors",
                    "Partly",
                    "The `ScreeningSource` protocol exists, but the repo does not ship a mature live-connector set for web crawling or remote document retrieval.",
                ],
                [
                    "Direct PDF upload",
                    "No",
                    "No user-facing upload flow or PDF parser is implemented in the current code.",
                ],
                [
                    "Arbitrary document upload",
                    "No",
                    "There is no intake path today for uploaded Word files, slides, emails, or local documents.",
                ],
                [
                    "Automatic website crawling or scraping",
                    "No",
                    "There is no crawler, fetcher, or web-ingestion pipeline implemented in this repo.",
                ],
                [
                    "Source management UI",
                    "No",
                    "The docs describe it as a planned management layer, not a shipped feature.",
                ],
            ],
            [52 * mm, 22 * mm, 103 * mm],
            styles,
        )
    )
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("Operational workflow today", styles["h1"]))
    add_paragraphs(
        story,
        [
            "The current repository is best understood as an operator-driven pipeline rather than a self-service product. A regulatory analyst or developer prepares the monthly input, runs the screening logic, reviews the resulting JSON or markdown outputs, and then triggers PDF generation.",
            "That means the core engine already works, but it assumes a human operator around it. There is no job scheduler, review dashboard, or upload wizard in the baseline. Reliability comes from transparency and reviewability, not from workflow automation.",
        ],
        styles["body"],
    )
    story.append(
        build_table(
            ["Stage", "What happens now", "Reliance implication"],
            [
                [
                    "1. Input preparation",
                    "Monthly screening data is prepared as structured JSON-like records with topic, status, scope, dates, and references.",
                    "Quality depends on disciplined source curation before the engine runs.",
                ],
                [
                    "2. Scope normalization",
                    "The screening module filters by `allowed_countries`, ensures all five topics are represented, and emits data-quality flags for empty topics.",
                    "You can rely on consistent monthly coverage structure even when a topic has no new items.",
                ],
                [
                    "3. Change detection",
                    "The new state is compared to the prior state field by field and each change is classified into a deterministic change type.",
                    "The result is reproducible and inspectable. It is not a black-box narrative step.",
                ],
                [
                    "4. Validation and audit",
                    "Quarterly validation checks source count, reliability, age, and confidence; gap analysis independently audits references and scope.",
                    "Trust comes from explicit thresholds and audit findings, not from silent acceptance.",
                ],
                [
                    "5. Narrative assembly",
                    "Monthly report prose and parts of the sample quarterly brief are still assembled from hardcoded or rule-built content.",
                    "The visual output is strong, but some text is not yet generated directly from the latest structured dataset.",
                ],
                [
                    "6. PDF build",
                    "ReportLab builders generate branded A4 PDFs with tables, callouts, and chart placements.",
                    "The system can produce board-ready output today.",
                ],
                [
                    "7. Human release",
                    "A human reviews the outputs before distribution.",
                    "This is currently essential because workflow enforcement is procedural, not product-enforced.",
                ],
            ],
            [31 * mm, 82 * mm, 65 * mm],
            styles,
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(
        build_note(
            "Current operating model",
            "Today the repo supports a strong analyst-in-the-loop workflow. It should not be described as a lights-out autonomous platform yet.",
            styles,
            C_NOTE_BG,
        )
    )
    story.append(PageBreak())

    story.append(Paragraph("Report structure and output shape", styles["h1"]))
    story.append(
        build_table(
            ["Output", "Structure visible in current sample artifacts"],
            [
                [
                    "Monthly report",
                    "Cover page, executive summary, technical screening summary, change-log extract, monthly impact overview, regulation deep dives, tables, charts, references, and disclaimer.",
                ],
                [
                    "Quarterly brief",
                    "Cover page, executive summary, quarterly coverage table, per-topic summary, compliance timeline, strategic priority matrix, regulation deep dives, financial impact, roadmap, and references.",
                ],
                [
                    "Supporting artifacts",
                    "Chart PNGs, JSON screening state, JSON changelog or consolidation data, and markdown audit output.",
                ],
            ],
            [35 * mm, 142 * mm],
            styles,
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(
        Paragraph(
            "The PDFs are visually polished already. The more important engineering caveat is that the monthly and sample quarterly builders still contain hardcoded narrative sections. So the output quality is strong today, but the degree of parameterization is still incomplete.",
            styles["body"],
        )
    )

    story.append(Paragraph("How monthly and quarterly outputs differ", styles["h1"]))
    story.append(
        build_table(
            ["Dimension", "Monthly impact report", "Quarterly strategic brief"],
            [
                [
                    "Primary audience",
                    "Regulatory affairs, operations, and facility stakeholders who need to see what changed this cycle.",
                    "Executive leadership and board-style readers who need prioritization across a wider horizon.",
                ],
                [
                    "Main question answered",
                    "What changed since the last reporting period?",
                    "What strategic pattern emerges across the quarter and what should be prioritized next?",
                ],
                [
                    "Primary source artifact",
                    "Monthly screening state and monthly changelog.",
                    "Three monthly outputs consolidated into a quarterly summary.",
                ],
                [
                    "Detail level",
                    "Operational and change-specific.",
                    "Comparative, prioritization-heavy, and roadmap-oriented.",
                ],
                [
                    "Typical sections",
                    "Technical screening summary, change-log entries, impact overview, regulation deep dives, and references.",
                    "Coverage table, timeline, strategic priority matrix, thematic deep dives, financial impact, roadmap, and references.",
                ],
                [
                    "Validation emphasis",
                    "Scope filtering and deterministic classification.",
                    "Cross-month validation, conflict resolution, and confidence trend interpretation.",
                ],
                [
                    "Decision support style",
                    "Immediate operational action and monitoring.",
                    "Resource allocation, sequencing, and strategic planning.",
                ],
                [
                    "Current implementation maturity",
                    "Visually polished but with hardcoded narrative sections in the sample builder.",
                    "Two paths exist: a polished sample builder and a more data-oriented adapter from consolidation output.",
                ],
            ],
            [31 * mm, 73 * mm, 74 * mm],
            styles,
        )
    )
    story.append(Spacer(1, 3 * mm))
    add_paragraphs(
        story,
        [
            "This distinction matters when presenting the solution. The monthly output is the change-monitoring instrument. The quarterly output is the executive synthesis instrument. They are related, but they are not interchangeable.",
            "It also matters for future extension work. If the product later adds uploads, UI, or LLM drafting, those additions will need slightly different rules for the monthly and quarterly layers because the two outputs serve different decision rhythms.",
        ],
        styles["body"],
    )

    story.append(Paragraph("Report and radar adjustment", styles["h1"]))
    add_paragraphs(
        story,
        [
            "In practical terms, the radar is defined by jurisdictions, topics, and source set. The report is defined by the ReportLab layout, branded constants, content sections, and charts. All of those levers exist today, but most are still developer-facing rather than self-service.",
            "That means the system is adjustable now, but adjustment usually means code or configuration changes by someone comfortable with the repository.",
        ],
        styles["body"],
    )
    story.append(
        build_table(
            ["Adjustment area", "Adjustable today", "What it currently requires"],
            [
                [
                    "Branding and layout",
                    "Yes",
                    "Edit ReportLab styles, page templates, frames, colors, headers, footers, and helper components in the PDF builder scripts.",
                ],
                [
                    "Section ordering and narrative blocks",
                    "Yes",
                    "Edit `build_content()` style functions or the quarterly adapter. Some sections are hardcoded.",
                ],
                [
                    "Charts",
                    "Yes",
                    "Edit `generate_charts.py` to change chart logic, labels, styling, or chart set.",
                ],
                [
                    "Jurisdictions / radar geography",
                    "Yes",
                    "Change `allowed_countries` and supply the relevant source data. The main effort is sourcing and validating the new jurisdiction.",
                ],
                [
                    "Topics",
                    "With engineering work",
                    "Extend the topic enum, update inputs, summaries, and templates. The engine assumes all defined topics are reported every cycle.",
                ],
                [
                    "Source set",
                    "With engineering work",
                    "Add or change screening inputs and implement new `ScreeningSource` connectors where needed.",
                ],
            ],
            [38 * mm, 30 * mm, 109 * mm],
            styles,
        )
    )
    story.append(PageBreak())

    story.append(Paragraph("Limitations and current caveats", styles["h1"]))
    add_paragraphs(
        story,
        [
            "This section is deliberately blunt. The repository is strong enough to demonstrate a credible intelligence engine, but it still contains present-state limitations that matter if the document is being used for decision-making or scope definition.",
            "These caveats do not invalidate the system. They simply define where present functionality stops and where productization work begins.",
        ],
        styles["body"],
    )
    story.append(
        build_table(
            ["Caveat", "What it means in practice", "Why it matters"],
            [
                [
                    "No live LLM quality layer",
                    "There is no implemented model orchestration, no second-model review, and no automatic hallucination checking.",
                    "Any claim about multi-LLM safety would be a roadmap statement, not a current feature statement.",
                ],
                [
                    "No upload workflow",
                    "Users cannot currently upload PDFs, Word files, spreadsheets, or arbitrary documents through a product interface.",
                    "Source ingestion is still developer or analyst mediated.",
                ],
                [
                    "No crawler or web fetch runtime",
                    "The repo does not automatically browse or scrape regulatory websites.",
                    "External research still depends on the source-preparation step outside the core engine.",
                ],
                [
                    "Hardcoded narratives remain",
                    "Parts of the monthly and sample quarterly narrative text are embedded in Python files.",
                    "Some sample outputs are presentation-grade but not fully parameterized by the latest structured data.",
                ],
                [
                    "Bibliography path is only partly dynamic",
                    "Reference presentation is strong, but some report references are embedded in the builders and not assembled end to end from source objects.",
                    "Auditability is good, but full provenance automation is not complete yet.",
                ],
                [
                    "No enforced approval product layer",
                    "Statuses such as draft, pending, validated, superseded, and retracted exist, but there is no UI or state machine enforcing distribution controls.",
                    "Human process discipline still carries part of the governance load.",
                ],
                [
                    "File-based persistence only",
                    "States and outputs live on disk as JSON, markdown, PNG, and PDF files.",
                    "This is simple and transparent, but not yet optimized for multi-user operations or administration.",
                ],
                [
                    "No automated test suite beyond the work added here",
                    "The handover doc itself says the baseline had no comprehensive project test suite.",
                    "Future productization still needs broader coverage around change detection, integration, and output generation.",
                ],
            ],
            [39 * mm, 73 * mm, 66 * mm],
            styles,
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(
        build_note(
            "How to read these caveats",
            "They are exactly the kinds of gaps you would expect between a strong internal engine and a finished operational product. "
            "They should drive scope and prioritization, not undermine confidence in the implemented core logic.",
            styles,
            C_WARN_BG,
        )
    )
    story.append(PageBreak())

    story.append(Paragraph("Planned or optional extensions", styles["h1"]))
    story.append(
        Paragraph(
            "The repository documentation is explicit about what comes next if the system is productized further. Those items are real extension paths, but they should be described as roadmap or engagement scope, not as present-day features.",
            styles["body"],
        )
    )
    story.append(
        build_table(
            ["Extension", "Why it matters", "Status in current repo"],
            [
                [
                    "Configuration layer",
                    "Move branding, thresholds, countries, topics, and templates out of hardcoded Python.",
                    "Planned. Not implemented as a dedicated config product layer yet.",
                ],
                [
                    "API and web UI",
                    "Allow non-technical users to run reports, manage settings, and review outputs without code.",
                    "Planned. No frontend or FastAPI layer is implemented today.",
                ],
                [
                    "Source management CRUD",
                    "Add/edit/validate sources without manual JSON or code edits.",
                    "Planned. Not implemented today.",
                ],
                [
                    "Approval workflow",
                    "Enforce draft, review, approve, publish transitions before distribution.",
                    "The status concepts exist in data models, but there is no enforced workflow layer yet.",
                ],
                [
                    "LLM-generated narratives",
                    "Replace hardcoded or rule-assembled narrative sections with assisted drafting.",
                    "Planned only. Handover recommends template fallback and human review.",
                ],
                [
                    "Alternative storage backends",
                    "Move from filesystem JSON to SQLite or PostgreSQL if scale or multi-user access increases.",
                    "Architecturally prepared through protocols, not implemented as the default runtime.",
                ],
                [
                    "Country / radar setup wizard",
                    "Make later-scope jurisdiction expansion self-service.",
                    "Planned. Current repo uses code/config changes instead.",
                ],
            ],
            [40 * mm, 72 * mm, 65 * mm],
            styles,
        )
    )
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("If further topics come into scope later", styles["h1"]))
    add_paragraphs(
        story,
        [
            "Bringing new topics into scope is feasible, but it is not just a prompt change. The topic enum, input data, summaries, validation rules, and report sections all assume a fixed topic set today. So adding a topic is a bounded engineering task, not an impossible rewrite, but it still needs deliberate implementation and source design.",
            "Bringing a new country or radar into scope follows the same pattern. The data model is already multi-jurisdiction, yet operational success depends more on sourcing and validating regulatory inputs than on the mechanical code change itself.",
            "LLM provider changes are also later-stage friendly. The handover material treats narrative generation as a replaceable enhancement layer, so Claude, GPT, or another provider could be swapped later. The important qualifier is that none of this provider abstraction is implemented in the current repo yet.",
        ],
        styles["body"],
    )
    story.append(
        build_note(
            "Recommended reading of scope",
            "Treat the current repo as a strong intelligence engine plus polished sample outputs. "
            "Treat self-service configuration, uploads, UI, and LLM-enhanced narrative generation as the next delivery layer.",
            styles,
            C_NOTE_BG,
        )
    )
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("Recommended next-phase packaging", styles["h1"]))
    add_paragraphs(
        story,
        [
            "If this document is being used to define a next engagement, the cleanest framing is to separate three layers. Layer 1 is the engine that already exists: screening logic, consolidation logic, audit rules, charts, and PDF rendering. Layer 2 is the configuration and governance layer: editable settings, source management, review flow, and parameterized templates. Layer 3 is the operator experience: API, UI, scheduling, uploads, and optional LLM drafting.",
            "That framing prevents two common mistakes. First, it avoids understating how much is already real in the baseline. Second, it avoids overstating the current repo as if it were already a fully self-service product.",
        ],
        styles["body"],
    )
    story.append(
        build_table(
            ["Layer", "Already present", "Typical next work"],
            [
                [
                    "Layer 1: intelligence engine",
                    "Yes",
                    "Mostly refinement, broader test coverage, and additional source implementations.",
                ],
                [
                    "Layer 2: configuration and governance",
                    "Partly",
                    "Extract config, build source CRUD, add approval workflow, and make templates editable.",
                ],
                [
                    "Layer 3: user-facing operations",
                    "No",
                    "Add API, UI, uploads, scheduling, operator dashboards, and optional AI drafting.",
                ],
            ],
            [42 * mm, 28 * mm, 108 * mm],
            styles,
        )
    )
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("Evidence base used for this brief", styles["h1"]))
    story.append(
        build_table(
            ["File", "Why it matters"],
            [
                [
                    "SOLUTION_OVERVIEW.md",
                    "Defines the intended capabilities, quality-assurance concepts, report sections, and commercial framing.",
                ],
                [
                    "INTERNAL_DEV_HANDOVER.md",
                    "Separates real implementation from future gap-closure work and names extension points for LLMs, config, API, and UI.",
                ],
                [
                    "regulatory_screening.py",
                    "Shows the actual monthly data models, filtering, normalization, deduplication, and export behavior.",
                ],
                [
                    "quarterly_consolidator.py",
                    "Shows validated-source rules, confidence scoring, and structured quarterly consolidation behavior.",
                ],
                [
                    "gap_analysis.py",
                    "Proves the existing conservative audit checks and also shows that the sample PDF builders are still partly hardcoded.",
                ],
                [
                    "build_monthly_report.py / build_quarterly_brief.py",
                    "Show the current visual output structure and where layout, references, and narrative text are assembled.",
                ],
                [
                    "Sample PDFs and charts",
                    "Show what the current polished output actually looks like in rendered form.",
                ],
            ],
            [57 * mm, 120 * mm],
            styles,
        )
    )

    return story


def build_pdf(output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    styles = build_styles()

    doc = BaseDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Visusta Functionality and Output Guide",
        author="Codex",
    )
    cover_frame = Frame(
        18 * mm,
        18 * mm,
        PAGE_W - 36 * mm,
        PAGE_H - 36 * mm,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="cover_frame",
    )
    content_frame = Frame(
        20 * mm,
        18 * mm,
        PAGE_W - 40 * mm,
        PAGE_H - 36 * mm,
        leftPadding=0,
        rightPadding=0,
        topPadding=2 * mm,
        bottomPadding=0,
        id="content_frame",
    )
    doc.addPageTemplates(
        [
            PageTemplate(id="cover", frames=[cover_frame], onPage=on_cover),
            PageTemplate(id="content", frames=[content_frame], onPage=on_page),
        ]
    )
    doc.build(build_story(styles))
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Visusta functionality and output guide PDF.")
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help=f"Output PDF path. Default: {OUTPUT_PATH}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = build_pdf(args.output)
    print(path)


if __name__ == "__main__":
    main()
