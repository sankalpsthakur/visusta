from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "build_capabilities_brief.py"


def test_build_capabilities_brief_pdf(tmp_path: Path) -> None:
    output_pdf = tmp_path / "capabilities_brief.pdf"
    output_txt = tmp_path / "capabilities_brief.txt"

    subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--output", str(output_pdf)],
        check=True,
        cwd=REPO_ROOT,
    )

    assert output_pdf.exists()

    pdfinfo = subprocess.run(
        ["pdfinfo", str(output_pdf)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    pages_match = re.search(r"^Pages:\s+(\d+)$", pdfinfo, re.MULTILINE)
    assert pages_match is not None
    assert int(pages_match.group(1)) >= 9

    subprocess.run(["pdftotext", str(output_pdf), str(output_txt)], check=True)
    text = output_txt.read_text(encoding="utf-8")

    assert "Visusta Functionality and Output Guide" in text
    assert "Implemented today" in text
    assert "Planned or optional extensions" in text
    assert "Quality checks and hallucination control" in text
    assert "Source handling and referencing" in text
    assert "Limitations and current caveats" in text
    assert "How monthly and quarterly outputs differ" in text
