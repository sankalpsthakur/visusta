from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import build_monthly_report
import build_quarterly_brief
import pipeline


REPO_ROOT = Path(__file__).resolve().parents[1]
CLIENT_SOURCE = REPO_ROOT / "regulatory_data" / "gerold-foods"
CLIENT_ID = "acme-labs"


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
    text_path = result.with_suffix(".txt")
    subprocess.run(["pdftotext", str(result), str(text_path)], check=True)
    text = text_path.read_text(encoding="utf-8")
    assert "Regulatory Screening Report for 2026-02" in text
    assert "Law passed" in text


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
    text_path = result.with_suffix(".txt")
    subprocess.run(["pdftotext", str(result), str(text_path)], check=True)
    text = text_path.read_text(encoding="utf-8")
    assert "Amendment in progress" in text
    assert "Law passed" in text
