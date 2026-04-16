#!/usr/bin/env python3
"""
VISUSTA — Quarterly Strategic Brief
Enterprise-grade PDF, data-driven from extended changelog schema.
"""

import argparse
import logging
import os
import json
import re
from datetime import date
from xml.sax.saxutils import escape
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
from reportlab.pdfgen import canvas

from config import load_client_registry

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
C_DEEP_BLUE = HexColor('#1565C0')

PAGE_W, PAGE_H = A4
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
CHART_DIR = os.path.join(OUTPUT_DIR, 'charts')
# OUT_FILE and QUARTER_MONTHS are set at runtime via CLI args (see build_pdf / __main__)
_DEFAULT_PERIOD = "2026-02"


def _load_monthly_changelog(client_id: str, period: str):
    path = os.path.join(
        OUTPUT_DIR, "regulatory_data", client_id, "changelogs", f"{period}.json"
    )
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _quarter_for_period(period: str) -> str:
    """Return e.g. 'Q1 2026' for period '2026-02'."""
    try:
        year, month = period.split("-")
        q = (int(month) - 1) // 3 + 1
        return f"Q{q} {year}"
    except ValueError:
        return period


def _quarter_months_for_period(period: str) -> list:
    """Return the three YYYY-MM strings for the quarter containing period."""
    try:
        year, month = period.split("-")
        m = int(month)
        q_start = ((m - 1) // 3) * 3 + 1
        return [f"{year}-{str(q_start + i).zfill(2)}" for i in range(3)]
    except ValueError:
        return [period]


def _status_label(status: str) -> str:
    mapping = {
        "law_passed": "Law passed",
        "amendment_in_progress": "Amendment in progress",
        "change_under_discussion": "Change under discussion",
    }
    if not status:
        return "—"
    return mapping.get(status, status.replace("_", " ").strip().capitalize())


def _topic_label(topic: str) -> str:
    mapping = {
        "ghg": "GHG",
        "packaging": "Packaging",
        "water": "Water",
        "waste": "Waste",
        "social_human_rights": "Social / Human Rights",
    }
    return mapping.get(topic, topic)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _shade_hex(hex_color: str, factor: float) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    if factor < 1:
        r = round(r * factor)
        g = round(g * factor)
        b = round(b * factor)
    else:
        r = round(r + (255 - r) * (factor - 1))
        g = round(g + (255 - g) * (factor - 1))
        b = round(b + (255 - b) * (factor - 1))
    return _rgb_to_hex((max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))


def _load_branding(client_id: str, client_context: dict | None = None) -> dict:
    registry = load_client_registry()
    client = registry.get(client_id, {}) if isinstance(registry, dict) else {}
    context = client_context or {}
    display_name = client.get("display_name") or context.get("display_name") or client_id
    primary_hex = (
        (client.get("branding") or {}).get("primary_color")
        or context.get("primary_color")
        or "#1A6B4B"
    )
    if not isinstance(primary_hex, str):
        primary_hex = "#1A6B4B"
    try:
        primary = HexColor(primary_hex)
    except Exception:
        primary_hex = "#1A6B4B"
        primary = HexColor(primary_hex)
    if not primary_hex.startswith("#"):
        primary_hex = f"#{primary_hex}"
    return {
        "display_name": display_name,
        "primary_hex": primary_hex.upper(),
        "primary": primary,
        "primary_dark": HexColor(_shade_hex(primary_hex, 0.72)),
        "primary_light": HexColor(_shade_hex(primary_hex, 1.42)),
        "primary_soft": HexColor(_shade_hex(primary_hex, 1.75)),
    }


# ══════════════════════════════════════════════════════════════════
# Page Templates
# ══════════════════════════════════════════════════════════════════
def _draw_header_footer(canvas_obj, doc, is_cover=False, quarter_display="", brand=None):
    brand = brand or {
        "display_name": "Visusta",
        "primary": C_PRIMARY,
        "primary_dark": C_PRIMARY_DARK,
        "primary_light": C_PRIMARY_LIGHT,
        "primary_soft": HexColor('#8FB8A2'),
        "primary_hex": "#1A6B4B",
    }
    canvas_obj.saveState()
    if not is_cover:
        # Top accent bar
        canvas_obj.setFillColor(brand["primary"])
        canvas_obj.rect(0, PAGE_H - 3*mm, PAGE_W, 3*mm, fill=1, stroke=0)

        # Header
        canvas_obj.setStrokeColor(brand["primary"])
        canvas_obj.setLineWidth(1.5)
        canvas_obj.line(25*mm, PAGE_H - 18*mm, PAGE_W - 25*mm, PAGE_H - 18*mm)

        canvas_obj.setFont('Helvetica-Bold', 8)
        canvas_obj.setFillColor(brand["primary_dark"])
        canvas_obj.drawString(25*mm, PAGE_H - 16*mm, brand["display_name"])
        canvas_obj.setFont('Helvetica', 7)
        canvas_obj.setFillColor(C_MUTED)
        header_right = f'Quarterly Strategic Brief | {quarter_display}' if quarter_display else 'Quarterly Strategic Brief'
        canvas_obj.drawRightString(PAGE_W - 25*mm, PAGE_H - 16*mm, header_right)

        # Footer
        canvas_obj.setStrokeColor(C_BORDER)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(25*mm, 18*mm, PAGE_W - 25*mm, 18*mm)
        canvas_obj.setFont('Helvetica', 7)
        canvas_obj.setFillColor(C_MUTED)
        canvas_obj.drawString(25*mm, 13*mm, f'{brand["display_name"]} | Confidential')
        canvas_obj.drawRightString(PAGE_W - 25*mm, 13*mm, f'Page {doc.page}')
    canvas_obj.restoreState()

def on_cover(c, d): _draw_header_footer(c, d, True)

def _make_on_page(quarter_display: str, brand: dict):
    def on_page(c, d):
        _draw_header_footer(c, d, False, quarter_display=quarter_display, brand=brand)
    return on_page


# ══════════════════════════════════════════════════════════════════
# Styles
# ══════════════════════════════════════════════════════════════════
def build_styles():
    ss = getSampleStyleSheet()
    S = {}
    S['body'] = ParagraphStyle('body', parent=ss['Normal'], fontName='Helvetica',
                               fontSize=9.5, leading=14, textColor=C_TEXT,
                               alignment=TA_JUSTIFY, spaceAfter=8, spaceBefore=2)
    S['body_small'] = ParagraphStyle('body_small', parent=S['body'], fontSize=8.5, leading=12)
    S['h1'] = ParagraphStyle('h1', fontName='Helvetica-Bold', fontSize=16, leading=20,
                             textColor=C_PRIMARY_DARK, spaceBefore=14, spaceAfter=8)
    S['h2'] = ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=13, leading=17,
                             textColor=C_PRIMARY, spaceBefore=12, spaceAfter=6)
    S['h3'] = ParagraphStyle('h3', fontName='Helvetica-Bold', fontSize=11, leading=14,
                             textColor=C_PRIMARY_LIGHT, spaceBefore=10, spaceAfter=5)
    S['callout'] = ParagraphStyle('callout', fontName='Helvetica', fontSize=9.5, leading=13,
                                  textColor=C_TEXT, leftIndent=12, spaceBefore=6, spaceAfter=6)
    S['caption'] = ParagraphStyle('caption', fontName='Helvetica-Oblique', fontSize=8, leading=10,
                                  textColor=C_MUTED, alignment=TA_CENTER, spaceAfter=12)
    S['table_head'] = ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=8.5, leading=11,
                                     textColor=white, alignment=TA_LEFT)
    S['table_cell'] = ParagraphStyle('tc', fontName='Helvetica', fontSize=8.5, leading=11,
                                     textColor=C_TEXT, alignment=TA_LEFT)
    S['ref'] = ParagraphStyle('ref', fontName='Helvetica', fontSize=7.5, leading=10,
                              textColor=C_MUTED, spaceBefore=1, spaceAfter=1,
                              leftIndent=14, firstLineIndent=-14)
    S['status_tag'] = ParagraphStyle('st', fontName='Helvetica-Bold', fontSize=8.5, leading=12,
                                     textColor=white, alignment=TA_CENTER)
    S['cover_title'] = ParagraphStyle('ct', fontName='Helvetica-Bold', fontSize=28, leading=34,
                                      textColor=white, alignment=TA_LEFT, spaceAfter=8)
    S['cover_subtitle'] = ParagraphStyle('cs', fontName='Helvetica', fontSize=14, leading=18,
                                         textColor=HexColor('#B8D4C8'), alignment=TA_LEFT, spaceAfter=4)
    S['cover_meta'] = ParagraphStyle('cm', fontName='Helvetica', fontSize=10, leading=14,
                                     textColor=HexColor('#8FB8A2'), alignment=TA_LEFT)
    S['roadmap_item'] = ParagraphStyle('ri', fontName='Helvetica', fontSize=9.5, leading=14,
                                       textColor=C_TEXT, leftIndent=16, firstLineIndent=-16,
                                       spaceBefore=4, spaceAfter=4)
    return S


# ══════════════════════════════════════════════════════════════════
# Reusable Components
# ══════════════════════════════════════════════════════════════════
def status_badge(text, color, S):
    text_w = stringWidth(str(text), 'Helvetica-Bold', 8.5)
    max_w = PAGE_W - 50*mm
    col_w = min(max_w, max(80, text_w + 28))

    # Auto row height prevents clipped text when wrapping occurs.
    t = Table([[Paragraph(text, S['status_tag'])]], colWidths=[col_w])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), color),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROUNDEDCORNERS', [4,4,4,4]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    return t

def callout_box(title, body_text, S, accent_color=C_PRIMARY):
    content = []
    if title:
        content.append(Paragraph(f'<b>{title}</b>', S['callout']))
    content.append(Paragraph(body_text, S['callout']))
    inner = Table([[content]], colWidths=[PAGE_W - 62*mm])
    inner.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_LIGHT_BG),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    outer = Table([[inner]], colWidths=[PAGE_W - 58*mm])
    outer.setStyle(TableStyle([
        ('LINEBEFORE', (0,0), (0,-1), 3, accent_color),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    return outer

def pro_table(headers, rows, col_widths, S):
    header_row = [Paragraph(h, S['table_head']) for h in headers]
    data_rows = [[Paragraph(str(c), S['table_cell']) for c in row] for row in rows]
    all_data = [header_row] + data_rows
    t = Table(all_data, colWidths=col_widths, repeatRows=1)
    cmds = [
        ('BACKGROUND', (0,0), (-1,0), C_TABLE_HEAD),
        ('TEXTCOLOR', (0,0), (-1,0), white),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('LINEBELOW', (0,0), (-1,0), 1.5, C_PRIMARY),
    ]
    for i in range(1, len(all_data)):
        if i % 2 == 0:
            cmds.append(('BACKGROUND', (0,i), (-1,i), C_TABLE_STRIPE))
    t.setStyle(TableStyle(cmds))
    return t


# ══════════════════════════════════════════════════════════════════
# Cover Page
# ══════════════════════════════════════════════════════════════════
def build_cover(story, S, quarter_display: str, client_context: dict, brand: dict):
    facility_line = client_context.get("facility_line", "")
    audience = client_context.get("audience", "")
    jurisdiction_label = client_context.get("jurisdiction_label", "")
    display_name = brand["display_name"]

    items = []
    items.append(Spacer(1, 45*mm))
    items.append(Paragraph(
        f'<b>{escape(display_name)}</b>',
        ParagraphStyle('logo', fontName='Helvetica-Bold', fontSize=12, leading=16,
                       textColor=brand["primary_soft"])
    ))
    items.append(Spacer(1, 25*mm))
    items.append(Paragraph('Quarterly Strategic<br/>Brief', S['cover_title']))
    items.append(Spacer(1, 4*mm))
    if jurisdiction_label:
        items.append(Paragraph(jurisdiction_label, S['cover_subtitle']))
    items.append(Spacer(1, 12*mm))
    items.append(HRFlowable(width='60%', thickness=1, color=brand["primary"],
                             spaceBefore=0, spaceAfter=12, hAlign='LEFT'))
    m = S['cover_meta']
    items.append(Paragraph(f'<b>Reporting Period:</b>  {quarter_display}', m))
    if audience:
        items.append(Paragraph(f'<b>Prepared for:</b>  {audience}', m))
    if facility_line:
        items.append(Paragraph(f'<b>Facilities:</b>  {facility_line}', m))
    items.append(Spacer(1, 30*mm))
    items.append(Paragraph(
        '<font size="8">CLASSIFICATION: CONFIDENTIAL \u2014 INTERNAL USE ONLY</font>',
        ParagraphStyle('cls', fontName='Helvetica', fontSize=8, textColor=brand["primary_soft"])
    ))

    inner_rows = [[item] for item in items]
    ct = Table(inner_rows, colWidths=[PAGE_W - 50*mm])
    ct.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), brand["primary_dark"]),
        ('LEFTPADDING', (0,0), (-1,-1), 20*mm),
        ('RIGHTPADDING', (0,0), (-1,-1), 15*mm),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    outer = Table([[ct]], colWidths=[PAGE_W - 50*mm])
    outer.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), brand["primary_dark"]),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(outer)
    story.append(PageBreak())


def _synthesize_executive_summary(changelogs: dict) -> str:
    """Merge executive summaries from all available months into a quarterly narrative."""
    total_changes = sum(cl.get("total_changes_detected", 0) for cl in changelogs.values())
    total_critical = sum(len(cl.get("critical_actions") or []) for cl in changelogs.values())

    intro = (
        f"This quarterly strategic brief synthesizes regulatory intelligence across "
        f"{len(changelogs)} reporting period(s), documenting {total_changes} tracked changes "
        f"and {total_critical} critical actions requiring executive attention."
    )

    latest_period = sorted(changelogs.keys())[-1]
    latest_summary = changelogs[latest_period].get("executive_summary", "")

    return f"{intro}\n\n{latest_summary}" if latest_summary else intro


# ══════════════════════════════════════════════════════════════════
# Content
# ══════════════════════════════════════════════════════════════════
def build_content(story, S, quarter_months: list, quarter_display: str, client_id: str, brand: dict, preferences: dict | None = None):
    body = S['body']

    prefs = preferences or {}
    depth = prefs.get("depth", "standard")
    tone = prefs.get("tone", "executive")
    chart_mix = prefs.get("chart_mix")

    # Load all available changelogs for this quarter
    available_changelogs = {}
    for m in quarter_months:
        cl = _load_monthly_changelog(client_id, m)
        if cl:
            available_changelogs[m] = cl

    if not available_changelogs:
        raise ValueError(
            f"No changelogs found for client '{client_id}' in quarter months {quarter_months}. "
            "Cannot generate quarterly report without data."
        )

    latest_period = max(available_changelogs.keys())

    q_sections = {}
    try:
        from report_engine import ReportEngine
        engine = ReportEngine()
        q_sections = engine.render_quarterly_content(
            quarter_months, available_changelogs, quarter_display
        )
    except ModuleNotFoundError:
        pass
    except Exception as exc:
        logging.warning("ReportEngine.render_quarterly_content failed: %s", exc)
        q_sections = {}

    def _h1(title: str) -> Paragraph:
        if tone == "technical":
            tag = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
            return Paragraph(f'<font size="7" color="#5A6270">[{tag}]</font><br/>{title}', S['h1'])
        if tone == "boardroom":
            return Paragraph(f'<b><u>{title}</u></b>', S['h1'])
        return Paragraph(title, S['h1'])

    def _render_chart_if_allowed(chart_ref: str, path: str, caption: str):
        if chart_mix is not None and chart_ref not in chart_mix:
            return
        if os.path.exists(path):
            from reportlab.platypus import Image
            story.append(Image(path, width=155*mm, height=87*mm))
            story.append(Paragraph(caption, S['caption']))

    section_count = 0

    def _render_trailing_disclaimer():
        story.append(Spacer(1, 15*mm))
        story.append(HRFlowable(width='100%', thickness=0.5, color=C_BORDER, spaceBefore=4, spaceAfter=8))
        story.append(Paragraph(
            '<b>Disclaimer:</b> This report is based on regulatory data and legislative drafts available '
            'as of the stated reporting period. Legislative texts are subject to parliamentary amendment '
            'prior to final adoption. This document does not constitute legal advice.',
            ParagraphStyle('disc', fontName='Helvetica', fontSize=7.5, leading=10,
                           textColor=C_MUTED, alignment=TA_JUSTIFY)
        ))
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph(
            f'\u00a9 {escape(brand["display_name"])} \u2014 All rights reserved.',
            ParagraphStyle('fn', fontName='Helvetica', fontSize=7, leading=10,
                           textColor=C_MUTED, alignment=TA_CENTER)
        ))

    # ── Executive Summary ──
    story.append(_h1('Executive Summary'))
    exec_text = q_sections.get("executive_summary", "") or _synthesize_executive_summary(available_changelogs)
    section_count += 1
    if exec_text:
        for para in exec_text.strip().split("\n\n"):
            para = para.strip()
            if para:
                story.append(Paragraph(para, body))
    story.append(Spacer(1, 3*mm))

    # ── Quarterly Consolidation (Change Log Coverage) ──
    if depth == "brief" and section_count >= 3:
        _render_trailing_disclaimer()
        return
    section_count += 1
    story.append(Paragraph(f'Quarterly Consolidation \u2014 Change Log Coverage', S['h2']))
    story.append(Paragraph(
        f'This section is automatically generated from the monthly regulatory change logs available '
        f'in the system for <b>{quarter_display}</b>.',
        S['body_small']
    ))
    story.append(Spacer(1, 3*mm))

    coverage_rows = []
    available_months = []
    for m in quarter_months:
        cl = available_changelogs.get(m)
        if not cl:
            coverage_rows.append([m, "NO", "—", "—", "—"])
            continue
        available_months.append(m)
        coverage_rows.append([
            m,
            "YES",
            str(cl.get("total_regulations_tracked", "—")),
            str(cl.get("total_changes_detected", "—")),
            str(len(cl.get("critical_actions") or [])),
        ])

    story.append(pro_table(
        ['Month', 'Log Available', '# Tracked', '# Changes', '# Critical'],
        coverage_rows,
        [60, 80, 60, 60, 60],
        S
    ))
    story.append(Paragraph(
        f'Table 1: Monthly change log availability and headline metrics for {quarter_display}.',
        S['caption']
    ))
    story.append(Spacer(1, 3*mm))

    # Topic-level consolidation across available months
    topic_order = ["ghg", "packaging", "water", "waste", "social_human_rights"]
    priority = {"law_passed": 3, "amendment_in_progress": 2, "change_under_discussion": 1}

    topic_rows = []
    for t in topic_order:
        months_with_change = []
        best_level = None
        for m in available_months:
            cl = available_changelogs.get(m, {})
            status = (cl.get("topic_change_statuses") or {}).get(t) or {}
            if status.get("changed_since_last"):
                months_with_change.append(m)
                lvl = status.get("level")
                if lvl and (best_level is None or priority.get(lvl, 0) > priority.get(best_level, 0)):
                    best_level = lvl

        topic_rows.append([
            _topic_label(t),
            "YES" if months_with_change else "NO",
            _status_label(best_level) if months_with_change else "—",
            ", ".join(months_with_change) if months_with_change else "—",
        ])

    story.append(pro_table(
        ['Topic', f'Any Change in {quarter_display}', 'Highest Level Observed', 'Months with Change'],
        topic_rows,
        [95, 80, 140, 115],
        S
    ))
    story.append(Paragraph(
        f'Table 2: Per-topic consolidation of change signals across {quarter_display}.',
        S['caption']
    ))
    story.append(Spacer(1, 6*mm))

    if len(available_months) != len(quarter_months):
        story.append(callout_box(
            'Data Coverage Note',
            f'One or more monthly change logs for {quarter_display} are not yet available. '
            f'Interpretation of quarterly consolidation should consider these missing inputs.',
            S,
            accent_color=C_ALERT_AMBER
        ))
        story.append(Spacer(1, 6*mm))

    # ── Impact Summary Table — aggregated across all available months ──
    agg_impact_headers = []
    agg_impact_rows = []
    seen_impact_keys: set = set()
    for _period, cl in sorted(available_changelogs.items()):
        impact_data = cl.get("impact_summary_table") or {}
        if not agg_impact_headers and impact_data.get("headers"):
            agg_impact_headers = impact_data["headers"]
        for row in impact_data.get("rows") or []:
            key = row[0] if row else ""
            if key and key not in seen_impact_keys:
                seen_impact_keys.add(key)
                agg_impact_rows.append(row)
    if agg_impact_headers and agg_impact_rows:
        col_count = len(agg_impact_headers)
        col_w = (PAGE_W - 50*mm) / col_count
        story.append(Paragraph('Quarterly Impact Overview', S['h2']))
        story.append(pro_table(agg_impact_headers, agg_impact_rows, [col_w] * col_count, S))
        story.append(Paragraph('Table 3: Quarterly regulatory impact summary.', S['caption']))
        story.append(Spacer(1, 8*mm))


    # ── Sections — aggregated across all available months, dedupe by heading ──
    seen_headings: set = set()
    agg_sections = []
    for _period, cl in sorted(available_changelogs.items()):
        for section in cl.get("sections") or []:
            heading = section.get("heading", "")
            if heading not in seen_headings:
                seen_headings.add(heading)
                agg_sections.append(section)
    for section in agg_sections:
        heading = section.get("heading", "")
        if heading:
            story.append(Paragraph(heading, S['h1']))

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
                story.append(pro_table(headers, rows, [col_w] * col_count, S))
                story.append(Paragraph('', S['caption']))

        callout_text = section.get("callout")
        if callout_text:
            story.append(callout_box(None, callout_text, S))

        story.append(Spacer(1, 8*mm))

    # ── References (evidence_refs deduped across all months + top-level refs) ──
    evidence_ids_used = set()
    for cl in available_changelogs.values():
        for section in cl.get("sections") or []:
            evidence_ids_used.update(section.get("evidence_refs") or [])

    # Collect top-level refs from all available months, dedupe by url
    seen_urls = set()
    top_level_refs = []
    for cl in available_changelogs.values():
        for ref in cl.get("references") or []:
            key = ref.get("url") or ref.get("citation", "")
            if key and key not in seen_urls:
                seen_urls.add(key)
                top_level_refs.append(ref)

    if evidence_ids_used or top_level_refs:
        story.append(PageBreak())
        story.append(Paragraph('References', S['h1']))
        story.append(Paragraph(
            'The following sources underpin the analysis in this report.',
            S['body_small']
        ))
        story.append(Spacer(1, 3*mm))

        citation_index = 1

        if evidence_ids_used:
            from report_engine import ReportEngine as _RE
            evidence_records = _RE().load_client_evidence(client_id)
            for ev_id in sorted(evidence_ids_used):
                rec = evidence_records.get(ev_id)
                if not rec:
                    continue
                citation = (
                    f'<b>[{citation_index}]</b> <i>{rec["document_title"]}</i>. '
                    f'{rec["source_name"]}. '
                    f'Accessed {rec["access_date"]}. '
                    f'<link href="{rec["url"]}" color="{brand["primary_hex"]}">{rec["url"]}</link>'
                )
                story.append(Paragraph(citation, S['body_small']))
                story.append(Spacer(1, 2*mm))
                citation_index += 1

        for ref in top_level_refs:
            url = ref.get("url", "")
            citation_text = ref.get("citation", "")
            access_date = ref.get("access_date", "n/a")
            line = (
                f'<b>[{citation_index}]</b> <i>{citation_text}</i>. '
                f'Accessed {access_date}. '
                f'<link href="{url}" color="{brand["primary_hex"]}">{url}</link>'
            ) if url else (
                f'<b>[{citation_index}]</b> <i>{citation_text}</i>. '
                f'Accessed {access_date}.'
            )
            story.append(Paragraph(line, S['body_small']))
            story.append(Spacer(1, 2*mm))
            citation_index += 1

    _render_trailing_disclaimer()


# ══════════════════════════════════════════════════════════════════
# Build Document
# ══════════════════════════════════════════════════════════════════
def build_pdf(period: str = _DEFAULT_PERIOD, client_id: str | None = None, output_path: str | None = None, preferences: dict | None = None):
    S = build_styles()

    if client_id is None:
        raise ValueError("client_id is required to load quarterly changelogs")

    quarter_months = _quarter_months_for_period(period)
    quarter_display = _quarter_for_period(period)

    # Load changelogs to extract client_context from the latest available
    available_changelogs = {}
    for m in quarter_months:
        cl = _load_monthly_changelog(client_id, m)
        if cl:
            available_changelogs[m] = cl

    if not available_changelogs:
        raise ValueError(
            f"No changelogs found for client '{client_id}' in quarter months {quarter_months}."
        )

    latest_period = max(available_changelogs.keys())
    client_context = available_changelogs[latest_period].get("client_context") or {}
    brand = _load_branding(client_id, client_context)

    out_file = output_path or os.path.join(
        OUTPUT_DIR,
        f'Visusta_Quarterly_Strategic_Brief_{quarter_display.replace(" ", "_")}.pdf'
    )

    cover_frame = Frame(0, 0, PAGE_W, PAGE_H, leftPadding=25*mm, rightPadding=25*mm,
                        topPadding=10*mm, bottomPadding=10*mm, id='cf')
    content_frame = Frame(25*mm, 22*mm, PAGE_W - 50*mm, PAGE_H - 45*mm, id='ctf')

    on_page = _make_on_page(quarter_display, brand)
    doc = BaseDocTemplate(
        out_file, pagesize=A4,
        pageTemplates=[
            PageTemplate(id='cover', frames=[cover_frame], onPage=on_cover),
            PageTemplate(id='content', frames=[content_frame], onPage=on_page),
        ],
        title=f'{brand["display_name"]} Quarterly Strategic Brief \u2014 {quarter_display}',
        author=brand["display_name"],
        subject=f'{brand["display_name"]} Quarterly Strategic Brief',
        creator='Regulatory report builder'
    )

    story = []
    build_cover(story, S, quarter_display=quarter_display, client_context=client_context, brand=brand)
    story.append(NextPageTemplate('content'))
    build_content(story, S, quarter_months=quarter_months, quarter_display=quarter_display, client_id=client_id, brand=brand, preferences=preferences)
    os.makedirs(os.path.dirname(out_file) or ".", exist_ok=True)
    doc.build(story)

    print(f'\u2713 Quarterly Brief saved: {out_file}')
    print(f'  Size: {os.path.getsize(out_file) / 1024:.0f} KB')
    return out_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Build Visusta Quarterly Strategic Brief PDF.'
    )
    parser.add_argument(
        '--client-id',
        required=True,
        help='Client identifier used to load regulatory_data/<client_id>/changelogs',
    )
    parser.add_argument(
        '--period',
        default=_DEFAULT_PERIOD,
        help='Any period within the target quarter in YYYY-MM format (default: %(default)s)',
    )
    args = parser.parse_args()
    build_pdf(period=args.period, client_id=args.client_id)
