"""
PDF export stub.

Full implementation in Phase 4. This module provides the interface
that the exports router calls for PDF export jobs.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from api.schemas_mars import DraftSection


def export_sections_to_pdf(
    sections: List[DraftSection],
    output_path: Path,
    locale: str = "en",
    client_branding: dict | None = None,
) -> Path:
    """
    Render sections to a PDF file at output_path.

    Stub: creates a minimal PDF using ReportLab.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    output_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4
    y = height - 60

    c.setFont("Helvetica-Bold", 16)
    c.drawString(60, y, "Report Draft")
    y -= 40

    for section in sections:
        if y < 100:
            c.showPage()
            y = height - 60

        c.setFont("Helvetica-Bold", 13)
        c.drawString(60, y, section.heading)
        y -= 24

        c.setFont("Helvetica", 11)
        for block in section.blocks:
            if isinstance(block.content, str):
                # Naive line wrapping
                words = block.content.split()
                line = ""
                for word in words:
                    if len(line) + len(word) + 1 > 80:
                        c.drawString(60, y, line)
                        y -= 18
                        line = word
                        if y < 80:
                            c.showPage()
                            y = height - 60
                    else:
                        line = (line + " " + word).strip()
                if line:
                    c.drawString(60, y, line)
                    y -= 18
        y -= 12

    c.save()
    return output_path
