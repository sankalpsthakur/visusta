#!/usr/bin/env python3
"""
VISUSTA — Quarterly PDF Integration Module

This module demonstrates how to integrate the quarterly consolidation workflow
with the existing ReportLab-based PDF generation pipeline.

Usage:
    1. Run consolidation to generate structured data
    2. Transform data to PDF-compatible format
    3. Call modified build functions with consolidated content
"""

import os
from datetime import date
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

# Import from existing PDF build scripts
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, 
    Table, TableStyle, PageBreak, Image, NextPageTemplate, HRFlowable
)

# Import from consolidation module
from quarterly_consolidator import (
    QuarterlySummary,
    ConsolidatedRegulation,
    ImpactLevel,
    RegulationScope,
    QuarterlyOutputFormatter,
    run_quarterly_consolidation,
    load_entries_from_json
)


# ═════════════════════════════════════════════════════════════════════════════
# BRAND CONSTANTS (mirrored from build_quarterly_brief.py)
# ═════════════════════════════════════════════════════════════════════════════

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


# ═════════════════════════════════════════════════════════════════════════════
# CONTENT TRANSFORMERS
# ═════════════════════════════════════════════════════════════════════════════

class ConsolidatedContentAdapter:
    """
    Adts consolidated quarterly data to ReportLab-compatible structures.
    
    This class bridges the gap between the data models in quarterly_consolidator.py
    and the visual components in build_quarterly_brief.py.
    """
    
    def __init__(self, summary: QuarterlySummary, styles: Dict[str, ParagraphStyle]):
        self.summary = summary
        self.styles = styles
        self.chart_dir = os.path.join(os.path.dirname(__file__), 'charts')
    
    # ─────────────────────────────────────────────────────────────────────────
    # Executive Summary Section
    # ─────────────────────────────────────────────────────────────────────────
    
    def build_executive_summary(self) -> List[Any]:
        """
        Build executive summary section from consolidated data.
        
        Transforms the high-level summary into ReportLab flowables.
        """
        story = []
        body = self.styles['body']
        
        story.append(Paragraph('Executive Summary', self.styles['h1']))
        
        # Primary summary paragraph
        stats = self.summary.stats
        critical_count = stats.get('by_impact', {}).get('CRITICAL', 0)
        high_count = stats.get('by_impact', {}).get('HIGH', 0)
        total_regs = len(self.summary.regulations)
        
        summary_text = (
            f"This Quarterly Strategic Brief consolidates {total_regs} key regulatory "
            f"developments from {self.summary.reporting_period}. The quarter shows "
            f"{critical_count} critical and {high_count} high-priority regulatory drivers "
            f"requiring strategic attention across our Hamburg and Rietberg facilities."
        )
        story.append(Paragraph(summary_text, body))
        
        # Theme-based summary
        if self.summary.themes:
            theme_summary = "Key strategic patterns identified: "
            theme_descriptions = []
            for theme in self.summary.themes[:3]:  # Top 3 themes
                theme_descriptions.append(theme['theme'].lower())
            theme_summary += ", ".join(theme_descriptions) + "."
            story.append(Paragraph(theme_summary, body))
        
        # Confidence note
        improving_count = sum(1 for r in self.summary.regulations if r.confidence_trend == "improving")
        if improving_count > 0:
            story.append(Paragraph(
                f"<i>Note: {improving_count} regulation(s) show improving confidence scores, "
                f"indicating clearer guidance emerging over the quarter.</i>",
                body
            ))
        
        story.append(Spacer(1, 4*mm))
        return story
    
    # ─────────────────────────────────────────────────────────────────────────
    # Priority Matrix
    # ─────────────────────────────────────────────────────────────────────────
    
    def build_priority_matrix(self) -> List[Any]:
        """
        Build strategic priority matrix from consolidated regulations.
        
        Transforms regulation data into the table format used in the PDF.
        """
        story = []
        
        story.append(Paragraph('Strategic Priority Matrix', self.styles['h2']))
        
        # Sort regulations by priority (CRITICAL first, then HIGH, etc.)
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        sorted_regs = sorted(
            self.summary.regulations,
            key=lambda r: priority_order.get(r.impact_level.value, 99)
        )
        
        # Build table headers (matching existing PDF structure)
        headers = ['Regulation', 'Priority', 'Deadline', 'Primary Impact Area', 'Investment Type']
        rows = []
        
        for reg in sorted_regs:
            # Determine primary impact area
            impact_area = self._derive_impact_area(reg)
            
            # Determine investment type
            investment = self._derive_investment_type(reg)
            
            # Format deadline
            deadline = self._format_deadline(reg.primary_deadline)
            
            rows.append([
                reg.regulation_code,
                reg.impact_level.value,
                deadline,
                impact_area,
                investment
            ])
        
        # Create table using existing pro_table pattern
        from build_quarterly_brief import pro_table
        story.append(pro_table(headers, rows, [80, 55, 65, 105, 80], self.styles))
        story.append(Paragraph(
            f'Table 1: Strategic priority matrix for {self.summary.reporting_period}.',
            self.styles['caption']
        ))
        story.append(Spacer(1, 8*mm))
        
        return story
    
    # ─────────────────────────────────────────────────────────────────────────
    # Regulation Sections
    # ─────────────────────────────────────────────────────────────────────────
    
    def build_regulation_sections(self) -> List[Any]:
        """
        Build detailed sections for each consolidated regulation.
        
        Each regulation gets its own section with narrative content
        derived from the consolidation process.
        """
        story = []
        
        # Sort by impact level (most important first)
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        sorted_regs = sorted(
            self.summary.regulations,
            key=lambda r: priority_order.get(r.impact_level.value, 99)
        )
        
        for idx, reg in enumerate(sorted_regs, 1):
            story.extend(self._build_single_regulation_section(reg, idx))
            story.append(Spacer(1, 8*mm))
        
        return story
    
    def _build_single_regulation_section(
        self,
        reg: ConsolidatedRegulation,
        section_num: int
    ) -> List[Any]:
        """Build a single regulation section."""
        story = []
        body = self.styles['body']
        
        # Section header
        story.append(Paragraph(
            f"{section_num}. {reg.regulation_name} ({reg.regulation_code})",
            self.styles['h1']
        ))
        
        # Status badge
        status_text = self._derive_status_text(reg)
        badge_color = self._derive_badge_color(reg.impact_level)
        from build_quarterly_brief import status_badge
        story.append(status_badge(status_text, badge_color, self.styles))
        story.append(Spacer(1, 4*mm))
        
        # Executive summary (from consolidation narrative)
        if reg.executive_summary:
            story.append(Paragraph(reg.executive_summary, body))
        
        # Strategic implications
        if reg.strategic_implications:
            story.append(Paragraph(
                f"<b>Strategic Implications:</b> {reg.strategic_implications}",
                body
            ))
        
        # Key developments table
        if reg.key_developments:
            story.append(Paragraph('Quarterly Developments', self.styles['h2']))
            dev_data = [["Month", "Development"]]
            for dev in reg.key_developments:
                # Parse "Month: Description" format
                if ": " in dev:
                    month, desc = dev.split(": ", 1)
                    dev_data.append([month, desc])
                else:
                    dev_data.append(["", dev])
            
            from build_quarterly_brief import pro_table
            story.append(pro_table(
                dev_data[0], 
                dev_data[1:], 
                [60, 400], 
                self.styles
            ))
            story.append(Spacer(1, 4*mm))
        
        # Recommended actions
        if reg.recommended_actions:
            story.append(Paragraph('Recommended Actions', self.styles['h2']))
            for action in reg.recommended_actions[:5]:  # Top 5 actions
                action_text = (
                    f"<b>[{action['priority']}]</b> {action['action']} "
                    f"<i>(from {action['source_month']})</i>"
                )
                story.append(Paragraph(f"• {action_text}", body))
            story.append(Spacer(1, 3*mm))
        
        # Investment requirements
        if reg.investment_requirements:
            story.append(Paragraph('Investment Requirements', self.styles['h2']))
            inv_headers = ['Type', 'Area', 'Priority']
            inv_rows = [
                [inv['type'], inv['area'], inv['priority']]
                for inv in reg.investment_requirements
            ]
            from build_quarterly_brief import pro_table
            story.append(pro_table(inv_headers, inv_rows, [120, 200, 80], self.styles))
            story.append(Spacer(1, 4*mm))
        
        # Source coverage note
        if len(reg.month_coverage) > 1:
            story.append(Paragraph(
                f"<i>This analysis consolidates observations from "
                f"{', '.join(sorted(reg.month_coverage))}.</i>",
                self.styles['body_small']
            ))
        
        return story
    
    # ─────────────────────────────────────────────────────────────────────────
    # Strategic Themes Section
    # ─────────────────────────────────────────────────────────────────────────
    
    def build_strategic_themes_section(self) -> List[Any]:
        """Build cross-cutting strategic themes section."""
        story = []
        
        if not self.summary.themes:
            return story
        
        story.append(PageBreak())
        story.append(Paragraph('Cross-Cutting Strategic Themes', self.styles['h1']))
        
        for theme in self.summary.themes:
            from build_quarterly_brief import callout_box
            
            # Build theme content
            content = theme['description']
            if theme.get('regulations'):
                content += f" <b>Affected:</b> {', '.join(theme['regulations'])}."
            
            story.append(callout_box(
                theme['theme'],
                content + f" <b>Implication:</b> {theme['strategic_implication']}",
                self.styles,
                accent_color=C_PRIMARY
            ))
            story.append(Spacer(1, 4*mm))
        
        return story
    
    # ─────────────────────────────────────────────────────────────────────────
    # Risk Assessment Section
    # ─────────────────────────────────────────────────────────────────────────
    
    def build_risk_assessment_section(self) -> List[Any]:
        """Build risk assessment section from consolidated data."""
        story = []
        
        if not self.summary.risk_assessment:
            return story
        
        story.append(Paragraph('Risk Assessment', self.styles['h1']))
        
        risk_data = self.summary.risk_assessment
        body = self.styles['body']
        
        # High-risk regulations
        high_risk = risk_data.get('high_risk_regulations', [])
        if high_risk:
            story.append(Paragraph('High-Priority Risk Items', self.styles['h2']))
            for item in high_risk:
                story.append(Paragraph(
                    f"• <b>{item['code']}:</b> {item['risk']}",
                    body
                ))
            story.append(Spacer(1, 4*mm))
        
        # Monitoring required
        monitoring = risk_data.get('monitoring_required', [])
        if monitoring:
            from build_quarterly_brief import callout_box
            story.append(callout_box(
                'Monitoring Required',
                f"The following regulations show declining confidence and require "
                f"continued monitoring: {', '.join(monitoring)}.",
                self.styles,
                accent_color=C_ALERT_AMBER
            ))
        
        return story
    
    # ─────────────────────────────────────────────────────────────────────────
    # Resource Implications Section
    # ─────────────────────────────────────────────────────────────────────────
    
    def build_resource_section(self) -> List[Any]:
        """Build resource implications section."""
        story = []
        
        if not self.summary.resource_implications:
            return story
        
        story.append(Paragraph('Resource Implications', self.styles['h1']))
        
        resources = self.summary.resource_implications
        body = self.styles['body']
        
        # Investment summary
        investment_summary = resources.get('investment_summary', {})
        if investment_summary:
            story.append(Paragraph('Investment Requirements by Type', self.styles['h2']))
            for inv_type, count in investment_summary.items():
                story.append(Paragraph(f"• <b>{inv_type}:</b> {count} regulation(s)", body))
            story.append(Spacer(1, 4*mm))
        
        # Affected departments
        departments = resources.get('affected_departments', [])
        if departments:
            story.append(Paragraph('Affected Functions', self.styles['h2']))
            story.append(Paragraph(
                f"The following functions will require capacity allocation: "
                f"{', '.join(departments)}.",
                body
            ))
            story.append(Spacer(1, 4*mm))
        
        # Effort estimate
        effort = resources.get('estimated_effort', 'Moderate')
        story.append(Paragraph(
            f"<b>Overall Effort Level:</b> {effort}. "
            f"This assessment is based on the number and complexity of "
            f"simultaneous regulatory requirements.",
            body
        ))
        
        return story
    
    # ─────────────────────────────────────────────────────────────────────────
    # Utility Methods
    # ─────────────────────────────────────────────────────────────────────────
    
    def _derive_impact_area(self, reg: ConsolidatedRegulation) -> str:
        """Derive primary impact area from regulation data."""
        # Extract from regulation code/name
        code_to_area = {
            'PPWR': 'R&D, Packaging',
            'EUDR': 'Sourcing, IT',
            'CSRD': 'Finance, Reporting',
            'VerpackDG': 'Logistics, Procurement',
            'FCM': 'Packaging Supply Chain',
            'EmpCo': 'Marketing, Legal',
        }
        
        for code, area in code_to_area.items():
            if code in reg.regulation_code.upper():
                return area
        
        return 'Operations'
    
    def _derive_investment_type(self, reg: ConsolidatedRegulation) -> str:
        """Derive investment type from regulation requirements."""
        if reg.investment_requirements:
            types = [inv['type'] for inv in reg.investment_requirements]
            return ' + '.join(set(types))
        
        # Infer from impact level
        if reg.impact_level == ImpactLevel.CRITICAL:
            return 'CAPEX + R&D'
        elif reg.impact_level == ImpactLevel.HIGH:
            return 'OPEX + Audit'
        return 'OPEX'
    
    def _format_deadline(self, deadline: Optional[date]) -> str:
        """Format deadline for display."""
        if not deadline:
            return 'TBD'
        
        days_until = (deadline - date.today()).days
        if days_until < 0:
            return f"OVERDUE ({deadline.strftime('%b %Y')})"
        elif days_until < 90:
            return f"URGENT: {deadline.strftime('%b %d, %Y')}"
        else:
            return deadline.strftime('%b %d, %Y')
    
    def _derive_status_text(self, reg: ConsolidatedRegulation) -> str:
        """Derive status badge text from regulation."""
        if reg.primary_deadline:
            return f"DEADLINE: {reg.primary_deadline.strftime('%B %d, %Y').upper()}"
        return reg.latest_status.upper()
    
    def _derive_badge_color(self, impact: ImpactLevel) -> HexColor:
        """Derive badge color from impact level."""
        if impact == ImpactLevel.CRITICAL:
            return C_ALERT_RED
        elif impact in (ImpactLevel.HIGH, ImpactLevel.MEDIUM):
            return C_ALERT_AMBER
        return C_ACCENT


# ═════════════════════════════════════════════════════════════════════════════
# PDF BUILD INTEGRATION
# ═════════════════════════════════════════════════════════════════════════════

def build_quarterly_brief_from_consolidation(
    summary: QuarterlySummary,
    output_path: Optional[str] = None
) -> str:
    """
    Build PDF from consolidated quarterly data.
    
    This function integrates the consolidation output with the existing
    ReportLab PDF generation pipeline.
    
    Args:
        summary: QuarterlySummary from consolidation workflow
        output_path: Optional path for output PDF
        
    Returns:
        Path to generated PDF file
    """
    from build_quarterly_brief import (
        build_styles, build_cover, on_cover, on_page,
        C_PRIMARY_DARK, C_PRIMARY, C_PRIMARY_LIGHT, C_ACCENT,
        C_LIGHT_BG, C_WARM_GRAY, C_TEXT, C_MUTED, C_BORDER,
        C_ALERT_RED, C_ALERT_AMBER, C_TABLE_HEAD, C_TABLE_STRIPE, C_DEEP_BLUE,
        PAGE_W, PAGE_H, CHART_DIR
    )
    
    # Setup output path
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(__file__),
            f"Visusta_Quarterly_Strategic_Brief_{summary.quarter.replace(' ', '_')}.pdf"
        )
    
    # Build styles
    styles = build_styles()
    
    # Create content adapter
    adapter = ConsolidatedContentAdapter(summary, styles)
    
    # Build content story
    story = []
    
    # Cover page (use existing but customize)
    story = _build_custom_cover(story, styles, summary)
    story.append(NextPageTemplate('content'))
    
    # Executive Summary
    story.extend(adapter.build_executive_summary())
    
    # Priority Matrix
    story.extend(adapter.build_priority_matrix())
    
    # Regulation Sections (detailed)
    story.extend(adapter.build_regulation_sections())
    
    # Strategic Themes
    story.extend(adapter.build_strategic_themes_section())
    
    # Risk Assessment
    story.extend(adapter.build_risk_assessment_section())
    
    # Resource Implications
    story.extend(adapter.build_resource_section())
    
    # Build PDF
    cover_frame = Frame(0, 0, PAGE_W, PAGE_H, leftPadding=25*mm, rightPadding=25*mm,
                        topPadding=10*mm, bottomPadding=10*mm, id='cf')
    content_frame = Frame(25*mm, 22*mm, PAGE_W - 50*mm, PAGE_H - 45*mm, id='ctf')
    
    doc = BaseDocTemplate(
        output_path, pagesize=A4,
        pageTemplates=[
            PageTemplate(id='cover', frames=[cover_frame], onPage=on_cover),
            PageTemplate(id='content', frames=[content_frame], onPage=on_page),
        ],
        title=f'Visusta Quarterly Strategic Brief — {summary.quarter}',
        author='visusta GmbH',
        subject='EU & German Sustainability Regulatory Strategy',
        creator='VARI — Visusta Autonomous Regulatory Intelligence'
    )
    
    doc.build(story)
    
    print(f'✓ Quarterly Brief generated: {output_path}')
    print(f'  Size: {os.path.getsize(output_path) / 1024:.0f} KB')
    
    return output_path


def _build_custom_cover(
    story: List[Any],
    styles: Dict[str, ParagraphStyle],
    summary: QuarterlySummary
) -> List[Any]:
    """
    Build customized cover page from consolidated data.
    """
    items = []
    items.append(Spacer(1, 45*mm))
    items.append(Paragraph(
        '<font size="12" color="#8FB8A2">visusta</font>  '
        '<font size="9" color="#5F9A7E">\u2014 make visions real.</font>',
        ParagraphStyle('logo', fontName='Helvetica-Bold', fontSize=12, leading=16,
                       textColor=HexColor('#8FB8A2'))
    ))
    items.append(Spacer(1, 25*mm))
    items.append(Paragraph('Quarterly Strategic<br/>Brief', styles['cover_title']))
    items.append(Spacer(1, 4*mm))
    items.append(Paragraph(
        'EU &amp; German Sustainability Frameworks<br/>'
        'Strategic Outlook for Food Manufacturers',
        styles['cover_subtitle']
    ))
    items.append(Spacer(1, 12*mm))
    items.append(HRFlowable(width='60%', thickness=1, color=HexColor('#2E8B63'),
                             spaceBefore=0, spaceAfter=12, hAlign='LEFT'))
    
    # Dynamic meta info from consolidation
    meta_style = styles['cover_meta']
    items.append(Paragraph(f'<b>Reporting Period:</b>  {summary.quarter} ({summary.reporting_period})', meta_style))
    
    # Count regulations by priority for cover
    stats = summary.stats
    critical = stats.get('by_impact', {}).get('CRITICAL', 0)
    high = stats.get('by_impact', {}).get('HIGH', 0)
    items.append(Paragraph(
        f'<b>Regulatory Drivers:</b>  {len(summary.regulations)} tracked '
        f'({critical} critical, {high} high)',
        meta_style
    ))
    
    items.append(Paragraph(f'<b>Date of Issue:</b>  {date.today().strftime("%B %d, %Y")}', meta_style))
    items.append(Paragraph('<b>Prepared for:</b>  Executive Leadership &amp; Board Advisory', meta_style))
    items.append(Paragraph('<b>Facilities:</b>  Hamburg &amp; Rietberg, Germany', meta_style))
    items.append(Spacer(1, 30*mm))
    items.append(Paragraph(
        '<font size="8" color="#5F9A7E">CLASSIFICATION: CONFIDENTIAL \u2014 INTERNAL USE ONLY</font>',
        ParagraphStyle('cls', fontName='Helvetica', fontSize=8, textColor=HexColor('#5F9A7E'))
    ))
    
    # Wrap in background table
    from build_quarterly_brief import C_PRIMARY_DARK, PAGE_W
    inner_rows = [[item] for item in items]
    ct = Table(inner_rows, colWidths=[PAGE_W - 50*mm])
    ct.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_PRIMARY_DARK),
        ('LEFTPADDING', (0,0), (-1,-1), 20*mm),
        ('RIGHTPADDING', (0,0), (-1,-1), 15*mm),
    ]))
    outer = Table([[ct]], colWidths=[PAGE_W - 50*mm])
    outer.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), C_PRIMARY_DARK)]))
    
    story.append(outer)
    story.append(PageBreak())
    
    return story


# ═════════════════════════════════════════════════════════════════════════════
# WORKFLOW ORCHESTRATION
# ═════════════════════════════════════════════════════════════════════════════

def run_full_quarterly_workflow(
    month1_data_path: str,
    month2_data_path: str,
    month3_data_path: str,
    quarter: str,
    year: int,
    output_dir: Optional[str] = None
) -> Dict[str, str]:
    """
    Run complete quarterly workflow from data files to PDF.
    
    This is the main orchestration function that:
    1. Loads monthly change log data from JSON files
    2. Runs consolidation
    3. Generates intermediate outputs
    4. Builds final PDF
    
    Args:
        month1_data_path: Path to first month JSON data
        month2_data_path: Path to second month JSON data
        month3_data_path: Path to third month JSON data
        quarter: Quarter identifier ("Q1", "Q2", etc.)
        year: Year (e.g., 2026)
        output_dir: Optional output directory
        
    Returns:
        Dictionary with paths to all generated files
    """
    # Step 1: Load data
    print(f"Loading monthly data files...")
    month1_entries = load_entries_from_json(month1_data_path)
    month2_entries = load_entries_from_json(month2_data_path)
    month3_entries = load_entries_from_json(month3_data_path)
    
    print(f"  Month 1: {len(month1_entries)} entries")
    print(f"  Month 2: {len(month2_entries)} entries")
    print(f"  Month 3: {len(month3_entries)} entries")
    
    # Step 2: Consolidate
    print(f"\nRunning consolidation for {quarter} {year}...")
    summary = run_quarterly_consolidation(
        month1_entries,
        month2_entries,
        month3_entries,
        quarter,
        year
    )
    
    # Step 3: Save intermediate outputs
    if output_dir:
        print(f"\nSaving intermediate outputs to {output_dir}...")
        from quarterly_consolidator import save_consolidation_output
        intermediate_files = save_consolidation_output(summary, output_dir)
        print(f"  JSON: {intermediate_files.get('json')}")
        print(f"  Markdown: {intermediate_files.get('markdown')}")
    
    # Step 4: Generate PDF
    print(f"\nGenerating PDF...")
    pdf_path = build_quarterly_brief_from_consolidation(summary, 
        output_path=output_dir and os.path.join(output_dir, f"Visusta_Quarterly_{quarter}_{year}.pdf"))
    
    return {
        "pdf": pdf_path,
        "json": intermediate_files.get("json") if output_dir else None,
        "markdown": intermediate_files.get("markdown") if output_dir else None
    }


# ═════════════════════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("VISUSTA Quarterly PDF Integration Module")
    print("=" * 70)
    print("\nThis module provides integration between the quarterly consolidation")
    print("workflow and the existing ReportLab PDF generation pipeline.")
    print("\nKey Functions:")
    print("  - ConsolidatedContentAdapter: Transforms data to PDF format")
    print("  - build_quarterly_brief_from_consolidation: Generate PDF from summary")
    print("  - run_full_quarterly_workflow: End-to-end orchestration")
    print("\nUsage:")
    print("  from quarterly_pdf_integration import run_full_quarterly_workflow")
    print("  files = run_full_quarterly_workflow(")
    print("      'data/jan_2026.json',")
    print("      'data/feb_2026.json',")
    print("      'data/mar_2026.json',")
    print("      quarter='Q1',")
    print("      year=2026,")
    print("      output_dir='output/Q1_2026'")
    print("  )")
    print("=" * 70)
