#!/usr/bin/env python3
"""
VISUSTA — Monthly Regulatory Impact Report (February 2026)
Enterprise-grade PDF with charts, tables, and full references.
"""

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
OUT_FILE = os.path.join(OUTPUT_DIR, 'Visusta_Monthly_Impact_Report_Feb2026.pdf')
SCREENING_PERIOD = "2026-02"


def _load_monthly_changelog(period: str):
    path = os.path.join(OUTPUT_DIR, "regulatory_data", "changelogs", f"{period}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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
def _draw_header_footer(canvas_obj, doc, is_cover=False):
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
        canvas_obj.drawRightString(PAGE_W - 25*mm, PAGE_H - 16*mm,
                                   'Monthly Regulatory Impact Report | February 2026')

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


def on_cover(canvas_obj, doc):
    _draw_header_footer(canvas_obj, doc, is_cover=True)

def on_page(canvas_obj, doc):
    _draw_header_footer(canvas_obj, doc, is_cover=False)


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
def build_cover(story, styles):
    # Full-page dark green background via a table
    cover_content = []
    cover_content.append(Spacer(1, 45*mm))

    # Logo text
    cover_content.append(Paragraph(
        '<font size="12" color="#8FB8A2">visusta</font>  '
        '<font size="9" color="#5F9A7E">— make visions real.</font>',
        ParagraphStyle('logo', fontName='Helvetica-Bold', fontSize=12, leading=16,
                       textColor=HexColor('#8FB8A2'), alignment=TA_LEFT)
    ))
    cover_content.append(Spacer(1, 25*mm))

    # Title block
    cover_content.append(Paragraph(
        'Monthly Regulatory<br/>Impact Report',
        styles['cover_title']
    ))
    cover_content.append(Spacer(1, 4*mm))
    cover_content.append(Paragraph(
        'EU &amp; German Sustainability Frameworks<br/>for Food Manufacturers',
        styles['cover_subtitle']
    ))
    cover_content.append(Spacer(1, 12*mm))

    # Divider line
    cover_content.append(HRFlowable(
        width='60%', thickness=1, color=HexColor('#2E8B63'),
        spaceBefore=0, spaceAfter=12, hAlign='LEFT'
    ))

    # Meta info
    meta_style = styles['cover_meta']
    cover_content.append(Paragraph('<b>Reporting Period:</b>  February 2026', meta_style))
    cover_content.append(Paragraph('<b>Date of Issue:</b>  February 1, 2026', meta_style))
    cover_content.append(Paragraph(
        '<b>Prepared for:</b>  Executive Leadership, Regulatory Affairs &amp; Operations',
        meta_style
    ))
    cover_content.append(Paragraph(
        '<b>Facilities:</b>  Hamburg &amp; Rietberg, Federal Republic of Germany',
        meta_style
    ))
    cover_content.append(Spacer(1, 30*mm))

    # Classification
    cover_content.append(Paragraph(
        '<font size="8" color="#5F9A7E">CLASSIFICATION: CONFIDENTIAL — INTERNAL USE ONLY</font>',
        ParagraphStyle('class', fontName='Helvetica', fontSize=8, textColor=HexColor('#5F9A7E'))
    ))

    # Build as a full-page table with dark background
    inner = []
    for item in cover_content:
        inner.append([item])

    cover_table = Table(inner, colWidths=[PAGE_W - 50*mm])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_PRIMARY_DARK),
        ('LEFTPADDING', (0, 0), (-1, -1), 20*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15*mm),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    # Outer wrapper to fill margins
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
def build_content(story, styles):
    S = styles
    body = S['body']

    # ── Executive Summary ──
    story.append(Paragraph('Executive Summary', S['h1']))
    story.append(Paragraph(
        'This Monthly Impact Report covers the regulatory developments directly affecting '
        'food manufacturing operations at the Hamburg and Rietberg facilities during February 2026. '
        'The convergence of new Hamburg municipal fee structures, the imminent finalization of the '
        'German Packaging Law Implementation Act (VerpackDG), and the retroactive abolition of LkSG '
        'reporting obligations creates a complex compliance environment demanding immediate operational '
        'recalibration.',
        body
    ))
    story.append(Paragraph(
        'The most significant financial impacts this month stem from the 3.3% increase in Hamburg '
        'industrial wastewater and utility fees (effective January 1, 2026, with first invoicing in '
        'February) and the new Extended Producer Responsibility (EPR) framework for B2B packaging '
        'under the draft VerpackDG, which introduces a levy of approximately \u20ac5 per tonne on '
        'transport and industrial packaging.',
        body
    ))
    story.append(Spacer(1, 3*mm))

    # ── Technical Screening Summary (Change Log) ──
    changelog = _load_monthly_changelog(SCREENING_PERIOD)
    if changelog:
        story.append(Paragraph('Technical Screening Summary (Change Log)', S['h2']))
        story.append(Paragraph(
            f'This section is generated from the monthly regulatory change log for <b>{SCREENING_PERIOD}</b> '
            f'(previous period: <b>{changelog.get("previous_period","")}</b>). It reports per-topic whether '
            f'there was a change since last reporting and, if so, at which level.',
            S['body_small']
        ))
        story.append(Spacer(1, 3*mm))

        topic_rows = []
        statuses = changelog.get("topic_change_statuses") or {}
        topic_order = ["ghg", "packaging", "water", "waste", "social_human_rights"]
        for topic in topic_order:
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

        # Flatten changed entries (exclude carried_forward)
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
                'Table 2: Extract of detected changes for this month (for full details use the JSON change log).',
                S['caption']
            ))
            story.append(Spacer(1, 6*mm))

    # ── Impact Summary Table ──
    impact_headers = ['Regulation', 'Status', 'Impact Level', 'Action Required']
    impact_rows = [
        ['Hamburg Wastewater Fees', 'Effective Jan 1, 2026', 'HIGH — Direct OPEX',
         'Audit Feb invoices; recalculate water efficiency ROI'],
        ['NRW Circular Economy (NKWS)', 'Strategic Alignment', 'MEDIUM — Strategic',
         'Engage EFA NRW for funding; prepare waste hierarchy audit'],
        ['VerpackDG (B2B EPR)', 'Draft — Q1 Adoption Expected', 'CRITICAL — New Liability',
         'Quantify B2B packaging tonnage; evaluate OfH membership'],
        ['LkSG Reporting Abolition', 'Retroactive from Jan 2023', 'LOW — Admin Relief',
         'Redirect resources to CSDDD/CSRD preparation'],
    ]
    impact_block = [
        Paragraph('Monthly Impact Overview', S['h2']),
        pro_table(impact_headers, impact_rows, [95, 100, 90, 175], styles),
        Paragraph('Table 3: Monthly regulatory impact summary for February 2026.', S['caption']),
        Spacer(1, 6*mm),
    ]
    story.append(KeepTogether(impact_block))

    # ══════════════════════════════════════════════════════════════
    # Section 1: Hamburg Municipal Fees
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph('1. Hamburg Industrial Wastewater &amp; Utility Fee Restructuring', S['h1']))

    story.append(status_badge('EFFECTIVE — JAN 1, 2026', C_ALERT_RED, styles))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph(
        'The Free and Hanseatic City of Hamburg has enacted significant adjustments to its municipal '
        'fee structures effective January 1, 2026, approved by the Senate in late 2025. These changes '
        'are driven by rising personnel and material costs within the Hamburger Stadtentwässerung (HSE) '
        'and broader sanitation services. For food manufacturers with wet processing operations in '
        'the region, these adjustments translate into immediate increases in operational expenditure '
        '(OPEX).',
        body
    ))
    story.append(Paragraph(
        'The <i>Schmutzwassergebühr</i> (foul water fee) and <i>Niederschlagswassergebühr</i> '
        '(rainwater fee) have both increased by approximately 3.3%. While this percentage may appear '
        'moderate in isolation, the compound effect on annual utility costs for high-volume industrial '
        'users is substantial. The fee calculation logic remains based on freshwater consumption '
        'volumes for wastewater and sealed surface area for rainwater.',
        body
    ))
    story.append(Spacer(1, 3*mm))

    # Chart: Hamburg Fees
    chart_path = os.path.join(CHART_DIR, 'hamburg_fees.png')
    if os.path.exists(chart_path):
        img = Image(chart_path, width=155*mm, height=87*mm)
        story.append(img)
        story.append(Paragraph(
            'Figure 1: Hamburg municipal fee adjustments by category, effective January 2026.',
            S['caption']
        ))
    story.append(Spacer(1, 3*mm))

    # Fee Details Table
    story.append(Paragraph('1.1 Fee Adjustment Details', S['h2']))
    fee_headers = ['Fee Category', 'Adjustment', 'Mechanism', 'Operational Implication']
    fee_rows = [
        ['Schmutzwasser (Wastewater)', '+3.3%', 'Volumetric (freshwater intake)',
         'Direct cost increase for washing, blanching, CIP processes'],
        ['Niederschlagswasser (Rainwater)', '+3.3%', 'Area-based (sealed surfaces)',
         'Higher costs for warehouse roofs/lots; incentivizes green roofs'],
        ['Waste Disposal (Müllabfuhr)', '+3.4%', 'Volume/Frequency',
         'Higher general facility waste costs; reinforces recycling'],
        ['Administrative Fees', 'Varied', 'Per transaction',
         'Significant increase in special permits (e.g., Zweckentfremdung)'],
    ]
    story.append(pro_table(fee_headers, fee_rows, [88, 70, 88, 214], styles))
    story.append(Paragraph(
        'Table 4: Detailed breakdown of Hamburg municipal fee adjustments.',
        S['caption']
    ))
    story.append(Spacer(1, 3*mm))

    # Action box
    story.append(callout_box(
        '\u26a0  Immediate Action Required',
        'Facility managers in Hamburg must audit the February 2026 utility invoices. Verification '
        'should focus on the application of the new unit rates against metered volumes from January. '
        'The 3.3% increase alters the ROI calculus for water efficiency projects. Technologies such '
        'as membrane bioreactors (MBR) for wastewater recycling or condensate recovery systems, '
        'which may have been borderline viable in 2024, may now meet internal hurdle rates for '
        'CAPEX approval.',
        styles, accent_color=C_ALERT_AMBER
    ))
    story.append(Spacer(1, 8*mm))

    # ══════════════════════════════════════════════════════════════
    # Section 2: NRW Circular Economy
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph('2. North Rhine-Westphalia (NRW) Circular Economy Implementation', S['h1']))

    story.append(status_badge('STRATEGIC — ALIGNMENT PHASE', C_PRIMARY, styles))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph(
        'In Rietberg, the regulatory environment is heavily influenced by the NRW state government\'s '
        'aggressive implementation of the National Circular Economy Strategy (NKWS), adopted at the '
        'federal level in December 2024. NRW, as a densely populated industrial hub, is piloting '
        'several initiatives to decouple economic activity from resource consumption.',
        body
    ))
    story.append(Paragraph(
        'The NRW strategy specifically targets the food and beverage sector. Aligning with UN SDG 12.3, '
        'the state has committed to halving per capita food waste at retail and consumer levels by 2030, '
        'and significantly reducing food losses along production and supply chains. This is translating '
        'into stricter reporting requirements for industrial food waste. The emphasis is shifting from '
        '"safe disposal" to "highest value retention" — diverting food waste to biogas generation '
        '(energy recovery) is becoming the <i>minimum</i> standard, with nutrient recovery or animal '
        'feed production being the preferred tier.',
        body
    ))
    story.append(Spacer(1, 3*mm))

    story.append(callout_box(
        '\u2713  Strategic Opportunity',
        'The Rietberg facility management should engage with the <b>Effizienz-Agentur NRW (EFA)</b> '
        'to identify potential funding for circularity projects. The "Circularity Made in Germany" '
        'seal, introduced with the NKWS, offers a reputational advantage for B2B suppliers. '
        'Additionally, the Federal Environment Agency is developing a "National Urban Mining Strategy" '
        'by 2026, and NRW is likely to offer matching grants for industrial symbiosis projects.',
        styles, accent_color=C_ACCENT
    ))
    story.append(Spacer(1, 8*mm))

    # ══════════════════════════════════════════════════════════════
    # Section 3: VerpackDG
    # ══════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph('3. German Packaging Law Implementation Act (VerpackDG)', S['h1']))

    story.append(status_badge('CRITICAL — ADOPTION IMMINENT Q1 2026', C_ALERT_RED, styles))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph(
        'The most significant looming regulatory change is the finalization of the '
        '<i>Verpackungs-Durchführungsgesetz</i> (VerpackDG). This new act replaces the existing '
        'Packaging Act (VerpackG) and serves as the national execution vehicle for the EU PPWR. '
        'The draft introduces a <b>paradigm shift</b> for commercial and industrial packaging.',
        body
    ))

    story.append(Paragraph('3.1 Expansion of EPR to B2B Packaging', S['h2']))
    story.append(Paragraph(
        'Under the previous regime, manufacturers of transport packaging and industrial packaging (B2B) '
        'were required to register with the LUCID system but were largely exempt from financial '
        'participation obligations. The new draft mandates that manufacturers of non-system-participating '
        'packaging must now assume financial responsibility by either joining an authorized '
        '"Organisation for Producer Responsibility" (OfH) or establishing an approved individual '
        'take-back system.',
        body
    ))

    story.append(Paragraph('3.2 Financial Impact Analysis', S['h2']))
    story.append(Paragraph(
        'A new levy of approximately <b>\u20ac5 per tonne</b> is proposed for all packaging handled '
        'by EPR schemes or individual compliers, intended to fund waste prevention and reuse measures '
        'managed by the Central Agency (ZSVR). Additional service fees from OfH providers are estimated '
        'at \u20ac3 per tonne. The following chart illustrates the projected annual cost exposure by '
        'B2B packaging volume:',
        body
    ))
    story.append(Spacer(1, 3*mm))

    chart_path2 = os.path.join(CHART_DIR, 'verpackdg_cost.png')
    if os.path.exists(chart_path2):
        img2 = Image(chart_path2, width=155*mm, height=83*mm)
        story.append(img2)
        story.append(Paragraph(
            'Figure 2: Estimated annual EPR cost exposure under VerpackDG by B2B packaging volume.',
            S['caption']
        ))
    story.append(Spacer(1, 3*mm))

    # Recycling targets table
    story.append(Paragraph('3.3 Recycling Targets for B2B Packaging Materials', S['h2']))
    target_headers = ['Material Stream', '2028 Target', '2030 Target', 'Mechanical Only?']
    target_rows = [
        ['Plastics (B2B)', '75%', '80%', 'Mechanical baseline + chemical for gap'],
        ['Paper / Cardboard', '85%', '90%', 'Mechanical preferred'],
        ['Metals (Steel / Aluminium)', '80%', '85%', 'N/A'],
        ['Wood', '30%', '35%', 'N/A'],
    ]
    story.append(pro_table(target_headers, target_rows, [120, 80, 80, 180], styles))
    story.append(Paragraph(
        'Table 5: VerpackDG recycling targets for non-system-participating (B2B) packaging.',
        S['caption']
    ))
    story.append(Spacer(1, 3*mm))

    story.append(callout_box(
        '\u26a0  Immediate Action Required',
        'Procurement and logistics teams must quantify the tonnage of transport packaging entering '
        'and leaving the Hamburg and Rietberg sites. The potential cost of \u20ac5/tonne plus OfH '
        'service fees represents a new logistics budget line item. Contracts with waste management '
        'providers (Remondis, Veolia, PreZero) must be reviewed to assess whether they are positioning '
        'as authorized OfH providers under the new framework.',
        styles, accent_color=C_ALERT_AMBER
    ))
    story.append(Spacer(1, 8*mm))

    # ══════════════════════════════════════════════════════════════
    # Section 4: LkSG
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph('4. Abolition of LkSG Reporting Obligations', S['h1']))

    story.append(status_badge('ADMINISTRATIVE RELIEF — RETROACTIVE', C_ACCENT, styles))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph(
        'The German Federal Cabinet passed a law amending the Supply Chain Due Diligence Act (LkSG), '
        'abolishing the reporting obligation under \u00a7 10 (2) LkSG with retroactive effect from '
        'January 1, 2023. Companies are no longer required to submit the annual report to BAFA.',
        body
    ))

    # Risk callout
    story.append(callout_box(
        '\u26a0  Risk of Misinterpretation',
        '<b>Only the reporting obligation has been removed.</b> The substantive obligations remain '
        'in full force: establishing a risk management system, conducting annual risk analyses, '
        'adopting a policy statement, and implementing preventive and remedial measures. BAFA retains '
        'authority to conduct risk-based controls and investigate complaints. Resources previously '
        'dedicated to BAFA report compilation should be redirected toward preparing for the EU '
        'CSDDD and CSRD.',
        styles, accent_color=C_ALERT_AMBER
    ))
    story.append(Spacer(1, 3*mm))

    # Comparison table
    story.append(Paragraph('4.1 LkSG vs. Upcoming CSDDD: Key Differences', S['h2']))
    comp_headers = ['Dimension', 'LkSG (Current)', 'CSDDD (Upcoming)']
    comp_rows = [
        ['Scope', 'Direct suppliers + known indirect', 'Full value chain incl. downstream'],
        ['Reporting', 'Abolished (retroactive)', 'Integrated with CSRD'],
        ['Liability', 'Administrative fines', 'Civil liability (damages claims)'],
        ['Threshold', '\u2265 1,000 employees', 'TBD (EU-level thresholds)'],
        ['Climate Plan', 'Not required', 'Mandatory transition plan'],
    ]
    story.append(pro_table(comp_headers, comp_rows, [80, 170, 210], styles))
    story.append(Paragraph(
        'Table 6: Comparison of German LkSG and upcoming EU CSDDD.',
        S['caption']
    ))
    story.append(Spacer(1, 8*mm))

    # ══════════════════════════════════════════════════════════════
    # Section 5: EWKFondsG
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph('5. Single-Use Plastic Fund (EWKFondsG) — Data Collection Phase', S['h1']))

    story.append(status_badge('ONGOING — 2026 DATA COLLECTION', C_ALERT_AMBER, styles))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph(
        'The <i>Einwegkunststofffondsgesetz</i> (EWKFondsG) establishes a "plastic tax" mechanism '
        'in Germany covering the costs of cleaning up litter in public spaces. The system is live '
        'and the current period (2026) is the data collection phase for the 2026 reporting cycle. '
        'Data for FY 2024 must be reported by May 15, 2025, with payments due shortly thereafter.',
        body
    ))
    story.append(Spacer(1, 3*mm))

    chart_path3 = os.path.join(CHART_DIR, 'ewk_levies.png')
    if os.path.exists(chart_path3):
        img3 = Image(chart_path3, width=145*mm, height=79*mm)
        story.append(img3)
        story.append(Paragraph(
            'Figure 3: EWKFondsG single-use plastic levy rates by packaging category.',
            S['caption']
        ))
    story.append(Spacer(1, 3*mm))

    story.append(callout_box(
        'Classification Risk',
        'The definition of "flexible material containing food intended for immediate consumption" '
        'is a frequent area of dispute. A wrapper for a chocolate bar is included; a wrapper for a '
        'multipack may not be. Accurate classification in the ERP system is essential to avoid '
        'overpayment or penalties for under-reporting.',
        styles, accent_color=C_WARM_GRAY
    ))
    story.append(Spacer(1, 8*mm))

    # ══════════════════════════════════════════════════════════════
    # References
    # ══════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph('References', S['h1']))
    story.append(Paragraph(
        'The following sources underpin the analysis in this report. All URLs were accessed on '
        'February 1, 2026.',
        S['body_small']
    ))
    story.append(Spacer(1, 3*mm))

    refs = [
        '[1] "Änderung städtischer Gebühren ab 2026," Hamburg.de — https://www.hamburg.de/politik-und-verwaltung/behoerden/finanzbehoerde/aktuelles/aenderung-staedtischer-gebuehren-ab-2026-1123310',
        '[2] "Hamburg erhöht 2026 Gebühren für Müllabfuhr und Abwasser," Hansetipp — https://www.hansetipp.de/hamburg-erhoeht-2026-gebuehren-fuer-muellabfuhr-und-abwasser/',
        '[3] "Drucksache 22/16672," Hamburgische Bürgerschaft — https://www.buergerschaft-hh.de/parldok/dokument/22/art/Drucksache/num/16672',
        '[4] "Germany: Circularity Made in Germany — The NKWS has been adopted," Baker McKenzie InsightPlus — https://insightplus.bakermckenzie.com/bm/environment-climate-change_1/germany-circularity-made-in-germany-the-national-circular-economy-strategy-nkws',
        '[5] "National Strategy for Food Waste Reduction," BMLEH — https://www.bmleh.de/EN/topics/food-and-nutrition/food-waste/national-strategy-for-food-waste-reduction.html',
        '[6] "National Circular Economy Strategy (NKWS)," IEA — https://www.iea.org/policies/24983-national-circular-economy-strategy-nkws',
        '[7] "Neues VerpackDG: Referentenentwurf vorgelegt," ZENTEK — https://www.zentek.de/referentenentwurf-fuer-ein-neues-verpackungsrecht-durchfuehrungsgesetz-verpackdg/',
        '[8] "Referentenentwurf (VerpackDG) — IHK resource," IHK — https://www.ihk.de/blueprint/servlet/resource/blob/6816162/3be581c7dddafeca305a04450943e5fa/verpackg-refentwurf-data.pdf',
        '[9] "Federal cabinet resolves reforms to the German Supply Chain Act and implementation of the CSRD," Noerr — https://www.noerr.com/en/insights/federal-cabinet-resolves-reforms-to-the-german-supply-chain-act-and-implementation-of-the-csrd',
        '[10] "Update on the Single-Use Plastics Fund Act: Plastic tax came into force on 1 January 2024," DLA Piper — https://www.dlapiper.com/en/insights/publications/2024/03/update-on-the-single-use-plastics-fund-act',
        '[11] "The German EWKFondsG explained," Noventiz — https://www.noventiz.de/en/the-german-einwegkunststofffondsgesetz-ewkfondsg-explained/',
    ]
    for ref in refs:
        story.append(Paragraph(ref, S['ref']))

    story.append(Spacer(1, 15*mm))

    # Disclaimer
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_BORDER, spaceBefore=4, spaceAfter=8))
    story.append(Paragraph(
        '<b>Disclaimer:</b> This report is based on regulatory data and legislative drafts available '
        'as of February 1, 2026. Legislative texts, particularly the German VerpackDG and the national '
        'implementation of CSRD, are subject to parliamentary amendment prior to final adoption. '
        'This document does not constitute legal advice.',
        ParagraphStyle('disclaimer', fontName='Helvetica', fontSize=7.5, leading=10,
                       textColor=C_MUTED, alignment=TA_JUSTIFY)
    ))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        '\u00a9 2026 visusta GmbH — visusta.ch — All rights reserved.',
        ParagraphStyle('footer_note', fontName='Helvetica', fontSize=7, leading=10,
                       textColor=C_MUTED, alignment=TA_CENTER)
    ))


# ══════════════════════════════════════════════════════════════════
# Build the Document
# ══════════════════════════════════════════════════════════════════
def build_pdf():
    styles = build_styles()

    # Define frames
    cover_frame = Frame(0, 0, PAGE_W, PAGE_H, leftPadding=25*mm, rightPadding=25*mm,
                        topPadding=10*mm, bottomPadding=10*mm, id='cover_frame')
    content_frame = Frame(25*mm, 22*mm, PAGE_W - 50*mm, PAGE_H - 45*mm,
                          id='content_frame')

    cover_template = PageTemplate(id='cover', frames=[cover_frame], onPage=on_cover)
    content_template = PageTemplate(id='content', frames=[content_frame], onPage=on_page)

    doc = BaseDocTemplate(
        OUT_FILE,
        pagesize=A4,
        pageTemplates=[cover_template, content_template],
        title='Visusta Monthly Regulatory Impact Report — February 2026',
        author='visusta GmbH',
        subject='EU & German Sustainability Regulatory Monitoring',
        creator='VARI — Visusta Autonomous Regulatory Intelligence'
    )

    story = []

    # Cover page
    build_cover(story, styles)
    story.append(NextPageTemplate('content'))

    # Content
    build_content(story, styles)

    doc.build(story)
    print(f'✓ Monthly Report saved: {OUT_FILE}')
    print(f'  Size: {os.path.getsize(OUT_FILE) / 1024:.0f} KB')


if __name__ == '__main__':
    build_pdf()
