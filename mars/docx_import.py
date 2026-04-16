"""
DOCX import stub.

Full parsing logic in Phase 4. This module provides the interface
used by the exports router's import-docx endpoint.
"""

from __future__ import annotations

from typing import List, Tuple

from api.schemas_mars import DraftSection, SectionBlock


def parse_docx_to_sections(
    content: bytes,
    locale: str = "en",
) -> Tuple[List[DraftSection], List[str]]:
    """
    Parse raw DOCX bytes into a list of DraftSection objects.

    Returns (sections, warnings).

    Stub: splits the document on Heading 1 styles. Each heading becomes
    a section; paragraph text under it becomes a single paragraph block.
    """
    try:
        import io
        from docx import Document

        doc = Document(io.BytesIO(content))
    except Exception as exc:
        return [], [f"Failed to parse DOCX: {exc}"]

    sections: List[DraftSection] = []
    warnings: List[str] = []

    current_section: DraftSection | None = None
    section_counter = 0

    for para in doc.paragraphs:
        style_name = para.style.name if para.style else ""
        text = para.text.strip()

        if style_name.startswith("Heading 1"):
            section_counter += 1
            current_section = DraftSection(
                section_id=f"imported_s{section_counter}",
                heading=text or f"Section {section_counter}",
                locale=locale,
            )
            sections.append(current_section)
        elif text and current_section is not None:
            block = SectionBlock(
                block_id=f"b{len(current_section.blocks) + 1}",
                block_type="paragraph",
                content=text,
            )
            current_section.blocks.append(block)
        elif text and current_section is None:
            # Content before first heading — create a preamble section
            current_section = DraftSection(
                section_id="imported_preamble",
                heading="Preamble",
                locale=locale,
            )
            sections.append(current_section)
            block = SectionBlock(
                block_id="b1",
                block_type="paragraph",
                content=text,
            )
            current_section.blocks.append(block)

    if not sections:
        warnings.append("No sections detected; document may lack Heading 1 styles.")

    return sections, warnings
