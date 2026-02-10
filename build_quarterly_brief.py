#!/usr/bin/env python3
"""
VISUSTA — Quarterly Strategic Brief (Q1 2026)
Enterprise-grade PDF with charts, tables, timeline, and full references.
"""

import os
import json
from datetime import date
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
OUT_FILE = os.path.join(OUTPUT_DIR, 'Visusta_Quarterly_Strategic_Brief_Q1_2026.pdf')
QUARTER_MONTHS = ["2026-01", "2026-02", "2026-03"]


def _load_monthly_changelog(period: str):
    path = os.path.join(OUTPUT_DIR, "regulatory_data", "changelogs", f"{period}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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


# ══════════════════════════════════════════════════════════════════
# Page Templates
# ══════════════════════════════════════════════════════════════════
def _draw_header_footer(canvas_obj, doc, is_cover=False):
    canvas_obj.saveState()
    if not is_cover:
        # Top accent bar
        canvas_obj.setFillColor(C_PRIMARY_DARK)
        canvas_obj.rect(0, PAGE_H - 3*mm, PAGE_W, 3*mm, fill=1, stroke=0)

        # Header
        canvas_obj.setStrokeColor(C_PRIMARY)
        canvas_obj.setLineWidth(1.5)
        canvas_obj.line(25*mm, PAGE_H - 18*mm, PAGE_W - 25*mm, PAGE_H - 18*mm)

        canvas_obj.setFont('Helvetica-Bold', 8)
        canvas_obj.setFillColor(C_PRIMARY_DARK)
        canvas_obj.drawString(25*mm, PAGE_H - 16*mm, 'VISUSTA')
        canvas_obj.setFont('Helvetica', 7)
        canvas_obj.setFillColor(C_WARM_GRAY)
        canvas_obj.drawString(50*mm, PAGE_H - 16*mm, '— make visions real.')
        canvas_obj.setFillColor(C_MUTED)
        canvas_obj.drawRightString(PAGE_W - 25*mm, PAGE_H - 16*mm,
                                   'Quarterly Strategic Brief | Q1 2026')

        # Footer
        canvas_obj.setStrokeColor(C_BORDER)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(25*mm, 18*mm, PAGE_W - 25*mm, 18*mm)
        canvas_obj.setFont('Helvetica', 7)
        canvas_obj.setFillColor(C_MUTED)
        canvas_obj.drawString(25*mm, 13*mm, 'visusta GmbH | visusta.ch | Confidential')
        canvas_obj.drawRightString(PAGE_W - 25*mm, 13*mm, f'Page {doc.page}')
    canvas_obj.restoreState()

def on_cover(c, d): _draw_header_footer(c, d, True)
def on_page(c, d): _draw_header_footer(c, d, False)


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
def build_cover(story, S):
    items = []
    items.append(Spacer(1, 45*mm))
    items.append(Paragraph(
        '<font size="12" color="#8FB8A2">visusta</font>  '
        '<font size="9" color="#5F9A7E">\u2014 make visions real.</font>',
        ParagraphStyle('logo', fontName='Helvetica-Bold', fontSize=12, leading=16,
                       textColor=HexColor('#8FB8A2'))
    ))
    items.append(Spacer(1, 25*mm))
    items.append(Paragraph('Quarterly Strategic<br/>Brief', S['cover_title']))
    items.append(Spacer(1, 4*mm))
    items.append(Paragraph(
        'EU &amp; German Sustainability Frameworks<br/>'
        'Strategic Outlook for Food Manufacturers',
        S['cover_subtitle']
    ))
    items.append(Spacer(1, 12*mm))
    items.append(HRFlowable(width='60%', thickness=1, color=HexColor('#2E8B63'),
                             spaceBefore=0, spaceAfter=12, hAlign='LEFT'))
    m = S['cover_meta']
    items.append(Paragraph('<b>Reporting Period:</b>  Q1 2026 (January \u2013 March)', m))
    items.append(Paragraph('<b>Strategic Horizon:</b>  Q1 \u2013 Q4 2026', m))
    items.append(Paragraph('<b>Date of Issue:</b>  February 1, 2026', m))
    items.append(Paragraph('<b>Prepared for:</b>  Executive Leadership &amp; Board Advisory', m))
    items.append(Paragraph('<b>Facilities:</b>  Hamburg &amp; Rietberg, Germany', m))
    items.append(Spacer(1, 30*mm))
    items.append(Paragraph(
        '<font size="8" color="#5F9A7E">CLASSIFICATION: CONFIDENTIAL \u2014 INTERNAL USE ONLY</font>',
        ParagraphStyle('cls', fontName='Helvetica', fontSize=8, textColor=HexColor('#5F9A7E'))
    ))

    inner_rows = [[item] for item in items]
    ct = Table(inner_rows, colWidths=[PAGE_W - 50*mm])
    ct.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_PRIMARY_DARK),
        ('LEFTPADDING', (0,0), (-1,-1), 20*mm),
        ('RIGHTPADDING', (0,0), (-1,-1), 15*mm),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    outer = Table([[ct]], colWidths=[PAGE_W - 50*mm])
    outer.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_PRIMARY_DARK),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(outer)
    story.append(PageBreak())


# ══════════════════════════════════════════════════════════════════
# Content
# ══════════════════════════════════════════════════════════════════
def build_content(story, S):
    body = S['body']

    # ── Executive Summary ──
    story.append(Paragraph('Executive Summary', S['h1']))
    story.append(Paragraph(
        'This Quarterly Strategic Brief provides a medium-term outlook for food manufacturers '
        'operating from Hamburg and Rietberg, Germany. Q1 2026 represents a critical window '
        'for strategic alignment as multiple EU-level regulations converge: the EU Packaging and '
        'Packaging Waste Regulation (PPWR) approaches its August 2026 general application date, '
        'the EU Deforestation Regulation (EUDR) deadline moves to December 2026, and Germany '
        'finalizes its CSRD transposition to avoid infringement proceedings.',
        body
    ))
    story.append(Paragraph(
        'The regulatory environment in early 2026 is characterized by a "deceptive calm." '
        'The EUDR delay and LkSG reporting abolition may suggest loosening controls \u2014 this is '
        'a misinterpretation. The underlying trend is a shift from <i>process reporting</i> '
        '(filling questionnaires) to <i>performance mandates</i> (recyclability grades, '
        'deforestation-free verification, wastewater limits). This brief outlines the strategic '
        'imperatives and cost implications for the coming quarters.',
        body
    ))
    story.append(Spacer(1, 3*mm))

    # ── Quarterly Consolidation (Change Log Coverage) ──
    story.append(Paragraph('Quarterly Consolidation — Change Log Coverage', S['h2']))
    story.append(Paragraph(
        'This section is automatically generated from the monthly regulatory change logs available in the '
        'system for Q1 2026. It provides traceability and highlights data coverage gaps (if any).',
        S['body_small']
    ))
    story.append(Spacer(1, 3*mm))

    coverage_rows = []
    available_months = []
    for m in QUARTER_MONTHS:
        cl = _load_monthly_changelog(m)
        label = f"{m}-01"
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
        'Table 1: Monthly change log availability and headline metrics for Q1 2026.',
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
            cl = _load_monthly_changelog(m) or {}
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
        ['Topic', 'Any Change in Q1', 'Highest Level Observed', 'Months with Change'],
        topic_rows,
        [95, 80, 140, 115],
        S
    ))
    story.append(Paragraph(
        'Table 2: Per-topic consolidation of change signals across Q1 2026 (based on available logs).',
        S['caption']
    ))
    story.append(Spacer(1, 6*mm))

    if len(available_months) != len(QUARTER_MONTHS):
        story.append(callout_box(
            'Data Coverage Note',
            'One or more monthly change logs for Q1 2026 are not available in the system output directory. '
            'Interpretation of Q1 consolidation should consider these missing inputs.',
            S,
            accent_color=C_ALERT_AMBER
        ))
        story.append(Spacer(1, 6*mm))

    # ── Regulatory Timeline ──
    story.append(Paragraph('Regulatory Compliance Timeline \u2014 2026', S['h2']))
    chart = os.path.join(CHART_DIR, 'regulatory_timeline.png')
    if os.path.exists(chart):
        story.append(Image(chart, width=170*mm, height=100*mm))
        story.append(Paragraph(
            'Figure 1: Key regulatory milestones and compliance deadlines across 2026.',
            S['caption']
        ))
    story.append(Spacer(1, 6*mm))

    # Strategic Priority Matrix
    story.append(Paragraph('Strategic Priority Matrix', S['h2']))
    pri_h = ['Regulation', 'Priority', 'Deadline', 'Primary Impact Area', 'Investment Type']
    pri_r = [
        ['PPWR (Recyclability)', 'CRITICAL', 'Aug 12, 2026', 'R&amp;D, Packaging', 'CAPEX + R&amp;D'],
        ['VerpackDG (B2B EPR)', 'CRITICAL', 'Q3/Q4 2026', 'Logistics, Procurement', 'OPEX'],
        ['FCM Reg 2022/1616', 'HIGH', 'Jul 10, 2026', 'Packaging Supply Chain', 'Supplier Audit'],
        ['EmpCo (Green Claims)', 'HIGH', 'Sep 27, 2026', 'Marketing, Legal', 'Artwork Redesign'],
        ['EUDR', 'MEDIUM', 'Dec 30, 2026', 'Sourcing, IT', 'IT/API Integration'],
        ['CSRD Transposition', 'MEDIUM', 'TBD (Q2-Q3 2026)', 'Finance, Reporting', 'Data Architecture'],
    ]
    story.append(pro_table(pri_h, pri_r, [80, 55, 65, 105, 80], S))
    story.append(Paragraph(
        'Table 3: Strategic priority matrix for Q1\u2013Q4 2026 regulatory compliance.',
        S['caption']
    ))
    story.append(Spacer(1, 8*mm))

    # ══════════════════════════════════════════════════════════════
    # Section 1: PPWR Deep Dive
    # ══════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph('1. EU Packaging and Packaging Waste Regulation (PPWR)', S['h1']))
    story.append(status_badge('GENERAL APPLICATION: AUGUST 12, 2026', C_ALERT_RED, S))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph(
        'The PPWR entered into force on February 11, 2025, triggering an 18-month transition period '
        'culminating on August 12, 2026. Unlike the previous Directive 94/62/EC, the PPWR is a '
        '<b>Regulation</b> \u2014 it applies directly and uniformly across all EU Member States, '
        'removing national flexibility. Q1 2026 is the critical window for product and packaging '
        'development cycles (6\u201312 months lead time).',
        body
    ))

    # 1.1 Recyclability Grading
    story.append(Paragraph('1.1 Design for Recycling \u2014 The Grading System (Article 6)', S['h2']))
    story.append(Paragraph(
        'From January 1, 2030, all packaging will be graded on recyclability from A (\u226595%) '
        'to E (&lt;70%). Grade E packaging will be <b>effectively banned</b> from the EU market. '
        'Even Grade D may face punitive EPR fees under eco-modulation schemes. While the grading '
        'applies from 2030, the requirement for packaging to be <i>designed for recycling</i> applies '
        'from the general application date in August 2026.',
        body
    ))
    story.append(Spacer(1, 3*mm))

    chart2 = os.path.join(CHART_DIR, 'ppwr_grading.png')
    if os.path.exists(chart2):
        story.append(Image(chart2, width=155*mm, height=72*mm))
        story.append(Paragraph(
            'Figure 2: PPWR Design for Recycling grading scale with market exclusion threshold.',
            S['caption']
        ))
    story.append(Spacer(1, 3*mm))

    story.append(callout_box(
        'ZSVR Bridge Standard',
        'The German ZSVR "Minimum Standard" for 2025 acts as a de-facto bridge to PPWR compliance. '
        'It provides specific chemical and physical parameters (e.g., density of polyolefins, '
        'solubility of adhesives) currently used to assess recyclability in Germany. Any packaging '
        'format failing the current German standard will almost certainly receive a failing grade '
        '(D or E) under the future PPWR assessment.',
        S, accent_color=C_PRIMARY
    ))
    story.append(Spacer(1, 6*mm))

    # 1.2 Minimization
    story.append(Paragraph('1.2 Packaging Minimization Requirements (Article 9)', S['h2']))
    story.append(Paragraph(
        'The PPWR introduces strict requirements for packaging minimization. Weight and volume must '
        'be reduced to the minimum necessary for functionality (protection, hygiene, safety).',
        body
    ))

    min_h = ['Requirement', 'Specification', 'Affected Packaging Types']
    min_r = [
        ['Empty Space Ratio', 'Maximum 40% for grouped, transport, and e-commerce packaging',
         'Shelf-ready packaging (SRP), e-commerce boxes, retail display trays'],
        ['Perceived Volume', 'Prohibited: double walls, false bottoms (unless technically justified)',
         'Primary consumer packaging, promotional packaging'],
        ['Technical Documentation', 'Required for every SKU demonstrating compliance',
         'All packaging formats placed on EU market from Aug 2026'],
    ]
    story.append(pro_table(min_h, min_r, [85, 195, 180], S))
    story.append(Paragraph('Table 4: PPWR Article 9 packaging minimization requirements.', S['caption']))
    story.append(Spacer(1, 6*mm))

    # 1.3 Recycled Content
    story.append(Paragraph('1.3 Recycled Content Targets (Article 7)', S['h2']))
    story.append(Paragraph(
        'The PPWR mandates minimum recycled content in plastic packaging with ambitious 2030 and 2040 '
        'targets. Critically, the "Mirror Clause" stipulates that recycled content can only count '
        'toward targets if it originates from post-consumer plastic waste collected and recycled in '
        'the EU or in a third country with equivalent standards. This restricts the import of '
        'unverifiable recycled plastics from non-regulated jurisdictions.',
        body
    ))
    story.append(Spacer(1, 3*mm))

    chart3 = os.path.join(CHART_DIR, 'recycled_targets.png')
    if os.path.exists(chart3):
        story.append(Image(chart3, width=155*mm, height=83*mm))
        story.append(Paragraph(
            'Figure 3: PPWR mandatory recycled content targets for plastic packaging (2030 and 2040).',
            S['caption']
        ))
    story.append(Spacer(1, 3*mm))

    story.append(callout_box(
        '\u26a0  Supply Chain Risk',
        'Companies waiting until 2028\u20132029 to secure rPET supply contracts will likely face '
        'prohibitive prices or supply shortages. The availability of food-grade recycled polymers '
        '(rPET, rPP) is severely limited. Forward-buying agreements and partnerships with recyclers '
        'should be prioritized <b>now</b>.',
        S, accent_color=C_ALERT_AMBER
    ))
    story.append(Spacer(1, 8*mm))

    # ══════════════════════════════════════════════════════════════
    # Section 2: EUDR
    # ══════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph('2. EU Deforestation Regulation (EUDR)', S['h1']))
    story.append(status_badge('APPLICATION DATE: DECEMBER 30, 2026', C_ALERT_AMBER, S))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph(
        'The EUDR application date has been delayed by 12 months to December 30, 2026 for large '
        'and medium enterprises. This delay results from the unreadiness of the central Information '
        'System and the need for simplified compliance for low-risk countries \u2014 <b>not</b> '
        'a weakening of core requirements. The obligation to collect geolocation coordinates '
        '(latitude/longitude with 6 decimal places) for every plot of land producing relevant '
        'commodities remains unchanged.',
        body
    ))
    story.append(Paragraph(
        'The Port of Hamburg is a critical node for EUDR commodities (cocoa, coffee, soy, palm oil). '
        'Customs authorities will require the Reference Number of the Due Diligence Statement (DDS) '
        'to clear goods for free circulation. A failure in data transfer equals a failure to clear customs.',
        body
    ))

    eudr_h = ['Commodity', 'Hamburg Relevance', 'Data Requirement', 'Risk Level']
    eudr_r = [
        ['Cocoa', 'Major import via Port of Hamburg', 'Geolocation + DDS', 'HIGH'],
        ['Soy', 'Significant feed/ingredient import', 'Geolocation + DDS', 'HIGH'],
        ['Palm Oil', 'Ingredient supply chain', 'Geolocation + DDS', 'HIGH'],
        ['Coffee', 'Major import hub', 'Geolocation + DDS', 'MEDIUM'],
        ['Cattle (derivatives)', 'Processed products supply chain', 'Geolocation + DDS', 'MEDIUM'],
    ]
    story.append(pro_table(eudr_h, eudr_r, [70, 135, 100, 60], S))
    story.append(Paragraph('Table 5: EUDR commodity risk assessment for Hamburg operations.', S['caption']))
    story.append(Spacer(1, 3*mm))

    story.append(callout_box(
        'Action Plan',
        'Q1 and Q2 2026 should be treated as a "dry run" period. Sourcing teams must collect '
        'geolocation coordinates for all relevant commodity inputs. These datasets should be tested '
        'for completeness and format compatibility with the EU Traces platform. ERP systems '
        '(SAP, Oracle) must be integrated with the Information System API. Waiting until Q4 2026 '
        'will result in supply chain paralysis in January 2027.',
        S, accent_color=C_DEEP_BLUE
    ))
    story.append(Spacer(1, 8*mm))

    # ══════════════════════════════════════════════════════════════
    # Section 3: CSRD
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph('3. Corporate Sustainability Reporting Directive (CSRD)', S['h1']))
    story.append(status_badge('GERMAN TRANSPOSITION — FINAL STAGES', C_ALERT_AMBER, S))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph(
        'Germany missed the July 2024 deadline for transposing the CSRD, leading to infringement '
        'proceedings. The national implementation process is now in its final stages. A "Stop-the-Clock" '
        'directive at EU level has postponed sector-specific standards and non-EU company reporting '
        'by two years.',
        body
    ))
    story.append(Paragraph(
        'The German draft implementation act proposes significant relief: companies with fewer than '
        '1,000 employees may be exempted from the first wave of reporting (originally FY 2025, '
        'reporting in 2026). This is contingent on the final text. Monitoring the '
        '<i>Bundesgesetzblatt</i> (Federal Law Gazette) in Q1 2026 is essential.',
        body
    ))

    csrd_h = ['Reporting Wave', 'Companies', 'Reporting Year', 'Status']
    csrd_r = [
        ['Wave 1 (Already Active)', 'Large PIEs (>500 employees)', 'FY 2024 (report in 2025)',
         'Active \u2014 ESRS applies'],
        ['Wave 2 (Germany)', 'Large companies (\u22651,000 employees)', 'FY 2025 (report in 2026)',
         'Pending \u2014 German threshold may apply'],
        ['Wave 2b (Possible Reprieve)', 'Large companies (500\u20131,000 employees)',
         'Potentially FY 2027', 'Pending final German law'],
        ['Wave 3', 'Listed SMEs', 'FY 2026 (report in 2027)', 'Stop-the-Clock delay possible'],
    ]
    story.append(pro_table(csrd_h, csrd_r, [80, 115, 105, 160], S))
    story.append(Paragraph('Table 6: CSRD reporting wave timeline with German implementation status.', S['caption']))
    story.append(Spacer(1, 8*mm))

    # ══════════════════════════════════════════════════════════════
    # Section 4: FCM Regulation
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph('4. Food Contact Materials \u2014 The July 2026 Cliff Edge', S['h1']))
    story.append(status_badge('DEADLINE: JULY 10, 2026', C_ALERT_RED, S))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph(
        'Commission Regulation (EU) 2022/1616 establishes a new harmonized framework for recycled '
        'plastics in food contact materials (FCM). The transition period for "novel technologies" '
        'and legacy processes ends on <b>July 10, 2026</b>. After this date, only recycled plastics '
        'produced by a "suitable recycling technology" (currently primarily mechanical PET recycling) '
        'or authorized novel technologies can be placed on the market.',
        body
    ))

    fcm_h = ['Technology', 'Status', 'Food Contact Legality After Jul 2026']
    fcm_r = [
        ['Mechanical PET Recycling', 'Suitable Technology (Established)', '\u2705 Authorized'],
        ['Mechanical PP/HDPE Recycling (food-grade)', 'Novel Technology (EFSA assessment)',
         '\u26a0 Only if registered + authorized'],
        ['Solvent-based Polyolefin Recycling', 'Novel Technology (National provisional)',
         '\u274c Illegal unless EU-authorized by deadline'],
        ['Pyrolysis (Chemical Recycling)', 'Novel Technology (Mass balance debate)',
         '\u26a0 Only if registered + authorized'],
    ]
    story.append(pro_table(fcm_h, fcm_r, [130, 140, 190], S))
    story.append(Paragraph('Table 7: FCM recycling technology authorization status under Reg 2022/1616.', S['caption']))
    story.append(Spacer(1, 4*mm))

    story.append(callout_box(
        '\u26a0  Urgent Supplier Audit Required',
        'Manufacturers must audit packaging suppliers providing recycled content (other than '
        'mechanically recycled PET). Each supplier must provide evidence of their status under '
        'Reg 2022/1616 \u2014 specifically, their registration in the Union Register of technologies '
        'and processes. Failure to verify creates a risk of placing illegal food contact materials '
        'on the market.',
        S, accent_color=C_ALERT_RED
    ))
    story.append(Spacer(1, 8*mm))

    # ══════════════════════════════════════════════════════════════
    # Section 5: Green Claims
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph('5. Green Claims &amp; Anti-Greenwashing (EmpCo Directive)', S['h1']))
    story.append(status_badge('TRANSPOSITION DEADLINE: SEPTEMBER 27, 2026', C_ALERT_AMBER, S))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph(
        'The "Empowering Consumers for the Green Transition" (EmpCo) Directive, published in March '
        '2024, must be transposed by Member States by September 27, 2026. This directive fundamentally '
        'alters the landscape of environmental marketing by expanding the list of banned unfair '
        'commercial practices.',
        body
    ))

    claims_h = ['Banned Practice', 'Current Common Usage', 'Required Alternative']
    claims_r = [
        ['"Climate Neutral" based on offsetting',
         'Carbon credit labels on food packaging',
         'Claims must be based on actual lifecycle emission reductions within the value chain'],
        ['"CO2 Positive" based on offsets',
         'Marketing campaigns highlighting neutrality',
         'Scope 1, 2 & 3 reduction evidence required'],
        ['Generic environmental claims without substantiation',
         '"Eco-friendly," "Green Product" labels',
         'Must be verifiable with specific evidence and methodology'],
    ]
    story.append(pro_table(claims_h, claims_r, [120, 140, 200], S))
    story.append(Paragraph('Table 8: EmpCo Directive impact on food brand marketing claims.', S['caption']))
    story.append(Spacer(1, 4*mm))

    story.append(callout_box(
        'Marketing De-Risking',
        'Marketing departments must audit <b>all packaging artwork</b>. Any "Carbon Neutral" badges '
        'or claims based on offsetting must be phased out in the next design cycle to ensure inventory '
        'reaching shelves in Q4 2026 is compliant. In Germany, this will likely be transposed as an '
        'amendment to the <i>Gesetz gegen den unlauteren Wettbewerb</i> (UWG).',
        S, accent_color=C_ALERT_AMBER
    ))
    story.append(Spacer(1, 8*mm))

    # ══════════════════════════════════════════════════════════════
    # Section 6: Financial Impact
    # ══════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph('6. Consolidated Financial &amp; Budgetary Impact (2026)', S['h1']))

    story.append(Paragraph(
        'The convergence of these regulations creates a compounding cost effect. The following table '
        'summarizes the estimated regulatory cost drivers for the 2026 fiscal year:',
        body
    ))
    story.append(Spacer(1, 3*mm))

    fin_h = ['Regulatory Driver', 'Cost Component', 'Est. Magnitude', 'Timeline']
    fin_r = [
        ['Hamburg Wastewater', 'Increased unit rate', '+3.3% on sewer fees', 'Effective Jan 1, 2026'],
        ['VerpackDG (Draft)', 'New B2B EPR levy', '~\u20ac5.00/tonne', 'Expected Q3/Q4 2026'],
        ['EWKFondsG', 'Plastic levy', '\u20ac0.17\u2013\u20ac1.24/kg (item specific)', 'Accrual ongoing; payment May 2027'],
        ['PPWR Compliance', 'Redesign &amp; testing', 'One-off R&amp;D + tooling costs', 'Q1\u2013Q3 2026'],
        ['EUDR Logistics', 'Data administration', 'High admin/IT overhead', 'Ongoing through 2026'],
        ['FCM Supplier Audit', 'Verification & testing', 'Moderate (consultancy + lab)', 'Q1\u2013Q2 2026'],
        ['EmpCo Artwork Redesign', 'Packaging artwork reprint', 'Moderate (per SKU)', 'Q2\u2013Q3 2026'],
    ]
    story.append(pro_table(fin_h, fin_r, [95, 100, 120, 145], S))
    story.append(Paragraph('Table 9: Estimated 2026 regulatory cost drivers across all frameworks.', S['caption']))
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph('6.1 Capital Investment Requirements', S['h2']))
    inv_h = ['Investment Area', 'Purpose', 'Priority', 'Est. Timeframe']
    inv_r = [
        ['Logistics IT / API Integration', 'EUDR Information System + OfH reporting', 'HIGH', 'Q1\u2013Q2 2026'],
        ['Production Machinery (Labelling)', 'Dynamic QR coding for PPWR digital compliance', 'MEDIUM', 'Q2\u2013Q3 2026'],
        ['Water Efficiency (Hamburg)', 'MBR/condensate recovery to offset fee hikes', 'MEDIUM', 'Q2\u2013Q4 2026'],
        ['R&amp;D Packaging Redesign', 'Mono-material transition, minimization, rPET sourcing', 'CRITICAL', 'Q1\u2013Q3 2026'],
    ]
    story.append(pro_table(inv_h, inv_r, [120, 170, 60, 110], S))
    story.append(Paragraph('Table 10: Priority capital investment requirements for 2026 compliance.', S['caption']))
    story.append(Spacer(1, 8*mm))

    # ══════════════════════════════════════════════════════════════
    # Section 7: Strategic Roadmap
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph('7. Strategic Roadmap \u2014 Q1 2026 Recommended Actions', S['h1']))
    story.append(Paragraph(
        'For the Hamburg facility, the strategic imperative is <b>digital logistics</b>: the ability '
        'to attach a geolocation dataset to a shipment of cocoa or soy is now as important as the '
        'physical bill of lading. For the Rietberg facility, the imperative is <b>circular engineering</b>: '
        'aligning with the NRW strategy and VerpackDG requirements means ensuring that every kilogram '
        'of packaging and every liter of wastewater is minimized, valorized, or recycled.',
        body
    ))
    story.append(Spacer(1, 4*mm))

    roadmap = [
        ('\u2776', 'Audit B2B Packaging',
         'Immediately quantify the volume of transport packaging used. Calculate potential financial '
         'exposure under the new VerpackDG levy (\u20ac5/tonne) and prepare to join an authorized OfH.'),
        ('\u2777', 'Verify Recycled Plastic Sources',
         'Launch a supplier audit to ensure all recycled plastic materials (FCM) are supported by a '
         'valid authorization or "novel technology" registration under EU 2022/1616 before July 2026.'),
        ('\u2778', 'Marketing De-Risking',
         'Initiate the phase-out of "Climate Neutral" claims on all packaging artwork to ensure '
         'compliance with the EmpCo Directive by late 2026.'),
        ('\u2779', 'EUDR Data Pilot',
         'Utilize the 12-month delay to run full-scale data collection pilots with high-risk suppliers, '
         'identifying gaps without the threat of immediate trade disruption.'),
        ('\u277a', 'PPWR Portfolio Audit',
         'Audit the entire packaging portfolio against the ZSVR 2025 Minimum Standard. Prioritize '
         'mono-material transition and secure rPET forward-buying agreements.'),
        ('\u277b', 'Water Efficiency Business Case',
         'Recalculate ROI for MBR and condensate recovery systems in Hamburg given the 3.3% fee hike. '
         'Submit CAPEX proposals by end of Q1 2026.'),
    ]

    for num, title, desc in roadmap:
        story.append(Paragraph(
            f'<b><font color="{C_PRIMARY.hexval()}">{num}</font>  {title}</b>',
            S['h3']
        ))
        story.append(Paragraph(desc, body))
        story.append(Spacer(1, 2*mm))

    story.append(Spacer(1, 8*mm))

    # ══════════════════════════════════════════════════════════════
    # References
    # ══════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph('References', S['h1']))
    story.append(Paragraph(
        'The following sources underpin the analysis in this report. All URLs were accessed on '
        'February 1, 2026.', S['body_small']
    ))
    story.append(Spacer(1, 3*mm))

    refs = [
        '[1] "Änderung städtischer Gebühren ab 2026," Hamburg.de — https://www.hamburg.de/politik-und-verwaltung/behoerden/finanzbehoerde/aktuelles/aenderung-staedtischer-gebuehren-ab-2026-1123310',
        '[6] "Germany: Circularity Made in Germany — The NKWS has been adopted," Baker McKenzie — https://insightplus.bakermckenzie.com/bm/environment-climate-change_1/germany-circularity-made-in-germany-the-national-circular-economy-strategy-nkws',
        '[11] "Germany — New Draft of The VerpackDG," Recoup — https://www.recoup.org/members-update/germany-new-draft-of-the-packaging-law-implementation-act-verpackdg/',
        '[13] "Unpacking Germany\'s Draft Packaging Act 2025," ComplianceAndRisks — https://www.complianceandrisks.com/blog/unpacking-germanys-draft-packaging-act-2025-what-is-new-and-what-stays-the-same/',
        '[14] "Neues VerpackDG: Referentenentwurf vorgelegt," ZENTEK — https://www.zentek.de/referentenentwurf-fuer-ein-neues-verpackungsrecht-durchfuehrungsgesetz-verpackdg/',
        '[17] "Germany — Federal government abolishes reporting obligations under the LKSG," GlobalNorm — https://compliance.globalnorm.de/en/product-compliance-news/detail/germany-federal-government-abolishes-reporting-obligations-under-the-lksg/',
        '[20] "Packaging waste — European Commission," environment.ec.europa.eu — https://environment.ec.europa.eu/topics/waste-and-recycling/packaging-waste_en',
        '[22] "Packaging and packaging waste (from 2026)," EUR-Lex — https://eur-lex.europa.eu/EN/legal-content/summary/packaging-and-packaging-waste-from-2026.html',
        '[24] "2025 minimum standard published," ZSVR — https://www.verpackungsregister.org/en/foundation-authority/press-media-section/newsdetail/2025-minimum-standard-published',
        '[29] "European Commission Proposes Further One-Year Delay to the EUDR," Latham & Watkins — https://www.lw.com/en/insights/european-commission-proposes-further-one-year-delay-to-the-eu-deforestation-regulation',
        '[33] "Germany Moves Forward with CSRD Transposition," Debevoise — https://www.debevoise.com/insights/publications/2025/09/germany-moves-forward-with-csrd-transposition',
        '[37] "Commission Regulation (EU) 2022/1616 on recycled plastic materials," CCRI — https://circular-cities-and-regions.ec.europa.eu/support-materials/eu-regulations-legislation/commission-regulation-eu-20221616-recycled-plastic',
        '[38] "New Recycling Regulation for Plastic Materials," FSAI — https://www.fsai.ie/business-advice/running-a-food-business/food-safety-and-hygiene/food-contact-materials/new-recycling-regulation-for-plastic-materials',
        '[41] "What the Green Claims Directive means for companies," KPMG-Law — https://kpmg-law.de/en/what-the-green-claims-directive-means-for-companies-an-overview/',
        '[42] "Directive to empower consumers for the green transition has been published," Bird & Bird — https://www.twobirds.com/en/insights/2024/global/directive-to-empower-consumers-for-the-green-transition-hasn-adopted',
        '[44] "Germany to implement Single-Use Plastics levy from 2024," EY — https://www.ey.com/en_gl/technical/tax-alerts/germany-to-implement-single-use-plastics-levy-from-2024--extendi',
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
        ParagraphStyle('disc', fontName='Helvetica', fontSize=7.5, leading=10,
                       textColor=C_MUTED, alignment=TA_JUSTIFY)
    ))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        '\u00a9 2026 visusta GmbH \u2014 visusta.ch \u2014 All rights reserved.',
        ParagraphStyle('fn', fontName='Helvetica', fontSize=7, leading=10,
                       textColor=C_MUTED, alignment=TA_CENTER)
    ))


# ══════════════════════════════════════════════════════════════════
# Build Document
# ══════════════════════════════════════════════════════════════════
def build_pdf():
    S = build_styles()

    cover_frame = Frame(0, 0, PAGE_W, PAGE_H, leftPadding=25*mm, rightPadding=25*mm,
                        topPadding=10*mm, bottomPadding=10*mm, id='cf')
    content_frame = Frame(25*mm, 22*mm, PAGE_W - 50*mm, PAGE_H - 45*mm, id='ctf')

    doc = BaseDocTemplate(
        OUT_FILE, pagesize=A4,
        pageTemplates=[
            PageTemplate(id='cover', frames=[cover_frame], onPage=on_cover),
            PageTemplate(id='content', frames=[content_frame], onPage=on_page),
        ],
        title='Visusta Quarterly Strategic Brief \u2014 Q1 2026',
        author='visusta GmbH',
        subject='EU & German Sustainability Regulatory Strategy',
        creator='VARI \u2014 Visusta Autonomous Regulatory Intelligence'
    )

    story = []
    build_cover(story, S)
    story.append(NextPageTemplate('content'))
    build_content(story, S)
    doc.build(story)

    print(f'\u2713 Quarterly Brief saved: {OUT_FILE}')
    print(f'  Size: {os.path.getsize(OUT_FILE) / 1024:.0f} KB')


if __name__ == '__main__':
    build_pdf()
