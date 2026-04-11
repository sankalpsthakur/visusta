from __future__ import annotations

import json
from pathlib import Path

import gap_analysis
import pytest

pytest.importorskip("fastapi")

from api.main import run_audit_endpoint


def _write_builder_script(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "import json",
                'refs = [',
                '    "EUR-Lex https://eur-lex.europa.eu/example",',
                ']',
                "# json.load placeholder keeps the auditor happy",
                "# regulatory_data placeholder keeps the auditor happy",
            ]
        ),
        encoding="utf-8",
    )


def test_run_audit_uses_client_scoped_state_and_writes_client_report(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    regulatory_data = repo_root / "regulatory_data"
    client_id = "alpine-dairy"

    repo_root.mkdir()
    regulatory_data.mkdir()

    _write_builder_script(repo_root / "build_monthly_report.py")
    _write_builder_script(repo_root / "build_quarterly_brief.py")

    root_states = regulatory_data / "states"
    root_states.mkdir(parents=True)
    (root_states / "2026-02.json").write_text(
        json.dumps(
            {
                "topics_covered": ["ghg"],
                "regulations": [
                    {
                        "regulation_id": "ROOT-1",
                        "applicable_countries": ["US"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    client_states = regulatory_data / client_id / "states"
    client_states.mkdir(parents=True)
    (client_states / "2026-02.json").write_text(
        json.dumps(
            {
                "topics_covered": [
                    "ghg",
                    "packaging",
                    "water",
                    "waste",
                    "social_human_rights",
                ],
                "regulations": [
                    {
                        "regulation_id": "CLIENT-1",
                        "applicable_countries": ["EU", "DE"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(gap_analysis, "REPO_ROOT", repo_root)
    monkeypatch.setattr(gap_analysis, "REG_DATA", regulatory_data)

    report = gap_analysis.run_audit(client_id=client_id)

    client_report = regulatory_data / client_id / "audits" / "gap_analysis_report.md"
    root_report = regulatory_data / "audits" / "gap_analysis_report.md"

    assert client_report.exists()
    assert not root_report.exists()
    assert report.findings == []


def test_run_audit_endpoint_passes_client_id_to_audit(monkeypatch):
    captured = {}

    def fake_run_audit(client_id=None):
        captured["client_id"] = client_id
        return gap_analysis.AuditReport()

    monkeypatch.setattr("gap_analysis.run_audit", fake_run_audit)

    response = run_audit_endpoint(client_id="alpine-dairy")

    assert captured["client_id"] == "alpine-dairy"
    assert response.finding_count == 0
    assert response.findings == []
