"""
Shared dependencies, helpers, and constants for all API routers.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException

from api.schemas import (
    ClientResponse,
    FacilitySchema,
    ReportPreferences,
    SourceConfig,
    Thresholds,
)

# ── Project root ───────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Directory constants ────────────────────────────────────────────────────────

REGULATORY_DATA_DIR = PROJECT_ROOT / "regulatory_data"
OUTPUT_DIR = PROJECT_ROOT / "output"
CHARTS_DIR = PROJECT_ROOT / "charts"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHARTS_DIR.mkdir(parents=True, exist_ok=True)


# ── Path helpers ───────────────────────────────────────────────────────────────

def _client_changelog_dir(client_id: str) -> Path:
    return REGULATORY_DATA_DIR / client_id / "changelogs"


def _client_state_dir(client_id: str) -> Path:
    return REGULATORY_DATA_DIR / client_id / "states"


def _client_output_dir(client_id: str) -> Path:
    return OUTPUT_DIR / client_id / "pdf"


# ── Utility helpers ────────────────────────────────────────────────────────────

def _list_periods(directory: Path) -> List[str]:
    """Return sorted list of YYYY-MM period strings from JSON filenames."""
    if not directory.exists():
        return []
    import re
    period_re = re.compile(r"^\d{4}-\d{2}$")
    return sorted(
        p.stem for p in directory.glob("*.json")
        if not p.name.endswith(".old.json") and period_re.match(p.stem)
    )


def _read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _serialize(obj: Any) -> Any:
    """Recursively serialize dataclass dicts, converting Enum keys/values and dates."""
    if isinstance(obj, dict):
        return {
            (k.value if isinstance(k, Enum) else k): _serialize(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_serialize(i) for i in obj]
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj


# ── Client dependency ─────────────────────────────────────────────────────────

def validate_client(client_id: str) -> str:
    """FastAPI dependency: raise 404 if client_id is not in the registry."""
    from config import list_clients
    known = {c["client_id"] for c in list_clients()}
    if client_id not in known:
        raise HTTPException(status_code=404, detail=f"Client not found: {client_id}")
    return client_id


# ── Client response builder ────────────────────────────────────────────────────

def _build_client_response(client_id: str, c: Dict[str, Any]) -> ClientResponse:
    facilities = [
        FacilitySchema(name=f["name"], jurisdiction=f["jurisdiction"])
        if isinstance(f, dict)
        else FacilitySchema(name=f, jurisdiction="")
        for f in c.get("facilities", [])
    ]
    sources = [SourceConfig(**s) for s in c.get("sources", [])]
    raw_thresh = c.get("thresholds", {})
    thresholds = Thresholds(**raw_thresh) if raw_thresh else Thresholds()
    raw_prefs = c.get("report_preferences", {})
    report_preferences = ReportPreferences(**raw_prefs) if raw_prefs else ReportPreferences()
    return ClientResponse(
        client_id=client_id,
        display_name=c.get("display_name", client_id),
        facilities=facilities,
        allowed_countries=c.get("allowed_countries", []),
        required_topics=c.get("required_topics", []),
        branding=c.get("branding"),
        created_at=c.get("created_at"),
        sources=sources,
        thresholds=thresholds,
        report_preferences=report_preferences,
    )
