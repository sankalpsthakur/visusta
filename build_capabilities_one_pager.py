#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle


PAGE_W, PAGE_H = landscape(A4)
OUTPUT_PATH = Path("output/pdf/Visusta_Agent_Orchestrated_Dashboard_One_Pager.pdf")

C_BRAND = colors.HexColor("#0D3B26")
C_BRAND_LIGHT = colors.HexColor("#1A6B4B")
C_ACCENT = colors.HexColor("#B7D77A")
C_TEXT = colors.HexColor("#1D2A24")
C_MUTED = colors.HexColor("#5C6E66")
C_BORDER = colors.HexColor("#D6DED9")
C_ROW = colors.HexColor("#F5F8F6")
C_WARN = colors.HexColor("#FFF7EA")
C_WHITE = colors.white


def build_styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {}
    styles["title"] = ParagraphStyle(
        "title",
        parent=sample["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=C_BRAND,
        alignment=TA_LEFT,
        spaceAfter=4,
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle",
        parent=sample["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=C_MUTED,
        spaceAfter=5,
    )
    styles["section"] = ParagraphStyle(
        "section",
        parent=sample["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=9.2,
        leading=11,
        textColor=C_WHITE,
    )
    styles["cell"] = ParagraphStyle(
        "cell",
        parent=sample["BodyText"],
        fontName="Helvetica",
        fontSize=7.7,
        leading=9.6,
        textColor=C_TEXT,
        spaceAfter=0,
    )
    styles["emphasis"] = ParagraphStyle(
        "emphasis",
        parent=styles["cell"],
        fontName="Helvetica-Bold",
    )
    return styles


def on_page(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(C_WHITE)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(C_BRAND)
    canvas.rect(0, PAGE_H - 8 * mm, PAGE_W, 8 * mm, fill=1, stroke=0)
    canvas.setFillColor(C_BRAND)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(16 * mm, 11 * mm, "visusta - Agent-Orchestrated Dashboard")
    canvas.setFillColor(C_MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawRightString(PAGE_W - 16 * mm, 11 * mm, "April 4, 2026")
    canvas.restoreState()


def info_box(title: str, body: str, styles: dict[str, ParagraphStyle], width: float) -> Table:
    table = Table(
        [
            [Paragraph(title, styles["section"])],
            [Paragraph(body, styles["cell"])],
        ],
        colWidths=[width],
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), C_BRAND),
                ("BACKGROUND", (0, 1), (-1, 1), C_WHITE),
                ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, C_BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def build_story(styles: dict[str, ParagraphStyle]) -> list:
    left_width = 120 * mm
    right_width = 120 * mm

    orchestration = (
        "<b>Central dashboard:</b> one workspace where users launch, monitor, and steer specialized agents for screening, synthesis, reporting, and follow-up actions.<br/>"
        "<b>Agent roles:</b> source scout, validator, summarizer, report writer, and reviewer agents working in parallel under one orchestration layer.<br/>"
        "<b>Operator view:</b> status panels, queues, approvals, and traceable work logs instead of raw scripts."
    )
    trust_layer = (
        "<b>Quality and trust layer:</b> cross-source validation, confidence scoring, approval checkpoints, and optional second-model review before final publication.<br/>"
        "<b>Noise reduction:</b> topic filters, jurisdiction filters, severity ranking, deduplication, and explainable change traces.<br/>"
        "<b>Outcome:</b> faster intelligence production without losing auditability."
    )
    source_intake = (
        "<b>Source intake and referencing:</b> ingest links to web pages, official gazettes, PDF documents, uploaded files, and internal reference material into one evidence layer.<br/>"
        "<b>Referencing:</b> every report section can resolve back to source URLs, file references, access dates, and evidence snippets.<br/>"
        "<b>Benefit:</b> reports stay readable for executives while remaining traceable for compliance teams."
    )
    outputs = (
        "<b>Output shape:</b> monthly operational radar, quarterly strategic brief, executive summaries, priority matrices, and agent-generated action lists from the same evidence base.<br/>"
        "<b>Dashboard usage:</b> users can trigger refreshes, compare periods, drill into a topic, and generate a board-ready PDF on demand."
    )
    adjustability = (
        "<b>Adjustable radar and reports:</b> choose jurisdictions, topics, facilities, thresholds, report tone, chart mix, section order, and depth of analysis from the dashboard.<br/>"
        "<b>Scalable scope:</b> add new countries, new ESG topics, or new source classes later without redesigning the whole system."
    )
    expectations = (
        "<b>What Visusta can expect:</b> a dashboard to orchestrate agents, source management for analysts, approval flows for reviewers, and polished outputs for leadership.<br/>"
        "<b>Commercially important message:</b> this is not just a static report generator; it is a controllable intelligence workspace built around agents and traceable evidence."
    )

    top_grid = Table(
        [
            [
                info_box("Dashboard and agent orchestration", orchestration, styles, left_width),
                info_box("Quality and trust layer", trust_layer, styles, right_width),
            ],
            [
                info_box("Source intake and referencing", source_intake, styles, left_width),
                info_box("Output shape", outputs, styles, right_width),
            ],
            [
                info_box("Adjustable radar and reports", adjustability, styles, left_width),
                info_box("What Visusta can expect", expectations, styles, right_width),
            ],
        ],
        colWidths=[left_width, right_width],
        rowHeights=[50 * mm, 44 * mm, 42 * mm],
        hAlign="LEFT",
    )
    top_grid.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    note = Table(
        [[Paragraph(
            "<b>Positioning note:</b> present Visusta as a dashboard-led intelligence platform where users orchestrate agents, collect evidence, control quality, and generate executive-ready outputs from one place.",
            styles["cell"],
        )]],
        colWidths=[246 * mm],
        hAlign="LEFT",
    )
    note.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), C_WARN),
                ("BOX", (0, 0), (-1, -1), 0.5, C_ACCENT),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    return [
        Paragraph("Visusta Agent-Orchestrated Intelligence Dashboard", styles["title"]),
        Paragraph(
            "One-page concept sheet focused on what Visusta should expect: a dashboard to orchestrate agents, manage sources, control trust, and produce adjustable regulatory intelligence outputs.",
            styles["subtitle"],
        ),
        Spacer(1, 2 * mm),
        top_grid,
        Spacer(1, 2 * mm),
        note,
    ]


def build_pdf(output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    styles = build_styles()

    doc = BaseDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Visusta Agent-Orchestrated Intelligence Dashboard",
        author="Codex",
    )
    frame = Frame(
        14 * mm,
        16 * mm,
        PAGE_W - 28 * mm,
        PAGE_H - 32 * mm,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="one_pager",
    )
    doc.addPageTemplates([PageTemplate(id="one_pager", frames=[frame], onPage=on_page)])
    doc.build(build_story(styles))
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Visusta functionality one-pager PDF.")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = build_pdf(args.output)
    print(path)


if __name__ == "__main__":
    main()
