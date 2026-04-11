#!/usr/bin/env python3
"""
VISUSTA — Monthly Regulatory Impact Report
Enterprise-grade PDF, data-driven from extended changelog schema.
"""

import argparse
import os
import json
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether, NextPageTemplate, HRFlowable
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderPDF
from io import BytesIO

# ── Brand Colors ──────────────────────────────────────────────────
C_PRIMARY_DARK = HexColor('#0D3B26')
C_PRIMARY = HexColor('#1A6B4B')
C_PRIMARY_LIGHT = HexColor('#2E8B63')
C_ACCENT = HexColor('#4CAF50')
C_LIGHT_BG = HexColor('#E8F5E9')
C_WARM_GRAY = HexColor('#6B7B8D')
C_TEXT = HexColor('#1A1A2E')
C_MUTED = HexColor('#5A6270')
C_BORDER = HexColor('#D0D8DF')
C_ALERT_RED = HexColor('#C62828')
C_ALERT_AMBER = HexColor('#F57F17')
C_TABLE_HEAD = HexColor('#0D3B26')
C_TABLE_STRIPE = HexColor('#F0F7F2')

PAGE_W, PAGE_H = A4  # 595.28 x 841.89 points

# ── Output ────────────────────────────────────────────────────────
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
CHART_DIR = os.path.join(OUTPUT_DIR, 'charts')
# OUT_FILE and SCREENING_PERIOD are set at runtime via CLI args (see build_pdf / __main__)
_DEFAULT_PERIOD = "2026-02"


def _load_monthly_changelog(client_id: str, period: str):
    path = os.path.join(
        OUTPUT_DIR, "regulatory_data", client_id, "changelogs", f"{period}.json"
    )
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _period_to_display(period: str) -> str:
    """Convert 'YYYY-MM' to 'Month YYYY'."""
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    try:
        year, month = period.split("-")
        return f"{months[int(month) - 1]} {year}"
    except (ValueError, IndexError):
        return period


def _topic_label(topic: str) -> str:
    mapping = {
        "ghg": "GHG",
        "packaging": "Packaging",
        "water": "Water",
        "waste": "Waste",
        "social_human_rights": "Social / Human Rights",
    }
    return mapping.get(topic, topic)


def _status_label(status: str) -> str:
    mapping = {
        "law_passed": "Law passed",
        "amendment_in_progress": "Amendment in progress",
        "change_under_discussion": "Change under discussion",
        "proposed": "Proposed",
        "expired": "Expired",
        "repealed": "Repealed",
    }
    if not status:
        return ""
    return mapping.get(status, status.replace("_", " ").strip().capitalize())


def _change_type_label(change_type: str) -> str:
    mapping = {
        "new_regulation": "New regulation",
        "status_promoted_to_law": "Law passed",
        "status_advancing": "Amendment in progress",
        "law_being_amended": "Amendment in progress",
        "timeline_updated": "Timeline updated",
        "content_updated": "Content updated",
        "metadata_updated": "Metadata updated",
        "law_expired": "Ended / expired",
        "regulation_ended": "Ended / expired",
        "regulation_removed": "Removed",
    }
    if not change_type:
        return ""
    if change_type in mapping:
        return mapping[change_type]
    return re.sub(r"_+", " ", change_type).strip().capitalize()


# ══════════════════════════════════════════════════════════════════
# Page Templates (Header / Footer)
# ══════════════════════════════════════════════════════════════════
def _draw_header_footer(canvas_obj, doc, is_cover=False, period_display=""):
    """Draw branded header and footer on every non-cover page."""
    canvas_obj.saveState()

    if not is_cover:
        # ── Header line ──
        canvas_obj.setStrokeColor(C_PRIMARY)
        canvas_obj.setLineWidth(1.5)
        canvas_obj.line(25*mm, PAGE_H - 18*mm, PAGE_W - 25*mm, PAGE_H - 18*mm)

        # Header text
        canvas_obj.setFont('Helvetica-Bold', 8)
        canvas_obj.setFillColor(C_PRIMARY_DARK)
        canvas_obj.drawString(25*mm, PAGE_H - 16*mm, 'VISUSTA')
        canvas_obj.setFont('Helvetica', 7)
        canvas_obj.setFillColor(C_WARM_GRAY)
        canvas_obj.drawString(50*mm, PAGE_H - 16*mm, '— make visions real.')

        canvas_obj.setFont('Helvetica', 7)
        canvas_obj.setFillColor(C_MUTED)
        header_right = f'Monthly Regulatory Impact Report | {period_display}' if period_display else 'Monthly Regulatory Impact Report'
        canvas_obj.drawRightString(PAGE_W - 25*mm, PAGE_H - 16*mm, header_right)

        # ── Footer ──
        canvas_obj.setStrokeColor(C_BORDER)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(25*mm, 18*mm, PAGE_W - 25*mm, 18*mm)

        canvas_obj.setFont('Helvetica', 7)
        canvas_obj.setFillColor(C_MUTED)
        canvas_obj.drawString(25*mm, 13*mm, 'visusta GmbH | visusta.ch | Confidential')
        canvas_obj.drawRightString(PAGE_W - 25*mm, 13*mm, f'Page {doc.page}')

        # Thin green accent bar at top
        canvas_obj.setFillColor(C_PRIMARY)
        canvas_obj.rect(0, PAGE_H - 3*mm, PAGE_W, 3*mm, fill=1, stroke=0)

    canvas_obj.restoreState()


def _make_on_page(period_display: str):
    def on_page(canvas_obj, doc):
        _draw_header_footer(canvas_obj, doc, is_cover=False, period_display=period_display)
    return on_page

def on_cover(canvas_obj, doc):
    _draw_header_footer(canvas_obj, doc, is_cover=True)


# ══════════════════════════════════════════════════════════════════
# Styles
# ══════════════════════════════════════════════════════════════════
def build_styles():
    ss = getSampleStyleSheet()
    styles = {}

    styles['body'] = ParagraphStyle(
        'body', parent=ss['Normal'],
        fontName='Helvetica', fontSize=9.5, leading=14,
        textColor=C_TEXT, alignment=TA_JUSTIFY,
        spaceAfter=8, spaceBefore=2
    )
    styles['body_small'] = ParagraphStyle(
        'body_small', parent=styles['body'],
        fontSize=8.5, leading=12
    )
    styles['h1'] = ParagraphStyle(
        'h1', fontName='Helvetica-Bold', fontSize=16, leading=20,
        textColor=C_PRIMARY_DARK, spaceBefore=14, spaceAfter=8,
        borderWidth=0, borderPadding=0
    )
    styles['h2'] = ParagraphStyle(
        'h2', fontName='Helvetica-Bold', fontSize=13, leading=17,
        textColor=C_PRIMARY, spaceBefore=12, spaceAfter=6
    )
    styles['h3'] = ParagraphStyle(
        'h3', fontName='Helvetica-Bold', fontSize=11, leading=14,
        textColor=C_PRIMARY_LIGHT, spaceBefore=10, spaceAfter=5
    )
    styles['callout'] = ParagraphStyle(
        'callout', fontName='Helvetica', fontSize=9.5, leading=13,
        textColor=C_TEXT, alignment=TA_LEFT,
        leftIndent=12, borderWidth=0, spaceBefore=6, spaceAfter=6
    )
    styles['caption'] = ParagraphStyle(
        'caption', fontName='Helvetica-Oblique', fontSize=8, leading=10,
        textColor=C_MUTED, alignment=TA_CENTER, spaceAfter=12
    )
    styles['table_head'] = ParagraphStyle(
        'table_head', fontName='Helvetica-Bold', fontSize=8.5, leading=11,
        textColor=white, alignment=TA_LEFT
    )
    styles['table_cell'] = ParagraphStyle(
        'table_cell', fontName='Helvetica', fontSize=8.5, leading=11,
        textColor=C_TEXT, alignment=TA_LEFT
    )
    styles['ref'] = ParagraphStyle(
        'ref', fontName='Helvetica', fontSize=7.5, leading=10,
        textColor=C_MUTED, spaceBefore=1, spaceAfter=1,
        leftIndent=14, firstLineIndent=-14
    )
    styles['status_tag'] = ParagraphStyle(
        'status_tag', fontName='Helvetica-Bold', fontSize=8.5, leading=12,
        textColor=white, alignment=TA_CENTER
    )
    styles['cover_title'] = ParagraphStyle(
        'cover_title', fontName='Helvetica-Bold', fontSize=28, leading=34,
        textColor=white, alignment=TA_LEFT, spaceAfter=8
    )
    styles['cover_subtitle'] = ParagraphStyle(
        'cover_subtitle', fontName='Helvetica', fontSize=14, leading=18,
        textColor=HexColor('#B8D4C8'), alignment=TA_LEFT, spaceAfter=4
    )
    styles['cover_meta'] = ParagraphStyle(
        'cover_meta', fontName='Helvetica', fontSize=10, leading=14,
        textColor=HexColor('#8FB8A2'), alignment=TA_LEFT
    )
    return styles


# ══════════════════════════════════════════════════════════════════
# Helper: Status Badge
# ══════════════════════════════════════════════════════════════════
def status_badge(text, color, styles):
    """Return a single-cell table that looks like a colored badge."""
    plain = re.sub(r"<[^>]+>", "", str(text))
    # Estimate width using font metrics to avoid unintended wrapping.
    text_w = stringWidth(plain, 'Helvetica-Bold', 8.5)
    max_w = PAGE_W - 50*mm  # content frame width
    col_w = min(max_w, max(80, text_w + 28))

    # Let row height auto-size (prevents clipping when text wraps).
    t = Table([[Paragraph(text, styles['status_tag'])]], colWidths=[col_w])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), color),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    return t


# ══════════════════════════════════════════════════════════════════
# Helper: Callout Box
# ══════════════════════════════════════════════════════════════════
def callout_box(title, body_text, styles, accent_color=C_PRIMARY):
    """Green-bordered callout box for action items or key insights."""
    content = []
    if title:
        content.append(Paragraph(f'<b>{title}</b>', styles['callout']))
    content.append(Paragraph(body_text, styles['callout']))

    inner_table = Table([[content]], colWidths=[PAGE_W - 62*mm])
    inner_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_LIGHT_BG),
        ('LINEWIDTH', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))

    # Wrap in outer table with left accent border
    outer = Table([[inner_table]], colWidths=[PAGE_W - 58*mm])
    outer.setStyle(TableStyle([
        ('LINEWIDTH', (0,0), (-1,-1), 0),
        ('LINEBEFORE', (0,0), (0,-1), 3, accent_color),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    return outer


# ══════════════════════════════════════════════════════════════════
# Helper: Professional Table
# ══════════════════════════════════════════════════════════════════
def pro_table(headers, rows, col_widths, styles):
    """Enterprise table with header styling and alternating rows."""
    header_row = [Paragraph(h, styles['table_head']) for h in headers]
    data_rows = []
    for row in rows:
        data_rows.append([Paragraph(str(c), styles['table_cell']) for c in row])

    all_data = [header_row] + data_rows
    t = Table(all_data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), C_TABLE_HEAD),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, C_PRIMARY),
    ]
    # Alternating row colors
    for i in range(1, len(all_data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), C_TABLE_STRIPE))

    t.setStyle(TableStyle(style_cmds))
    return t


# ══════════════════════════════════════════════════════════════════
# Build the COVER PAGE
# ══════════════════════════════════════════════════════════════════
def build_cover(story, styles, period_display: str, client_context: dict):
    facility_line = client_context.get("facility_line", "")
    audience = client_context.get("audience", "")
    jurisdiction_label = client_context.get("jurisdiction_label", "")

    cover_content = []
    cover_content.append(Spacer(1, 45*mm))

    cover_content.append(Paragraph(
        '<font size="12" color="#8FB8A2">visusta</font>  '
        '<font size="9" color="#5F9A7E">— make visions real.</font>',
        ParagraphStyle('logo', fontName='Helvetica-Bold', fontSize=12, leading=16,
                       textColor=HexColor('#8FB8A2'), alignment=TA_LEFT)
    ))
    cover_content.append(Spacer(1, 25*mm))

    cover_content.append(Paragraph('Monthly Regulatory<br/>Impact Report', styles['cover_title']))
    cover_content.append(Spacer(1, 4*mm))
    if jurisdiction_label:
        cover_content.append(Paragraph(jurisdiction_label, styles['cover_subtitle']))
    cover_content.append(Spacer(1, 12*mm))

    cover_content.append(HRFlowable(
        width='60%', thickness=1, color=HexColor('#2E8B63'),
        spaceBefore=0, spaceAfter=12, hAlign='LEFT'
    ))

    meta_style = styles['cover_meta']
    cover_content.append(Paragraph(f'<b>Reporting Period:</b>  {period_display}', meta_style))
    if audience:
        cover_content.append(Paragraph(f'<b>Prepared for:</b>  {audience}', meta_style))
    if facility_line:
        cover_content.append(Paragraph(f'<b>Facilities:</b>  {facility_line}', meta_style))
    cover_content.append(Spacer(1, 30*mm))

    cover_content.append(Paragraph(
        '<font size="8" color="#5F9A7E">CLASSIFICATION: CONFIDENTIAL — INTERNAL USE ONLY</font>',
        ParagraphStyle('class', fontName='Helvetica', fontSize=8, textColor=HexColor('#5F9A7E'))
    ))

    inner = [[item] for item in cover_content]
    cover_table = Table(inner, colWidths=[PAGE_W - 50*mm])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_PRIMARY_DARK),
        ('LEFTPADDING', (0, 0), (-1, -1), 20*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15*mm),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    outer = Table([[cover_table]], colWidths=[PAGE_W - 50*mm])
    outer.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_PRIMARY_DARK),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    story.append(outer)
    story.append(PageBreak())


# ══════════════════════════════════════════════════════════════════
# Build the CONTENT
# ══════════════════════════════════════════════════════════════════
def _h1_for_tone(title: str, styles: dict, tone: str) -> Paragraph:
    if tone == "technical":
        tag = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
        return Paragraph(f'<font size="7" color="#5A6270">[{tag}]</font><br/>{title}', styles['h1'])
    if tone == "boardroom":
        return Paragraph(f'<b><u>{title}</u></b>', styles['h1'])
    return Paragraph(title, styles['h1'])


def build_content(story, styles, period: str, client_id: str, preferences: dict | None = None):
    S = styles
    body = S['body']

    prefs = preferences or {}
    depth = prefs.get("depth", "standard")
    section_order = prefs.get("section_order") or [
        "executive_summary", "change_log", "impact_summary", "topic_sections", "references"
    ]
    tone = prefs.get("tone", "executive")
    chart_mix = prefs.get("chart_mix")

    changelog = _load_monthly_changelog(client_id, period)
    if changelog is None:
        raise ValueError(
            f"No changelog found for client '{client_id}' and period '{period}'. "
            "Cannot generate report without data."
        )

    if depth == "brief":
        section_order = section_order[:3]

    def _render_chart(chart_ref: str, caption: str):
        if chart_mix is not None and chart_ref not in chart_mix:
            return
        chart_path = os.path.join(CHART_DIR, f'{chart_ref}.png')
        if os.path.exists(chart_path):
            story.append(Image(chart_path, width=155*mm, height=87*mm))
            story.append(Paragraph(caption, S['caption']))

    def _render_executive_summary():
        story.append(_h1_for_tone('Executive Summary', S, tone))
        exec_text = changelog.get("executive_summary", "")
        if exec_text:
            for para in exec_text.strip().split("\n\n"):
                para = para.strip()
                if para:
                    story.append(Paragraph(para, body))
        story.append(Spacer(1, 3*mm))

    def _render_change_log():
        story.append(Paragraph('Technical Screening Summary (Change Log)', S['h2']))
        story.append(Paragraph(
            f'This section is generated from the monthly regulatory change log for <b>{period}</b>.',
            S['body_small']
        ))
        story.append(Spacer(1, 3*mm))

        topic_rows = []
        statuses = changelog.get("topic_change_statuses") or {}
        topic_order_list = ["ghg", "packaging", "water", "waste", "social_human_rights"]
        for topic in topic_order_list:
            st = statuses.get(topic) or {}
            changed = "YES" if st.get("changed_since_last") else "NO"
            level_raw = st.get("level")
            level = _status_label(level_raw) if level_raw else ("—" if changed == "NO" else "Unspecified")
            cnt = st.get("changes_detected", 0)
            topic_rows.append([_topic_label(topic), changed, level, str(cnt)])

        story.append(pro_table(
            ['Topic', 'Change Since Last', 'Level', '# Changes'],
            topic_rows,
            [95, 95, 140, 60],
            styles
        ))
        story.append(Paragraph(
            'Table 1: Monthly technical screening status by topic (change log driven).',
            S['caption']
        ))
        story.append(Spacer(1, 4*mm))

        entries = []
        for key in ["new_regulations", "status_changes", "content_updates", "timeline_changes", "ended_regulations"]:
            entries.extend(changelog.get(key) or [])

        if entries:
            rows = []
            for e in entries[:20]:
                rows.append([
                    _topic_label(e.get("topic", "")),
                    e.get("regulation_id", ""),
                    _change_type_label(e.get("change_type", "")),
                    _status_label(e.get("current_status", "")),
                ])
            story.append(Paragraph('Change Log Entries (Top 20)', S['h3']))
            story.append(pro_table(
                ['Topic', 'Regulation', 'Change Type', 'Status'],
                rows,
                [70, 170, 125, 90],
                styles
            ))
            story.append(Paragraph(
                'Table 2: Extract of detected changes for this month.',
                S['caption']
            ))
            story.append(Spacer(1, 6*mm))

    def _render_impact_summary():
        impact_data = changelog.get("impact_summary_table")
        if impact_data:
            headers = impact_data.get("headers", [])
            rows = impact_data.get("rows", [])
            if headers and rows:
                col_count = len(headers)
                col_w = (PAGE_W - 50*mm) / col_count
                story.append(KeepTogether([
                    _h1_for_tone('Monthly Impact Overview', S, tone) if tone != "executive" else Paragraph('Monthly Impact Overview', S['h2']),
                    pro_table(headers, rows, [col_w] * col_count, styles),
                    Paragraph('Table 3: Monthly regulatory impact summary.', S['caption']),
                    Spacer(1, 6*mm),
                ]))

    def _render_topic_sections():
        sections = changelog.get("sections") or []
        for section in sections:
            heading = section.get("heading", "")
            if heading:
                story.append(_h1_for_tone(heading, S, tone))

            for para in section.get("paragraphs") or []:
                if para:
                    story.append(Paragraph(para, body))

            table_data = section.get("table")
            if table_data:
                headers = table_data.get("headers", [])
                rows = table_data.get("rows", [])
                if headers and rows:
                    col_count = len(headers)
                    col_w = (PAGE_W - 50*mm) / col_count
                    story.append(pro_table(headers, rows, [col_w] * col_count, styles))
                    story.append(Paragraph('', S['caption']))

            callout_text = section.get("callout")
            if callout_text:
                story.append(callout_box(None, callout_text, styles))

            chart_ref = section.get("chart_ref")
            if chart_ref:
                _render_chart(chart_ref, section.get("chart_caption", ""))

            story.append(Spacer(1, 8*mm))

        if depth == "deep":
            critical = changelog.get("critical_actions") or []
            if critical:
                story.append(Paragraph('Extended Commentary — Critical Actions', S['h2']))
                for entry in critical:
                    story.append(Paragraph(
                        f'<b>{entry.get("regulation_id", "")}</b>: {entry.get("action_required", "")}',
                        S['body_small']
                    ))
                    story.append(Spacer(1, 2*mm))

    def _render_references():
        references = changelog.get("references") or []
        if references:
            story.append(PageBreak())
            story.append(Paragraph('References', S['h1']))
            story.append(Paragraph(
                'The following sources underpin the analysis in this report.',
                S['body_small']
            ))
            story.append(Spacer(1, 3*mm))
            for i, ref in enumerate(references, 1):
                url = ref.get("url", "")
                citation_text = ref.get("citation", "")
                access_date = ref.get("access_date", "n/a")
                line = (
                    f'<b>[{i}]</b> <i>{citation_text}</i>. Accessed {access_date}. '
                    f'<link href="{url}" color="#8B2F1E">{url}</link>'
                ) if url else (
                    f'<b>[{i}]</b> <i>{citation_text}</i>. Accessed {access_date}.'
                )
                story.append(Paragraph(line, S['body_small']))
                story.append(Spacer(1, 2*mm))

    section_renderers = {
        "executive_summary": _render_executive_summary,
        "change_log": _render_change_log,
        "impact_summary": _render_impact_summary,
        "topic_sections": _render_topic_sections,
        "references": _render_references,
        "critical_actions": lambda: None,
    }

    for sec_id in section_order:
        renderer = section_renderers.get(sec_id)
        if renderer:
            renderer()

    story.append(Spacer(1, 15*mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_BORDER, spaceBefore=4, spaceAfter=8))
    story.append(Paragraph(
        '<b>Disclaimer:</b> This report is based on regulatory data and legislative drafts available '
        'as of the stated reporting period. Legislative texts are subject to parliamentary amendment '
        'prior to final adoption. This document does not constitute legal advice.',
        ParagraphStyle('disclaimer', fontName='Helvetica', fontSize=7.5, leading=10,
                       textColor=C_MUTED, alignment=TA_JUSTIFY)
    ))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        '\u00a9 visusta GmbH — visusta.ch — All rights reserved.',
        ParagraphStyle('footer_note', fontName='Helvetica', fontSize=7, leading=10,
                       textColor=C_MUTED, alignment=TA_CENTER)
    ))



# ══════════════════════════════════════════════════════════════════
# Build the Document
# ══════════════════════════════════════════════════════════════════
def build_pdf(period: str = _DEFAULT_PERIOD, client_id: str | None = None, output_path: str | None = None, preferences=None):
    styles = build_styles()

    if client_id is None:
        raise ValueError("client_id is required to load monthly changelogs")

    changelog = _load_monthly_changelog(client_id, period)
    if changelog is None:
        raise ValueError(
            f"No changelog found for client '{client_id}' and period '{period}'."
        )

    client_context = changelog.get("client_context") or {}
    period_display = _period_to_display(period)

    try:
        yr, mo = period.split("-")
        _month_abbr = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        period_slug = f"{_month_abbr[int(mo)-1]}{yr}"
    except (ValueError, IndexError):
        period_slug = period.replace("-", "")

    out_file = output_path or os.path.join(
        OUTPUT_DIR,
        f'Visusta_Monthly_Impact_Report_{period_slug}.pdf'
    )

    cover_frame = Frame(0, 0, PAGE_W, PAGE_H, leftPadding=25*mm, rightPadding=25*mm,
                        topPadding=10*mm, bottomPadding=10*mm, id='cover_frame')
    content_frame = Frame(25*mm, 22*mm, PAGE_W - 50*mm, PAGE_H - 45*mm,
                          id='content_frame')

    on_page = _make_on_page(period_display)
    cover_template = PageTemplate(id='cover', frames=[cover_frame], onPage=on_cover)
    content_template = PageTemplate(id='content', frames=[content_frame], onPage=on_page)

    doc = BaseDocTemplate(
        out_file,
        pagesize=A4,
        pageTemplates=[cover_template, content_template],
        title=f'Visusta Monthly Regulatory Impact Report \u2014 {period_display}',
        author='visusta GmbH',
        subject='EU & German Sustainability Regulatory Monitoring',
        creator='VARI \u2014 Visusta Autonomous Regulatory Intelligence'
    )

    story = []
    build_cover(story, styles, period_display=period_display, client_context=client_context)
    story.append(NextPageTemplate('content'))
    build_content(story, styles, period=period, client_id=client_id, preferences=preferences)

    os.makedirs(os.path.dirname(out_file) or ".", exist_ok=True)
    doc.build(story)
    print(f'\u2713 Monthly Report saved: {out_file}')
    print(f'  Size: {os.path.getsize(out_file) / 1024:.0f} KB')
    return out_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Build Visusta Monthly Regulatory Impact Report PDF.'
    )
    parser.add_argument(
        '--client-id',
        required=True,
        help='Client identifier used to load regulatory_data/<client_id>/changelogs',
    )
    parser.add_argument(
        '--period',
        default=_DEFAULT_PERIOD,
        help='Reporting period in YYYY-MM format (default: %(default)s)',
    )
    args = parser.parse_args()
    build_pdf(period=args.period, client_id=args.client_id)
