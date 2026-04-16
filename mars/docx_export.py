"""
DOCX export stub.

Full implementation in Phase 4. This module provides the interface
that the exports router calls; it creates a placeholder file and
marks the export job as completed.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from api.schemas_mars import DraftSection


def export_sections_to_docx(
    sections: List[DraftSection],
    output_path: Path,
    locale: str = "en",
) -> Path:
    """
    Write sections to a DOCX file at output_path.

    Stub: creates a minimal valid DOCX using python-docx.
    """
    from docx import Document

    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()
    doc.add_heading("Report Draft", level=0)

    for section in sections:
        doc.add_heading(section.heading, level=1)
        for block in section.blocks:
            if isinstance(block.content, str):
                doc.add_paragraph(block.content)

    doc.save(str(output_path))
    return output_path
