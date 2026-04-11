"""
Visusta configuration loader.

Usage
-----
    from config import get_config

    cfg = get_config()
    print(cfg.branding.colors.primary_dark)   # "#0D3B26"
    print(cfg.screening.allowed_countries)     # ["EU", "DE"]
    print(cfg.validation.min_sources)          # 2

Environment overrides
---------------------
Set the ``VISUSTA_CONFIG`` environment variable to an absolute path to load a
different YAML file (useful for staging / testing environments).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


# ── Sub-models ────────────────────────────────────────────────────────────────

class BrandColors(BaseModel):
    primary_dark:   str = "#0D3B26"
    primary:        str = "#1A6B4B"
    primary_light:  str = "#2E8B63"
    accent:         str = "#4CAF50"
    light_bg:       str = "#E8F5E9"
    warm_gray:      str = "#6B7B8D"
    text:           str = "#1A1A2E"
    muted:          str = "#5A6270"
    border:         str = "#D0D8DF"
    alert_red:      str = "#C62828"
    alert_amber:    str = "#F57F17"
    table_head:     str = "#0D3B26"
    table_stripe:   str = "#F0F7F2"
    deep_blue:      str = "#1565C0"
    soft_blue:      str = "#1565C0"


class BrandingConfig(BaseModel):
    colors: BrandColors = Field(default_factory=BrandColors)


class ScreeningConfig(BaseModel):
    allowed_countries:                 List[str] = ["EU", "DE"]
    critical_enforcement_window_days:  int       = 90
    required_topics:                   List[str] = [
        "ghg", "packaging", "water", "waste", "social_human_rights"
    ]


class ValidationConfig(BaseModel):
    min_sources:            int   = 2
    reliability_threshold:  float = 0.6
    confidence_threshold:   float = 0.5
    max_age_days:           int   = 90
    min_description_length: int   = 50


class ReportConfig(BaseModel):
    facilities:       List[str] = ["Hamburg", "Rietberg"]
    screening_period: str       = "2026-02"
    quarter_months:   List[str] = ["2026-01", "2026-02", "2026-03"]
    quarter_label:    str       = "Q1 2026"


# ── Root model ────────────────────────────────────────────────────────────────

class VisustaConfig(BaseModel):
    branding:   BrandingConfig   = Field(default_factory=BrandingConfig)
    screening:  ScreeningConfig  = Field(default_factory=ScreeningConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    report:     ReportConfig     = Field(default_factory=ReportConfig)


# ── Loader (singleton via lru_cache) ──────────────────────────────────────────

def _default_config_path() -> Path:
    """Return the path to ``visusta.yaml`` next to this package."""
    return Path(__file__).parent / "visusta.yaml"


@lru_cache(maxsize=1)
def get_config(config_path: Optional[str] = None) -> VisustaConfig:
    """Load and return the Visusta configuration (cached after first call).

    Parameters
    ----------
    config_path:
        Absolute path to a YAML file.  Falls back to the ``VISUSTA_CONFIG``
        environment variable, then to ``config/visusta.yaml`` next to this
        module.
    """
    path_str = config_path or os.environ.get("VISUSTA_CONFIG")
    path = Path(path_str) if path_str else _default_config_path()

    if not path.exists():
        # Graceful fallback — use Pydantic defaults
        return VisustaConfig()

    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    return VisustaConfig(**raw)


# ── Client registry ───────────────────────────────────────────────────────────

def _clients_yaml_path() -> Path:
    """Return the path to ``clients.yaml`` next to this package."""
    return Path(__file__).parent / "clients.yaml"


def _load_clients_raw() -> Dict[str, Any]:
    """Load the raw clients YAML. Returns empty dict if file missing."""
    path = _clients_yaml_path()
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_client_registry() -> dict:
    """Load and return the full clients registry dict (top-level ``clients`` key)."""
    raw = _load_clients_raw()
    return raw.get("clients", {})


def list_clients() -> List[Dict[str, Any]]:
    """Return a list of dicts with client_id, display_name, and all client fields."""
    registry = load_client_registry()
    result = []
    for client_id, data in registry.items():
        entry = {"client_id": client_id}
        entry.update(data)
        result.append(entry)
    return result


def get_client_config(client_id: str) -> VisustaConfig:
    """Load base config and merge with client-specific overrides.

    Parameters
    ----------
    client_id:
        The client identifier, e.g. ``"gerold-foods"``.

    Returns
    -------
    VisustaConfig with screening.allowed_countries, screening.required_topics,
    and report.facilities overridden from the client registry entry.

    Raises
    ------
    KeyError
        If the client_id is not found in the registry.
    """
    registry = load_client_registry()
    if client_id not in registry:
        raise KeyError(f"Client not found: {client_id}")

    client_data = registry[client_id]
    base_cfg = get_config()

    # Build overridden sub-models
    screening_overrides: Dict[str, Any] = base_cfg.screening.model_dump()
    if "allowed_countries" in client_data:
        screening_overrides["allowed_countries"] = client_data["allowed_countries"]
    if "required_topics" in client_data:
        screening_overrides["required_topics"] = client_data["required_topics"]

    report_overrides: Dict[str, Any] = base_cfg.report.model_dump()
    if "facilities" in client_data:
        report_overrides["facilities"] = [
            f["name"] if isinstance(f, dict) else f
            for f in client_data["facilities"]
        ]

    return VisustaConfig(
        branding=base_cfg.branding,
        screening=ScreeningConfig(**screening_overrides),
        validation=base_cfg.validation,
        report=ReportConfig(**report_overrides),
    )


def save_client_registry(registry: Dict[str, Any]) -> None:
    """Persist the client registry dict back to ``clients.yaml``.

    Parameters
    ----------
    registry:
        The ``clients`` sub-dict mapping client_id -> client data.
    """
    path = _clients_yaml_path()
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump({"clients": registry}, fh, allow_unicode=True, sort_keys=False)
