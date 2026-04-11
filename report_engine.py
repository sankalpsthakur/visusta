#!/usr/bin/env python3
"""
report_engine.py — Jinja2 template rendering engine for Visusta PDF reports.

Renders text sections from changelog JSON data.  The returned strings are
ReportLab-compatible (they may contain <b>, <i>, <br/>, &amp;, &bull; markup
but no full HTML tags).
"""

import os
import jinja2


_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def _make_env(subdir: str) -> jinja2.Environment:
    loader = jinja2.FileSystemLoader(os.path.join(_TEMPLATE_DIR, subdir))
    env = jinja2.Environment(
        loader=loader,
        autoescape=False,       # we generate ReportLab markup, not HTML
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env


def _count_topics_changed(changelog: dict) -> int:
    statuses = changelog.get("topic_change_statuses") or {}
    return sum(1 for v in statuses.values() if v.get("changed_since_last"))


class ReportEngine:
    """
    Template rendering engine for Visusta PDF reports.

    Usage::

        engine = ReportEngine()
        sections = engine.render_monthly_content(changelog_data, period="2026-02")
        # sections["executive_summary"]  -> rendered text string
    """

    def __init__(self, template_dir: str | None = None):
        base = template_dir or _TEMPLATE_DIR
        self._monthly_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.join(base, "monthly")),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._quarterly_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.join(base, "quarterly")),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    # ── Monthly ──────────────────────────────────────────────────────

    def render_monthly_content(self, changelog: dict, period: str) -> dict:
        """
        Render all template-backed monthly report sections from changelog data.

        Returns a dict of section_name -> rendered text string.
        Falls back gracefully to empty string if a template is missing.
        """
        # Compute period_display from YYYY-MM
        period_display = _period_to_display(period)

        total_changes = changelog.get("total_changes_detected", 0)
        critical_actions = changelog.get("critical_actions") or []
        topics_changed = _count_topics_changed(changelog)

        stats = {
            "total_changes": total_changes,
            "topics_changed": topics_changed,
            "critical_count": len(critical_actions),
        }

        ctx_exec = {
            "period": period,
            "period_display": period_display,
            "stats": stats,
            "critical_actions": critical_actions,
            "executive_summary": changelog.get("executive_summary", ""),
        }

        ctx_screening = {
            "period": period,
            "previous_period": changelog.get("previous_period", ""),
        }

        ctx_critical = {
            "critical_actions": critical_actions,
        }

        ctx_references = {
            "references": changelog.get("references") or [],
        }

        return {
            "executive_summary": self._render_monthly("executive_summary.j2", ctx_exec),
            "critical_actions": self._render_monthly("critical_actions.j2", ctx_critical),
            "screening_intro": self._render_monthly("screening_intro.j2", ctx_screening),
            "references": self._render_monthly("references.j2", ctx_references),
        }

    def render_section_text(self, section: dict) -> str:
        """Render a single section dict (heading + paragraphs + optional callout) via section.j2."""
        return self._render_monthly("section.j2", {"section": section})

    def render_references(self, references: list) -> str:
        """Render a numbered citation list from a list of reference dicts via references.j2."""
        return self._render_monthly("references.j2", {"references": references})

    def _render_monthly(self, template_name: str, context: dict) -> str:
        try:
            tmpl = self._monthly_env.get_template(template_name)
            return tmpl.render(**context).strip()
        except jinja2.TemplateNotFound:
            return ""

    # ── Quarterly ────────────────────────────────────────────────────

    def render_quarterly_content(self, quarter_months: list, changelogs: dict,
                                  quarter_display: str) -> dict:
        """
        Render all template-backed quarterly report sections.

        Args:
            quarter_months: list of period strings e.g. ["2026-01","2026-02","2026-03"]
            changelogs: dict of period -> changelog dict (only available months)
            quarter_display: human-readable quarter label e.g. "Q1 2026"

        Returns a dict of section_name -> rendered text string.
        """
        total_changes = sum(
            (cl.get("total_changes_detected") or 0)
            for cl in changelogs.values()
        )
        critical_count = sum(
            len(cl.get("critical_actions") or [])
            for cl in changelogs.values()
        )

        ctx_exec = {
            "quarter_display": quarter_display,
            "months_available": len(changelogs),
            "months_total": len(quarter_months),
            "total_changes": total_changes,
            "critical_count": critical_count,
        }

        ctx_coverage = {
            "quarter_display": quarter_display,
        }

        return {
            "executive_summary": self._render_quarterly("executive_summary.j2", ctx_exec),
            "coverage_intro": self._render_quarterly("coverage_intro.j2", ctx_coverage),
        }

    def _render_quarterly(self, template_name: str, context: dict) -> str:
        try:
            tmpl = self._quarterly_env.get_template(template_name)
            return tmpl.render(**context).strip()
        except jinja2.TemplateNotFound:
            return ""

    def load_client_evidence(self, client_id: str) -> dict:
        """Load all evidence records for a client, keyed by evidence_id."""
        from pathlib import Path
        import json as _json
        evidence_dir = Path(__file__).parent / "regulatory_data" / client_id / "evidence"
        if not evidence_dir.exists():
            return {}
        records = {}
        for f in evidence_dir.glob("*.json"):
            with open(f) as fh:
                r = _json.load(fh)
                records[r["evidence_id"]] = r
        return records


# ── Helpers ──────────────────────────────────────────────────────────

def _period_to_display(period: str) -> str:
    """Convert '2026-02' to 'February 2026'."""
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    try:
        year, month = period.split("-")
        return f"{months[int(month) - 1]} {year}"
    except (ValueError, IndexError):
        return period


def quarter_for_period(period: str) -> str:
    """Return e.g. 'Q1 2026' for period '2026-02'."""
    try:
        year, month = period.split("-")
        q = (int(month) - 1) // 3 + 1
        return f"Q{q} {year}"
    except ValueError:
        return period


def quarter_months_for_period(period: str) -> list:
    """Return the three YYYY-MM strings for the quarter containing period."""
    try:
        year, month = period.split("-")
        m = int(month)
        q_start = ((m - 1) // 3) * 3 + 1
        return [f"{year}-{str(q_start + i).zfill(2)}" for i in range(3)]
    except ValueError:
        return [period]
