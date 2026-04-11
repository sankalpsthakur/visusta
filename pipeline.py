#!/usr/bin/env python3
"""
VISUSTA — Monthly → Quarterly Pipeline Orchestrator

Orchestrates the full regulatory intelligence pipeline:
  1. Monthly screening (regulatory_screening.py)
  2. Model adaptation (models.py — MonthlyToQuarterlyAdapter)
  3. Quarterly consolidation (quarterly_consolidator.py)
  4. PDF generation (build_monthly_report.py / build_quarterly_brief.py)

Public API
----------
run_monthly_pipeline(client_id, period)           → MonthlyChangelog
run_quarterly_pipeline(client_id, quarter, year)  → QuarterlySummary
generate_monthly_pdf(client_id, period)           → str (output path)
generate_quarterly_pdf(client_id, quarter, year)  → str (output path)
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# ── Domain models ─────────────────────────────────────────────────────────────
from regulatory_screening import (
    MonthlyChangelog,
    RegulatoryScreeningModule,
    FileSystemRegulationStore,
    MonthlyScreeningInput,
)
from quarterly_consolidator import (
    QuarterlySummary,
    QuarterlyConsolidator,
    ChangeLogEntry as QuarterlyChangeLogEntry,
    load_entries_from_json,
    run_quarterly_consolidation,
)
from models import (
    MonthlyToQuarterlyAdapter,
    load_monthly_changelog_from_json,
)


# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).parent
REGULATORY_DATA_DIR = PROJECT_ROOT / "regulatory_data"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Mapping: quarter name → list of YYYY-MM period strings
QUARTER_PERIODS: Dict[str, Dict[int, List[str]]] = {
    "Q1": {2026: ["2026-01", "2026-02", "2026-03"]},
    "Q2": {2026: ["2026-04", "2026-05", "2026-06"]},
    "Q3": {2026: ["2026-07", "2026-08", "2026-09"]},
    "Q4": {2026: ["2026-10", "2026-11", "2026-12"]},
}


# ════════════════════════════════════════════════════════════════════════════
# PATH HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _client_data_dir(client_id: str) -> Path:
    """Return the regulatory_data sub-directory for a given client."""
    return REGULATORY_DATA_DIR / client_id


def _client_output_dir(client_id: str) -> Path:
    """Return the PDF output sub-directory for a given client."""
    return OUTPUT_DIR / client_id / "pdf"


def _client_changelog_path(client_id: str, period: str) -> Path:
    """Return the archived monthly changelog path for a client/period."""
    return _client_data_dir(client_id) / "changelogs" / f"{period}.json"


# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _load_client_preferences(client_id: str) -> Dict[str, Any]:
    """Load saved report preferences for a client from the registry."""
    try:
        from config import load_client_registry
        registry = load_client_registry()
        return dict(registry.get(client_id, {}).get("report_preferences", {}))
    except Exception:
        return {}


def _get_screening_module(client_id: str) -> RegulatoryScreeningModule:
    """Build a RegulatoryScreeningModule backed by the client's filesystem store."""
    store = FileSystemRegulationStore(_client_data_dir(client_id))
    return RegulatoryScreeningModule(store=store)


def _quarter_periods(quarter: str, year: int) -> List[str]:
    """
    Return the three YYYY-MM period strings for a given quarter and year.

    Falls back to computing them if not in the lookup table.
    """
    try:
        return QUARTER_PERIODS[quarter][year]
    except KeyError:
        q_month_starts = {"Q1": 1, "Q2": 4, "Q3": 7, "Q4": 10}
        start = q_month_starts.get(quarter.upper(), 1)
        return [f"{year}-{str(m).zfill(2)}" for m in range(start, start + 3)]


def _load_quarterly_entries_for_period(
    client_id: str, period: str
) -> List[QuarterlyChangeLogEntry]:
    """
    Load quarterly-compatible entries for a single monthly period.

    Strategy (in priority order):
    1. If the sample_monthly_data.json flat format exists (entries key), use load_entries_from_json.
    2. If a changelog JSON exists in regulatory_data/{client_id}/changelogs/, load it as a
       MonthlyChangelog and run it through MonthlyToQuarterlyAdapter.
    3. Return an empty list — the quarter can still consolidate partial data.
    """
    client_data_dir = _client_data_dir(client_id)
    changelog_dir = client_data_dir / "changelogs"

    # Option 1: pre-formatted quarterly-style JSON (sample_monthly_data.json pattern)
    sample_path = PROJECT_ROOT / f"sample_monthly_data_{period}.json"
    if sample_path.exists():
        try:
            with open(sample_path) as f:
                data = json.load(f)
            if "entries" in data:
                # Write a temp flat-list file that load_entries_from_json expects
                import tempfile, os
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False
                ) as tmp:
                    json.dump(data["entries"], tmp)
                    tmp_path = tmp.name
                try:
                    return load_entries_from_json(tmp_path)
                finally:
                    os.unlink(tmp_path)
        except Exception:
            pass  # Fall through to option 2

    # Option 2: monthly changelog JSON (structured by category)
    changelog_path = changelog_dir / f"{period}.json"
    if changelog_path.exists():
        try:
            changelog = load_monthly_changelog_from_json(str(changelog_path))
            adapter = MonthlyToQuarterlyAdapter(period=period)
            return adapter.adapt_changelog(changelog, exclude_carried_forward=True)
        except Exception as exc:
            print(f"[pipeline] Warning: could not load/adapt {changelog_path}: {exc}")

    return []


# ════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ════════════════════════════════════════════════════════════════════════════

def run_monthly_pipeline(
    client_id: str,
    period: str,
    input_data: Optional[MonthlyScreeningInput] = None,
) -> MonthlyChangelog:
    """
    Execute the monthly screening pipeline and return a MonthlyChangelog.

    Args:
        client_id: Client identifier, e.g. "gerold-foods".
        period: YYYY-MM string, e.g. "2026-02".
        input_data: Optional pre-loaded MonthlyScreeningInput. If None, the
                    module will attempt to fetch from registered sources.

    Returns:
        MonthlyChangelog — the complete monthly change detection output.
        The changelog is also persisted to regulatory_data/{client_id}/changelogs/{period}.json.
    """
    module = _get_screening_module(client_id)
    changelog = module.run_monthly_screening(period=period, input_data=input_data)

    # Persist the changelog so downstream quarterly runs can find it
    store = FileSystemRegulationStore(_client_data_dir(client_id))
    store.save_changelog(changelog)

    return changelog


def run_quarterly_pipeline(
    client_id: str,
    quarter: str,
    year: int,
    changelogs: Optional[Dict[str, MonthlyChangelog]] = None,
) -> QuarterlySummary:
    """
    Load three monthly changelogs, adapt them, and run quarterly consolidation.

    Args:
        client_id: Client identifier, e.g. "gerold-foods".
        quarter: "Q1", "Q2", "Q3", or "Q4".
        year: Four-digit year, e.g. 2026.
        changelogs: Optional dict mapping period string → MonthlyChangelog.
                    When provided, those changelogs are adapted in-memory instead
                    of loading from disk. Useful for testing or chained pipelines.

    Returns:
        QuarterlySummary ready for PDF generation or JSON export.
    """
    periods = _quarter_periods(quarter, year)
    month_entries: List[List[QuarterlyChangeLogEntry]] = []

    for period in periods:
        if changelogs and period in changelogs:
            # In-memory path: adapt the provided MonthlyChangelog
            adapter = MonthlyToQuarterlyAdapter(period=period)
            entries = adapter.adapt_changelog(
                changelogs[period], exclude_carried_forward=True
            )
        else:
            # Disk path: load from changelog JSON and adapt
            entries = _load_quarterly_entries_for_period(client_id, period)

        month_entries.append(entries)

    # Pad to exactly 3 months if some are missing
    while len(month_entries) < 3:
        month_entries.append([])

    summary = run_quarterly_consolidation(
        month1_entries=month_entries[0],
        month2_entries=month_entries[1],
        month3_entries=month_entries[2],
        quarter=quarter,
        year=year,
    )

    return summary


def generate_monthly_pdf(
    client_id: str,
    period: str,
    input_data: Optional[MonthlyScreeningInput] = None,
    output_path: Optional[str] = None,
    preferences: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Run monthly screening and generate a PDF impact report.

    Args:
        client_id: Client identifier, e.g. "gerold-foods".
        period: YYYY-MM string, e.g. "2026-02".
        input_data: Optional pre-loaded MonthlyScreeningInput.
        output_path: Override the default output file path.

    Returns:
        Path to the generated PDF file.
    """
    changelog_path = _client_changelog_path(client_id, period)

    if input_data is not None:
        run_monthly_pipeline(client_id=client_id, period=period, input_data=input_data)
    elif not changelog_path.exists():
        raise FileNotFoundError(
            f"No archived changelog found for client '{client_id}' and period '{period}'."
        )

    if output_path is None:
        out_dir = _client_output_dir(client_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(out_dir / f"Monthly_Impact_Report_{period}.pdf")

    merged_prefs = _load_client_preferences(client_id)
    if preferences:
        merged_prefs.update(preferences)

    from build_monthly_report import build_pdf

    return build_pdf(period=period, client_id=client_id, output_path=output_path, preferences=merged_prefs or None)


def generate_quarterly_pdf(
    client_id: str,
    quarter: str,
    year: int,
    changelogs: Optional[Dict[str, MonthlyChangelog]] = None,
    output_path: Optional[str] = None,
    preferences: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Run the full monthly→quarterly pipeline and generate a quarterly PDF brief.

    Args:
        client_id: Client identifier, e.g. "gerold-foods".
        quarter: "Q1", "Q2", "Q3", or "Q4".
        year: Four-digit year, e.g. 2026.
        changelogs: Optional pre-loaded changelogs (see run_quarterly_pipeline).
        output_path: Override the default output file path.

    Returns:
        Path to the generated PDF file.
    """
    if output_path is None:
        out_dir = _client_output_dir(client_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(out_dir / f"Quarterly_Strategic_Brief_{quarter}_{year}.pdf")

    quarter_period = _quarter_periods(quarter, year)[0]

    merged_prefs = _load_client_preferences(client_id)
    if preferences:
        merged_prefs.update(preferences)

    from build_quarterly_brief import build_pdf

    return build_pdf(period=quarter_period, client_id=client_id, output_path=output_path, preferences=merged_prefs or None)


# ════════════════════════════════════════════════════════════════════════════
# CONVENIENCE: adapter-only entry point (no side effects)
# ════════════════════════════════════════════════════════════════════════════

def adapt_monthly_to_quarterly(
    changelog: MonthlyChangelog,
    period: str,
    exclude_carried_forward: bool = True,
) -> List[QuarterlyChangeLogEntry]:
    """
    Thin wrapper around MonthlyToQuarterlyAdapter for direct use.

    Args:
        changelog: Monthly screening output.
        period: YYYY-MM string for the changelog's period.
        exclude_carried_forward: Skip no-change entries (default True).

    Returns:
        List of quarterly ChangeLogEntry objects.
    """
    adapter = MonthlyToQuarterlyAdapter(period=period)
    return adapter.adapt_changelog(changelog, exclude_carried_forward=exclude_carried_forward)
