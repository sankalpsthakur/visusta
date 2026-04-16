"""
State machine for report draft status transitions.

Valid statuses:
    composing → review → revision → translating → approval → approved → exported → archived
    (with several cross-edges; see TRANSITIONS below)
"""

from __future__ import annotations

# Adjacency map: current_status → set of valid next statuses
TRANSITIONS: dict[str, set[str]] = {
    "composing":   {"review"},
    "review":      {"revision", "translating", "approval", "archived"},
    "revision":    {"review"},
    "translating": {"review", "revision"},
    "approval":    {"approved", "revision"},
    "approved":    {"exported", "archived"},
    "exported":    {"archived"},
    "archived":    set(),   # terminal — no outgoing transitions
}

ALL_STATUSES: frozenset[str] = frozenset(TRANSITIONS.keys())


def validate_transition(current: str, target: str) -> bool:
    """
    Return True if transitioning from *current* to *target* is valid.

    Raises ValueError for unknown status values.
    """
    if current not in TRANSITIONS:
        raise ValueError(f"Unknown status: {current!r}")
    if target not in ALL_STATUSES:
        raise ValueError(f"Unknown status: {target!r}")
    return target in TRANSITIONS[current]


def allowed_transitions(current: str) -> set[str]:
    """Return the set of valid next statuses from *current*."""
    if current not in TRANSITIONS:
        raise ValueError(f"Unknown status: {current!r}")
    return set(TRANSITIONS[current])
