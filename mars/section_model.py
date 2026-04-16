"""
Serialization/deserialization for DraftSection and section-level diff.
"""

from __future__ import annotations

import json
from typing import Any

from api.schemas_mars import DraftSection


def sections_to_json(sections: list[DraftSection]) -> str:
    """Serialize a list of DraftSection objects to a JSON string."""
    return json.dumps([s.model_dump() for s in sections], ensure_ascii=False)


def sections_from_json(raw: str) -> list[DraftSection]:
    """Deserialize a JSON string into a list of DraftSection objects."""
    data = json.loads(raw)
    return [DraftSection(**item) for item in data]


def diff_sections(
    old: list[DraftSection],
    new: list[DraftSection],
) -> list[str]:
    """
    Return the section_ids of sections that changed between *old* and *new*.

    A section is considered changed if:
    - its section_id appears in new but not in old (added), or
    - its section_id appears in old but not in new (removed), or
    - the serialized content differs between old and new.
    """
    old_by_id: dict[str, dict[str, Any]] = {
        s.section_id: s.model_dump() for s in old
    }
    new_by_id: dict[str, dict[str, Any]] = {
        s.section_id: s.model_dump() for s in new
    }

    changed: list[str] = []

    all_ids = set(old_by_id) | set(new_by_id)
    for sid in all_ids:
        if old_by_id.get(sid) != new_by_id.get(sid):
            changed.append(sid)

    return changed
