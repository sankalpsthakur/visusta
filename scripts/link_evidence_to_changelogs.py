#!/usr/bin/env python3
"""
Link evidence records to changelog sections by topic and regulation ID match.

For each client, loads evidence records and updates changelog section
evidence_refs to use the real evidence_ids from the evidence directory.
"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent / "regulatory_data"

# Keywords in regulation IDs to match against evidence related_regulation_id
REGULATION_KEYWORD_MAP = {
    "verpack": ["VerpackDG", "PPWR", "packaging"],
    "csrd": ["CSRD", "ESRS"],
    "lksg": ["LkSG"],
    "ppwr": ["PPWR", "packaging"],
    "eudr": ["EUDR"],
    "ghg": ["KSG", "ETS", "ghg"],
    "water": ["water", "wastewater"],
    "waste": ["waste", "kreislauf"],
    "social": ["LkSG", "social"],
}


def _normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _evidence_matches_heading(evidence: dict, heading: str) -> bool:
    heading_norm = _normalize(heading)
    reg_id = _normalize(evidence.get("related_regulation_id", ""))
    title_norm = _normalize(evidence.get("document_title", ""))

    if reg_id and reg_id in heading_norm:
        return True
    if reg_id and heading_norm in reg_id:
        return True
    for keyword in re.findall(r"[A-Za-z]{3,}", heading):
        if _normalize(keyword) in reg_id or _normalize(keyword) in title_norm:
            return True
    return False


def _evidence_matches_topic(evidence: dict, topic: str) -> bool:
    ev_topic = (evidence.get("topic") or "").lower()
    if not ev_topic or ev_topic == "unknown":
        return False
    topic_norm = topic.lower().replace("_", "")
    return ev_topic in topic_norm or topic_norm.startswith(ev_topic)


def _section_topic(section: dict, changelog: dict) -> str:
    heading = section.get("heading", "").lower()
    statuses = changelog.get("topic_change_statuses") or {}
    for topic in statuses:
        topic_keywords = {
            "ghg": ["ghg", "emission", "co2", "ets", "ksg", "csrd", "esrs"],
            "packaging": ["pack", "verpack", "ppwr", "lucid", "recycl"],
            "water": ["water", "wasser"],
            "waste": ["waste", "abfall", "kreislauf"],
            "social_human_rights": ["lksg", "social", "human rights", "supply chain", "lieferketten"],
        }
        for kw in topic_keywords.get(topic, []):
            if kw in heading:
                return topic
    return ""


def link_client(client_id: str) -> int:
    client_dir = BASE_DIR / client_id
    evidence_dir = client_dir / "evidence"
    changelogs_dir = client_dir / "changelogs"

    if not evidence_dir.exists():
        print(f"  [{client_id}] No evidence directory, skipping.")
        return 0

    # Load all evidence records
    evidence_records = []
    for f in evidence_dir.glob("*.json"):
        with open(f) as fh:
            evidence_records.append(json.load(fh))

    if not evidence_records:
        print(f"  [{client_id}] No evidence records found.")
        return 0

    updated_count = 0

    for changelog_path in sorted(changelogs_dir.glob("*.json")):
        if changelog_path.name.endswith(".old.json"):
            continue

        with open(changelog_path) as f:
            changelog = json.load(f)

        sections = changelog.get("sections") or []
        changed = False

        for section in sections:
            heading = section.get("heading", "")
            section_topic = _section_topic(section, changelog)

            # Find matching evidence records for this section
            matched_ids = []
            for ev in evidence_records:
                if _evidence_matches_heading(ev, heading):
                    matched_ids.append(ev["evidence_id"])
                elif section_topic and _evidence_matches_topic(ev, section_topic):
                    matched_ids.append(ev["evidence_id"])

            matched_ids = list(dict.fromkeys(matched_ids))  # dedupe preserving order

            if matched_ids:
                section["evidence_refs"] = matched_ids
                changed = True

        if changed:
            with open(changelog_path, "w") as f:
                json.dump(changelog, f, indent=2, ensure_ascii=False)
                f.write("\n")
            print(f"  [{client_id}] Updated {changelog_path.name}")
            updated_count += 1

    return updated_count


def main():
    clients = [d.name for d in BASE_DIR.iterdir() if d.is_dir() and (d / "evidence").exists()]
    if not clients:
        print("No clients with evidence directories found.")
        return

    total = 0
    for client_id in sorted(clients):
        print(f"Processing {client_id}...")
        total += link_client(client_id)

    print(f"\nDone. Updated {total} changelog file(s).")


if __name__ == "__main__":
    main()
