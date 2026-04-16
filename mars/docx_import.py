"""
DOCX import — full round-trip parser for DraftSection data.

Handles: Heading 1 (sections), Heading 2 (sub-headings / Key Facts / References),
List Bullet / List Number (bullet_list blocks), Table Grid (table blocks),
and normal paragraphs.

Iterates doc.element.body children in document order so paragraphs and tables
are correctly interleaved.
"""

from __future__ import annotations

import io
import re
from typing import Any, List, Tuple

from api.schemas_mars import DraftSection, SectionBlock


def parse_docx_to_sections(
    content: bytes,
    locale: str = "en",
) -> Tuple[List[DraftSection], List[str]]:
    """
    Parse raw DOCX bytes into a list of DraftSection objects.

    Returns (sections, warnings).

    Handles:
      - Heading 1  → new DraftSection
      - Heading 2  → 'heading' block (or special Key Facts / References accumulation)
      - List Bullet / List Number → consecutive items merged into a single
        'bullet_list' block whose content is a list[str]
      - Tables     → 'table' block whose content is list[list[str]]
      - Normal paragraphs → 'paragraph' block
    """
    try:
        from docx import Document
        from docx.oxml.ns import qn
        from docx.table import Table as DocxTable
        from docx.text.paragraph import Paragraph as DocxParagraph

        doc = Document(io.BytesIO(content))
    except Exception as exc:
        return [], [f"Failed to parse DOCX: {exc}"]

    sections: List[DraftSection] = []
    warnings: List[str] = []

    current_section: DraftSection | None = None
    section_counter = 0

    # Tracks whether we're in a special Heading 2 accumulation mode.
    # Values: None | 'facts' | 'citations'
    special_mode: str | None = None

    # Pending bullet_list accumulator: list of strings for the current run of
    # list-style paragraphs.  Flushed when a non-list element is encountered.
    pending_bullets: List[str] = []

    def _next_block_id() -> str:
        if current_section is None:
            return "b1"
        return f"b{len(current_section.blocks) + 1}"

    def _flush_bullets() -> None:
        """Flush any accumulated bullet items into a bullet_list block."""
        nonlocal pending_bullets
        if not pending_bullets or current_section is None:
            pending_bullets = []
            return
        block = SectionBlock(
            block_id=_next_block_id(),
            block_type="bullet_list",
            content=list(pending_bullets),
        )
        current_section.blocks.append(block)
        pending_bullets = []

    def _ensure_section(heading: str = "Preamble", sid: str = "imported_preamble") -> DraftSection:
        """Return current section, creating a preamble if none exists yet."""
        nonlocal current_section
        if current_section is None:
            current_section = DraftSection(
                section_id=sid,
                heading=heading,
                locale=locale,
            )
            sections.append(current_section)
        return current_section

    # Walk body children in document order (paragraphs AND tables interleaved).
    from docx.oxml.ns import qn as _qn

    for child in doc.element.body:
        tag = child.tag

        if tag == _qn("w:p"):
            # Construct a Paragraph object from the XML element
            from docx.text.paragraph import Paragraph as _Para
            para = _Para(child, doc)
            style_name = para.style.name if para.style else ""
            text = para.text.strip()

            if style_name.startswith("Heading 1"):
                # Flush any pending bullets before starting a new section
                _flush_bullets()
                special_mode = None
                section_counter += 1
                current_section = DraftSection(
                    section_id=f"imported_s{section_counter}",
                    heading=text or f"Section {section_counter}",
                    locale=locale,
                )
                sections.append(current_section)

            elif style_name.startswith("Heading 2"):
                _flush_bullets()
                _ensure_section()
                if text == "Key Facts":
                    special_mode = "facts"
                elif text == "References":
                    special_mode = "citations"
                else:
                    special_mode = None
                    block = SectionBlock(
                        block_id=_next_block_id(),
                        block_type="heading",
                        content=text,
                    )
                    current_section.blocks.append(block)  # type: ignore[union-attr]

            elif style_name.startswith("List Bullet") or style_name.startswith("List Number"):
                if not text:
                    continue
                _ensure_section()
                if special_mode == "facts":
                    current_section.facts.append(text)  # type: ignore[union-attr]
                elif special_mode == "citations":
                    # Strip legacy [N] prefix if present from older exports
                    cleaned = re.sub(r"^\[\d+\]\s*", "", text)
                    current_section.citations.append(cleaned)  # type: ignore[union-attr]
                else:
                    pending_bullets.append(text)

            else:
                # Normal paragraph (or unknown style)
                _flush_bullets()
                if not text:
                    continue
                _ensure_section()
                special_mode = None
                block = SectionBlock(
                    block_id=_next_block_id(),
                    block_type="paragraph",
                    content=text,
                )
                current_section.blocks.append(block)  # type: ignore[union-attr]

        elif tag == _qn("w:tbl"):
            # Construct a Table object from the XML element
            _flush_bullets()
            special_mode = None
            _ensure_section()
            from docx.table import Table as _Table
            tbl = _Table(child, doc)
            rows: List[List[str]] = []
            for row in tbl.rows:
                rows.append([cell.text.strip() for cell in row.cells])
            if rows:
                block = SectionBlock(
                    block_id=_next_block_id(),
                    block_type="table",
                    content=rows,
                )
                current_section.blocks.append(block)  # type: ignore[union-attr]

        # Other body children (sectPr, etc.) are silently skipped.

    # Flush any trailing bullet list
    _flush_bullets()

    if not sections:
        warnings.append("No sections detected; document may lack Heading 1 styles.")

    return sections, warnings
