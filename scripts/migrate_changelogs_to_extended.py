"""
Migrate existing changelog JSON files from flat schema to extended schema.
Preserves all original fields (backward compat) and adds:
  client_context, sections[], impact_summary_table, references,
  confidence_scores, approval_state, agent_log
"""

import glob
import json
import re
import shutil
from pathlib import Path

BASE = Path(__file__).parent.parent

CLIENT_CONTEXT = {
    "gerold-foods": {
        "facility_line": "Hamburg Bakery & Rietberg Cold Cuts, Federal Republic of Germany",
        "audience": "Executive Leadership, Regulatory Affairs & Operations",
        "jurisdiction_label": "EU & German Sustainability Frameworks for Food Manufacturers",
    },
    "alpine-dairy": {
        "facility_line": "Zurich Cheese Works & Bern Yogurt Plant, Swiss Confederation",
        "audience": "Executive Leadership, Regulatory Affairs & Operations",
        "jurisdiction_label": "EU & Swiss Sustainability Frameworks for Dairy Manufacturers",
    },
    "nordic-harvest": {
        "facility_line": "Oslo Seafood & Bergen Fish Oils, Kingdom of Norway",
        "audience": "Executive Leadership, Regulatory Affairs & Operations",
        "jurisdiction_label": "EEA & Norwegian Sustainability Frameworks for Seafood Processors",
    },
    "trivento-foods": {
        "facility_line": "Parma Pasta & Modena Olive Oil, Italian Republic",
        "audience": "Executive Leadership, Regulatory Affairs & Operations",
        "jurisdiction_label": "EU & Italian Sustainability Frameworks for Food Manufacturers",
    },
    "terra-verde": {
        "facility_line": "Lisbon Juices & Porto Organic Veg, Portuguese Republic",
        "audience": "Executive Leadership, Regulatory Affairs & Operations",
        "jurisdiction_label": "EU & Portuguese Sustainability Frameworks for Organic Food Producers",
    },
    "brosel-backwaren": {
        "facility_line": "Munich Bread Works & Vienna Pastries, Germany / Austria",
        "audience": "Executive Leadership, Regulatory Affairs & Operations",
        "jurisdiction_label": "EU, German & Austrian Sustainability Frameworks for Bakery Manufacturers",
    },
}

# Known EUR-Lex regulation CELEX patterns → canonical citation + URL
EURLEX_PATTERNS = {
    "2022/2464": (
        "Directive (EU) 2022/2464 — Corporate Sustainability Reporting Directive",
        "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022L2464",
    ),
    "2025/40": (
        "Regulation (EU) 2025/40 on packaging and packaging waste",
        "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32025R0040",
    ),
    "2023/1115": (
        "Regulation (EU) 2023/1115 — EU Deforestation-free Products Regulation",
        "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R1115",
    ),
    "2018/848": (
        "Regulation (EU) 2018/848 on organic production and labelling",
        "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32018R0848",
    ),
    "2016/2284": (
        "Directive (EU) 2016/2284 — National Emission Ceilings Directive",
        "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016L2284",
    ),
}

# Regulation-id prefix → jurisdiction citation hint
REGULATION_REFERENCES = {
    "EU-CSRD": ("2022/2464",),
    "EU-PPWR": ("2025/40",),
    "EU-EUDR": ("2023/1115",),
    "EU-NEC": ("2016/2284",),
    "EU-ORGANIC": ("2018/848",),
}


def _split_paragraphs(text: str) -> list[str]:
    """Split text on blank lines or newlines into paragraphs."""
    paras = re.split(r"\n{2,}", text.strip())
    if len(paras) == 1:
        paras = [p.strip() for p in text.split("\n") if p.strip()]
    return [p.strip() for p in paras if p.strip()]


def _regulation_to_section(reg: dict) -> dict:
    """Convert a regulation entry (new_reg / status_change / content_update) to a section."""
    heading = reg.get("title", reg.get("regulation_id", "Regulatory Update"))
    paragraphs = []

    summary = reg.get("summary", "")
    if summary:
        paragraphs.append(summary)

    description = reg.get("description", "")
    if description:
        paragraphs.extend(_split_paragraphs(description))

    if not paragraphs:
        paragraphs = ["No additional detail available."]

    section = {"heading": heading, "paragraphs": paragraphs}

    action = reg.get("action_required", "")
    if action:
        section["callout"] = action

    return section


def _build_sections(data: dict) -> list[dict]:
    """Build sections[] from new_regulations, status_changes, content_updates."""
    sections = []
    seen_ids = set()

    for source in ("new_regulations", "status_changes", "content_updates", "ended_regulations"):
        for reg in data.get(source, []):
            rid = reg.get("regulation_id", "")
            if rid in seen_ids:
                continue
            seen_ids.add(rid)
            sections.append(_regulation_to_section(reg))

    # Cap at 5 sections
    return sections[:5]


def _build_impact_table(data: dict) -> dict:
    """Build impact_summary_table from critical_actions and high-severity changes."""
    headers = ["Regulation", "Topic", "Effect", "Action"]
    rows = []

    for action in data.get("critical_actions", []):
        rows.append([
            action.get("regulation_id", ""),
            action.get("topic", ""),
            action.get("summary", ""),
            action.get("action_required", ""),
        ])

    for source in ("status_changes", "new_regulations", "content_updates", "ended_regulations"):
        for reg in data.get(source, []):
            if reg.get("severity") in ("high", "critical"):
                rid = reg.get("regulation_id", "")
                if any(r[0] == rid for r in rows):
                    continue
                rows.append([
                    rid,
                    reg.get("topic", ""),
                    reg.get("summary", ""),
                    reg.get("action_required", ""),
                ])

    return {"headers": headers, "rows": rows}


def _build_references(data: dict, generated_date: str) -> list[dict]:
    """Extract EUR-Lex references from regulation IDs and text."""
    refs = []
    seen_celex = set()

    def _try_add(reg_id: str, description_text: str = "") -> None:
        # Match by regulation_id prefix
        for prefix, celex_ids in REGULATION_REFERENCES.items():
            if reg_id.startswith(prefix):
                for celex in celex_ids:
                    if celex not in seen_celex:
                        seen_celex.add(celex)
                        citation, url = EURLEX_PATTERNS[celex]
                        refs.append({"citation": citation, "url": url, "access_date": generated_date})

        # Scan description text for EUR-Lex CELEX numbers like 32022L2464
        if description_text:
            found = re.findall(r"3\d{4}[LR]\d{4}", description_text)
            for match in found:
                # Map back: 32022L2464 → 2022/2464
                year = match[1:5]
                kind = match[5]  # L or R
                num = match[6:]
                short = f"{year}/{num}"
                if short in EURLEX_PATTERNS and short not in seen_celex:
                    seen_celex.add(short)
                    citation, url = EURLEX_PATTERNS[short]
                    refs.append({"citation": citation, "url": url, "access_date": generated_date})

    for source in ("new_regulations", "status_changes", "content_updates", "ended_regulations"):
        for reg in data.get(source, []):
            _try_add(reg.get("regulation_id", ""), reg.get("description", ""))

    return refs


def _build_confidence_scores(sections: list[dict]) -> dict:
    scores = {"executive_summary": 0.85}
    for i in range(len(sections)):
        scores[f"sections[{i}]"] = 0.85
    return scores


def migrate_changelog(path: Path, client_id: str) -> None:
    """Migrate a single changelog file in-place, backing up original."""
    backup = path.with_suffix(".old.json")
    if backup.exists():
        print(f"  SKIP (already migrated): {path}")
        return

    with open(path) as f:
        data = json.load(f)

    # Already migrated?
    if "client_context" in data:
        print(f"  SKIP (already has client_context): {path}")
        return

    # Backup original
    shutil.copy2(path, backup)

    generated_date = data.get("generated_date", data.get("screening_period", "2026-01-01"))

    context = CLIENT_CONTEXT.get(client_id, {
        "facility_line": f"{client_id} facilities",
        "audience": "Executive Leadership, Regulatory Affairs & Operations",
        "jurisdiction_label": "EU Sustainability Frameworks",
    })

    sections = _build_sections(data)
    impact_table = _build_impact_table(data)
    references = _build_references(data, generated_date)
    confidence = _build_confidence_scores(sections)

    extended = {
        "screening_period": data["screening_period"],
        "generated_date": data.get("generated_date", ""),
        "previous_period": data.get("previous_period", ""),
        "client_context": context,
        "executive_summary": data.get("executive_summary", ""),
        "sections": sections,
        "impact_summary_table": impact_table,
        "references": references,
        # Backward-compat fields
        "total_regulations_tracked": data.get("total_regulations_tracked", 0),
        "total_changes_detected": data.get("total_changes_detected", 0),
        "topic_change_statuses": data.get("topic_change_statuses", {}),
        "new_regulations": data.get("new_regulations", []),
        "status_changes": data.get("status_changes", []),
        "content_updates": data.get("content_updates", []),
        "timeline_changes": data.get("timeline_changes", []),
        "metadata_updates": data.get("metadata_updates", []),
        "ended_regulations": data.get("ended_regulations", []),
        "carried_forward": data.get("carried_forward", []),
        "critical_actions": data.get("critical_actions", []),
        # New stubs
        "confidence_scores": confidence,
        "approval_state": {"status": "draft", "by": None, "at": None},
        "agent_log": [],
    }

    with open(path, "w") as f:
        json.dump(extended, f, indent=2, ensure_ascii=False)

    print(f"  Migrated: {path} ({len(sections)} sections, {len(references)} refs)")


def main() -> None:
    pattern = str(BASE / "regulatory_data" / "*" / "changelogs" / "*.json")
    files = sorted(glob.glob(pattern))

    # Filter out backups
    files = [f for f in files if not f.endswith(".old.json")]

    if not files:
        print("No changelog files found.")
        return

    print(f"Found {len(files)} changelog files to migrate.\n")

    for file_path in files:
        path = Path(file_path)
        # client_id is the directory two levels up from the file
        client_id = path.parent.parent.name
        print(f"[{client_id}] {path.name}")
        migrate_changelog(path, client_id)

    print("\nDone. Verifying new fields...")
    ok_count = 0
    for file_path in files:
        with open(file_path) as f:
            d = json.load(f)
        if "client_context" in d and "sections" in d:
            ok_count += 1
            print(f"  {file_path} ✓")
        else:
            print(f"  {file_path} MISSING FIELDS")

    print(f"\n{ok_count}/{len(files)} files verified.")


if __name__ == "__main__":
    main()
