from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "build_capabilities_one_pager.py"


def test_build_capabilities_one_pager_pdf(tmp_path: Path) -> None:
    output_pdf = tmp_path / "capabilities_one_pager.pdf"
    output_txt = tmp_path / "capabilities_one_pager.txt"

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
    assert int(pages_match.group(1)) == 1

    subprocess.run(["pdftotext", str(output_pdf), str(output_txt)], check=True)
    text = output_txt.read_text(encoding="utf-8")

    assert "Visusta Agent-Orchestrated Intelligence Dashboard" in text
    assert "Dashboard and agent orchestration" in text
    assert "Quality and trust layer" in text
    assert "Source intake and referencing" in text
    assert "What Visusta can expect" in text
    assert "Repo-grounded summary" not in text
    assert "What the client can expect" not in text
