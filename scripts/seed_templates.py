"""
Idempotent seeder for default report templates.

Inserts two baseline templates ("Monthly Impact Report" and
"Quarterly Strategic Brief") into report_templates + template_versions,
but only when the report_templates table is empty. Safe to run on every
container boot (see docker-entrypoint.sh).

Run:
    python3 scripts/seed_templates.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db import get_db


DEFAULT_THEME_TOKENS: dict[str, str] = {
    "--brand-primary": "#1a1a2e",
    "--brand-accent": "#3F4E31",
    "--brand-accent-secondary": "#8B2F1E",
    "--heading-font": "Fraunces, serif",
    "--body-font": "Inter, sans-serif",
    "--report-bg": "#ffffff",
    "--report-text": "#1a1a2e",
}


def _section(
    section_id: str,
    heading: str,
    order: int,
    prompt_template: str,
    *,
    chart_types: list[str] | None = None,
    max_tokens: int = 1000,
    required: bool = True,
) -> dict:
    return {
        "section_id": section_id,
        "heading": heading,
        "order": order,
        "prompt_template": prompt_template,
        "chart_types": chart_types or [],
        "max_tokens": max_tokens,
        "required": required,
    }


TEMPLATES: list[dict] = [
    {
        "name": "Monthly Impact Report",
        "description": "Standard monthly regulatory intelligence briefing: executive summary, regulatory changes, topic-by-topic analysis, and compliance status.",
        "base_locale": "en",
        "sections": [
            _section(
                "executive_summary",
                "Executive Summary",
                0,
                "Summarize the most important regulatory developments for the reporting period in 3-5 bullet points.",
                max_tokens=900,
            ),
            _section(
                "regulatory_changes",
                "Regulatory Changes",
                1,
                "Describe the regulatory changes detected during this period, grouped by jurisdiction or topic.",
                chart_types=["topic_distribution"],
                max_tokens=1200,
            ),
            _section(
                "topic_analysis",
                "Topic-by-Topic Analysis",
                2,
                "For each material topic, explain what changed, why it matters to this client, and what actions are recommended.",
                max_tokens=1400,
            ),
            _section(
                "compliance_status",
                "Compliance Status",
                3,
                "Summarize the client's current compliance posture against the regulations covered in this period.",
                max_tokens=900,
            ),
        ],
    },
    {
        "name": "Quarterly Strategic Brief",
        "description": "Quarterly strategic overview: trend analysis, risk prioritization, forward planning, and action items for senior stakeholders.",
        "base_locale": "en",
        "sections": [
            _section(
                "trend_analysis",
                "Trend Analysis",
                0,
                "Identify the dominant regulatory trends across the quarter and highlight emerging themes.",
                chart_types=["trend_timeline"],
                max_tokens=1200,
            ),
            _section(
                "risk_prioritization",
                "Risk Prioritization",
                1,
                "Rank the most material risks by exposure and likelihood, and justify the ordering.",
                chart_types=["risk_matrix"],
                max_tokens=1100,
            ),
            _section(
                "forward_planning",
                "Forward Planning",
                2,
                "Outline the regulatory milestones expected in the next two quarters and the preparation required.",
                max_tokens=1000,
            ),
            _section(
                "action_items",
                "Action Items",
                3,
                "List specific, owner-assigned action items with deadlines derived from the analysis above.",
                max_tokens=800,
            ),
        ],
    },
]


def seed() -> int:
    """Seed defaults when report_templates is empty. Returns number of templates inserted."""
    with get_db() as conn:
        existing = conn.execute("SELECT COUNT(*) AS n FROM report_templates").fetchone()
        if existing["n"] > 0:
            print(f"[seed_templates] skip: {existing['n']} templates already present")
            return 0

        inserted = 0
        for tmpl in TEMPLATES:
            cur = conn.execute(
                """INSERT INTO report_templates
                   (name, description, base_locale, current_version, is_published, created_by)
                   VALUES (?, ?, ?, 0, 1, ?)""",
                (tmpl["name"], tmpl["description"], tmpl["base_locale"], "seed"),
            )
            template_id = cur.lastrowid

            conn.execute(
                """INSERT INTO template_versions
                   (template_id, version_number, sections_json, theme_tokens,
                    changelog_note, created_by)
                   VALUES (?, 1, ?, ?, ?, ?)""",
                (
                    template_id,
                    json.dumps(tmpl["sections"]),
                    json.dumps(DEFAULT_THEME_TOKENS),
                    "Initial seeded version",
                    "seed",
                ),
            )

            conn.execute(
                """UPDATE report_templates
                   SET current_version=1,
                       updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                   WHERE id=?""",
                (template_id,),
            )

            inserted += 1
            print(f"[seed_templates] inserted: {tmpl['name']} (id={template_id})")

        return inserted


def main() -> int:
    count = seed()
    print(f"[seed_templates] done (inserted={count})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
