from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import build_monthly_report
import build_quarterly_brief
import pipeline
from pypdf import PdfReader


REPO_ROOT = Path(__file__).resolve().parents[1]
CLIENT_SOURCE = REPO_ROOT / "regulatory_data" / "gerold-foods"
CLIENT_ID = "gerold-foods"


def _prepare_client_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    regulatory_data = workspace / "regulatory_data"
    regulatory_data.mkdir(parents=True)
    shutil.copytree(CLIENT_SOURCE, regulatory_data / CLIENT_ID)
    return workspace


def _assert_pdf(path: Path) -> None:
    assert path.suffix == ".pdf"
    assert path.exists()
    pdfinfo = subprocess.run(
        ["pdfinfo", str(path)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert re.search(r"^Pages:\s+\d+$", pdfinfo, re.MULTILINE) is not None


def _pdf_text(path: Path) -> str:
    text_path = path.with_suffix(".txt")
    subprocess.run(["pdftotext", str(path), str(text_path)], check=True)
    return text_path.read_text(encoding="utf-8")


def _assert_client_branding(path: Path, expected_title: str, expected_display_name: str) -> None:
    metadata = PdfReader(str(path)).metadata
    assert metadata.title == expected_title
    assert metadata.author == expected_display_name

    text = _pdf_text(path)
    assert expected_display_name in text
    assert "VISUSTA" not in text
    assert "visusta GmbH" not in text


def test_generate_monthly_pdf_uses_client_changelog(tmp_path: Path, monkeypatch) -> None:
    workspace = _prepare_client_workspace(tmp_path)

    monkeypatch.setattr(pipeline, "OUTPUT_DIR", workspace / "output")
    monkeypatch.setattr(pipeline, "REGULATORY_DATA_DIR", workspace / "regulatory_data")
    monkeypatch.setattr(build_monthly_report, "OUTPUT_DIR", workspace)

    result = Path(
        pipeline.generate_monthly_pdf(
            client_id=CLIENT_ID,
            period="2026-02",
        )
    )

    _assert_pdf(result)
    assert not result.with_suffix(".json").exists()
    _assert_client_branding(
        result,
        "Gerold & Team Monthly Regulatory Impact Report — February 2026",
        "Gerold & Team",
    )


def test_generate_quarterly_pdf_uses_client_changelog(tmp_path: Path, monkeypatch) -> None:
    workspace = _prepare_client_workspace(tmp_path)

    monkeypatch.setattr(pipeline, "OUTPUT_DIR", workspace / "output")
    monkeypatch.setattr(pipeline, "REGULATORY_DATA_DIR", workspace / "regulatory_data")
    monkeypatch.setattr(build_quarterly_brief, "OUTPUT_DIR", workspace)

    result = Path(
        pipeline.generate_quarterly_pdf(
            client_id=CLIENT_ID,
            quarter="Q1",
            year=2026,
        )
    )

    _assert_pdf(result)
    assert not result.with_suffix(".json").exists()
    _assert_client_branding(
        result,
        "Gerold & Team Quarterly Strategic Brief — Q1 2026",
        "Gerold & Team",
    )
