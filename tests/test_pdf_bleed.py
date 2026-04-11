"""
Cross-client PDF content bleed regression tests.

Ensures that when a PDF is generated for a specific client, it contains
only that client's facilities, jurisdictions, and regulatory content —
never content from other clients.
"""
import os
import pytest
from pathlib import Path
from pypdf import PdfReader

from pipeline import generate_monthly_pdf, generate_quarterly_pdf

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Per-client forbidden name list: if any appear in this client's PDF, it's a bleed.
# Note: we only forbid FACILITY NAMES from other clients. Regulations like VerpackDG
# or CSRD can legitimately appear in any client whose allowed_countries covers them
# (e.g. alpine-dairy exports cheese to Germany so DE rules apply).
FORBIDDEN = {
    "gerold-foods": [],  # baseline
    "alpine-dairy": ["Hamburg Bakery", "Rietberg Cold Cuts", "Oslo Seafood", "Bergen Fish Oils", "Parma Pasta", "Modena Olive", "Lisbon Juices", "Porto Organic", "Munich Bread", "Vienna Pastries"],
    "nordic-harvest": ["Hamburg Bakery", "Rietberg Cold Cuts", "Zurich Cheese", "Bern Yogurt", "Parma Pasta", "Modena Olive", "Lisbon Juices", "Porto Organic", "Munich Bread", "Vienna Pastries"],
    "trivento-foods": ["Hamburg Bakery", "Rietberg Cold Cuts", "Zurich Cheese", "Bern Yogurt", "Oslo Seafood", "Bergen Fish Oils", "Lisbon Juices", "Porto Organic", "Munich Bread", "Vienna Pastries"],
    "terra-verde": ["Hamburg Bakery", "Rietberg Cold Cuts", "Zurich Cheese", "Bern Yogurt", "Oslo Seafood", "Bergen Fish Oils", "Parma Pasta", "Modena Olive", "Munich Bread", "Vienna Pastries"],
    "brosel-backwaren": ["Hamburg Bakery", "Rietberg Cold Cuts", "Zurich Cheese", "Bern Yogurt", "Oslo Seafood", "Bergen Fish Oils", "Parma Pasta", "Modena Olive", "Lisbon Juices", "Porto Organic"],
}

# Per-client REQUIRED names: must appear in the PDF
REQUIRED = {
    "gerold-foods": ["Hamburg Bakery", "Rietberg Cold Cuts"],
    "alpine-dairy": ["Zurich", "Bern"],
    "nordic-harvest": ["Oslo", "Bergen"],
    "trivento-foods": ["Parma", "Modena"],
    "terra-verde": ["Lisbon", "Porto"],
    "brosel-backwaren": ["Munich", "Vienna"],
}

# Per-client country name/phrase that must appear on the cover
CLIENT_JURISDICTION = {
    "gerold-foods": "German",
    "alpine-dairy": "Swiss",
    "nordic-harvest": "Norwegian",
    "trivento-foods": "Italian",
    "terra-verde": "Portuguese",
    "brosel-backwaren": "German",
}

# Hardcoded fallback phrases that indicate the old bleed-prone implementation
FORBIDDEN_PHRASES = [
    "This Monthly Impact Report covers the regulatory developments directly affecting",
    "Hamburg and Rietberg facilities during February 2026",
    "3.3% increase in Hamburg industrial wastewater",
    "\u20ac5 per tonne on transport and industrial packaging",
]


def _pdf_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


@pytest.mark.parametrize("client_id", [c for c, f in FORBIDDEN.items() if f])
def test_no_cross_client_bleed(client_id, tmp_path):
    """Each client's PDF must not contain facility/regulation names from other clients."""
    out_path = str(tmp_path / f"{client_id}_Monthly_Impact_Report_2026-02.pdf")
    pdf_path = generate_monthly_pdf(client_id, "2026-02", output_path=out_path)
    assert os.path.exists(pdf_path), f"PDF not generated for {client_id}"
    text = _pdf_text(pdf_path)

    forbidden = FORBIDDEN[client_id]
    found = [name for name in forbidden if name in text]
    assert not found, (
        f"CROSS-CLIENT BLEED: {client_id} PDF contains names from other clients: {found}"
    )


@pytest.mark.parametrize("client_id", list(REQUIRED.keys()))
def test_client_facilities_present(client_id, tmp_path):
    """Each client's PDF must show their own facility names."""
    out_path = str(tmp_path / f"{client_id}_Monthly_Impact_Report_2026-02.pdf")
    pdf_path = generate_monthly_pdf(client_id, "2026-02", output_path=out_path)
    text = _pdf_text(pdf_path)

    required = REQUIRED[client_id]
    missing = [name for name in required if name not in text]
    assert not missing, (
        f"MISSING CLIENT DATA: {client_id} PDF does not contain expected facilities: {missing}"
    )


@pytest.mark.parametrize("client_id", list(REQUIRED.keys()))
def test_pdf_contains_no_february_fallback(client_id, tmp_path):
    """No PDF should contain the old hardcoded February 2026 fallback text."""
    out_path = str(tmp_path / f"{client_id}_Monthly_Impact_Report_2026-02.pdf")
    pdf_path = generate_monthly_pdf(client_id, "2026-02", output_path=out_path)
    text = _pdf_text(pdf_path)

    found = [phrase for phrase in FORBIDDEN_PHRASES if phrase in text]
    assert not found, (
        f"HARDCODED FALLBACK DETECTED in {client_id} PDF: {found}"
    )


@pytest.mark.parametrize("client_id", list(CLIENT_JURISDICTION.keys()))
def test_pdf_has_client_jurisdiction(client_id, tmp_path):
    """Each client's PDF must contain their country code on the cover."""
    out_path = str(tmp_path / f"{client_id}_Monthly_Impact_Report_2026-02.pdf")
    pdf_path = generate_monthly_pdf(client_id, "2026-02", output_path=out_path)
    text = _pdf_text(pdf_path)

    jurisdiction = CLIENT_JURISDICTION[client_id]
    assert jurisdiction in text, (
        f"MISSING JURISDICTION: {client_id} PDF does not contain country code '{jurisdiction}'"
    )


# ── Quarterly tests ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("client_id", [c for c, f in FORBIDDEN.items() if f])
def test_no_cross_client_bleed_quarterly(client_id, tmp_path):
    """Each client's quarterly PDF must not contain facility names from other clients."""
    out_path = str(tmp_path / f"{client_id}_Quarterly_Q1_2026.pdf")
    pdf_path = generate_quarterly_pdf(client_id, "Q1", 2026, output_path=out_path)
    assert os.path.exists(pdf_path), f"Quarterly PDF not generated for {client_id}"
    text = _pdf_text(pdf_path)
    forbidden = FORBIDDEN[client_id]
    found = [name for name in forbidden if name in text]
    assert not found, f"QUARTERLY BLEED: {client_id} contains {found}"


@pytest.mark.parametrize("client_id", list(REQUIRED.keys()))
def test_client_facilities_present_quarterly(client_id, tmp_path):
    """Each client's quarterly PDF must show their own facility names."""
    out_path = str(tmp_path / f"{client_id}_Quarterly_Q1_2026.pdf")
    pdf_path = generate_quarterly_pdf(client_id, "Q1", 2026, output_path=out_path)
    text = _pdf_text(pdf_path)
    required = REQUIRED[client_id]
    missing = [name for name in required if name not in text]
    assert not missing, f"MISSING CLIENT DATA in quarterly PDF: {client_id} missing {missing}"


@pytest.mark.parametrize("client_id", list(REQUIRED.keys()))
def test_no_fallback_quarterly(client_id, tmp_path):
    """Quarterly PDFs must not contain old hardcoded fallback text."""
    out_path = str(tmp_path / f"{client_id}_Quarterly_Q1_2026.pdf")
    pdf_path = generate_quarterly_pdf(client_id, "Q1", 2026, output_path=out_path)
    text = _pdf_text(pdf_path)
    found = [phrase for phrase in FORBIDDEN_PHRASES if phrase in text]
    assert not found, f"HARDCODED FALLBACK in quarterly PDF for {client_id}: {found}"


# ── Evidence References tests ─────────────────────────────────────────────────

@pytest.mark.parametrize("client_id", list(REQUIRED.keys()))
def test_pdf_has_references_section(client_id, tmp_path):
    """Each client's PDF must have a References section with evidence citations."""
    import re
    out_path = str(tmp_path / f"{client_id}_Monthly_Impact_Report_2026-02.pdf")
    pdf_path = generate_monthly_pdf(client_id, "2026-02", output_path=out_path)
    text = _pdf_text(pdf_path)

    assert "References" in text, f"No References section in {client_id} PDF"
    assert re.search(r"Accessed \d{4}-\d{2}-\d{2}", text), (
        f"No accessed dates in {client_id} References"
    )
