"""
Source proposals router — list, suggest, approve/reject/pause.

Note: This manages `source_proposals` (SQLite), which is distinct from
the config-based `/api/clients/{cid}/sources` endpoint in the clients router.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException

from api.deps import REGULATORY_DATA_DIR, validate_client
from api.schemas_mars import (
    SourceProposalAction,
    SourceProposalImpactRecord,
    SourceProposalImpactResponse,
    SourceProposalResponse,
)

sources_router = APIRouter(
    prefix="/api/clients/{client_id}/source-proposals",
    tags=["source-proposals"],
)


def _row_to_response(row: Any) -> SourceProposalResponse:
    return SourceProposalResponse(
        id=row["id"],
        client_id=row["client_id"],
        url=row["url"],
        title=row["title"],
        publisher=row["publisher"],
        rationale=row["rationale"],
        status=row["status"],
        proposed_by=row["proposed_by"],
        reviewed_by=row["reviewed_by"],
        reviewed_at=row["reviewed_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _latest_changelog_path(client_id: str) -> Path | None:
    changelog_dir = REGULATORY_DATA_DIR / client_id / "changelogs"
    if not changelog_dir.exists():
        return None
    files = sorted(changelog_dir.glob("*.json"))
    return files[-1] if files else None


def _flatten_changelog_records(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []

    records: list[dict[str, Any]] = []
    for key, value in payload.items():
        if not isinstance(value, list):
            continue
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                continue
            title = (
                item.get("title")
                or item.get("heading")
                or item.get("name")
                or f"{key.replace('_', ' ').title()} {index + 1}"
            )
            topic = str(item.get("topic") or item.get("category") or key).replace("_", " ")
            paragraphs = item.get("paragraphs")
            body = " ".join(paragraphs) if isinstance(paragraphs, list) else str(item.get("summary") or item.get("description") or "")
            regulation_id = str(
                item.get("regulation_id")
                or item.get("id")
                or item.get("slug")
                or f"{key}-{index + 1}"
            )
            records.append(
                {
                    "regulation_id": regulation_id,
                    "title": str(title),
                    "topic": topic,
                    "text": f"{title} {body}".lower(),
                }
            )
    return records


def _proposal_terms(row: Any) -> list[str]:
    parsed = urlparse(row["url"])
    host_terms = [part for part in parsed.netloc.replace(".", " ").split() if len(part) > 2]
    title_terms = str(row["title"] or "").lower().replace("—", " ").replace("-", " ").split()
    publisher_terms = str(row["publisher"] or "").lower().replace("-", " ").split()
    rationale_terms = str(row["rationale"] or "").lower().replace("-", " ").split()

    deduped: list[str] = []
    for term in host_terms + title_terms + publisher_terms + rationale_terms:
        cleaned = term.strip(".,:;()[]{}").lower()
        if len(cleaned) < 4 or cleaned in deduped:
            continue
        deduped.append(cleaned)
    return deduped[:10]


@sources_router.get("", response_model=List[SourceProposalResponse], summary="List source proposals")
def list_proposals(
    client_id: str = Depends(validate_client),
    status: str | None = None,
) -> List[SourceProposalResponse]:
    from db import get_db
    with get_db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM source_proposals WHERE client_id=? AND status=? ORDER BY id",
                (client_id, status),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM source_proposals WHERE client_id=? ORDER BY id",
                (client_id,),
            ).fetchall()
    return [_row_to_response(r) for r in rows]


@sources_router.get(
    "/{proposal_id}/impact",
    response_model=SourceProposalImpactResponse,
    summary="Preview proposal impact against current client coverage",
)
def proposal_impact(
    proposal_id: int,
    client_id: str = Depends(validate_client),
) -> SourceProposalImpactResponse:
    from db import get_db

    with get_db() as conn:
        proposal = conn.execute(
            "SELECT * FROM source_proposals WHERE id=? AND client_id=?",
            (proposal_id, client_id),
        ).fetchone()
        if proposal is None:
            raise HTTPException(404, f"Source proposal {proposal_id} not found")

        keywords = conn.execute(
            "SELECT phrase FROM keyword_rules WHERE client_id=? AND is_active=1 ORDER BY id",
            (client_id,),
        ).fetchall()

    changelog_path = _latest_changelog_path(client_id)
    if changelog_path is None:
        return SourceProposalImpactResponse(
            proposal_id=proposal_id,
            estimated_matches=0,
            sample_regulations=[],
            coverage_delta=0.0,
        )

    try:
        with open(changelog_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return SourceProposalImpactResponse(
            proposal_id=proposal_id,
            estimated_matches=0,
            sample_regulations=[],
            coverage_delta=0.0,
        )

    terms = _proposal_terms(proposal)
    keyword_terms = [row["phrase"].lower() for row in keywords if row["phrase"]]
    records = _flatten_changelog_records(payload)

    matches = []
    for record in records:
        score = sum(1 for term in terms if term in record["text"])
        keyword_hits = sum(1 for keyword in keyword_terms if keyword in record["text"])
        total_score = score + keyword_hits
        if total_score <= 0:
            continue
        matches.append((total_score, record))

    matches.sort(key=lambda item: item[0], reverse=True)
    sample = [
        SourceProposalImpactRecord(
            regulation_id=record["regulation_id"],
            title=record["title"],
            topic=record["topic"],
        )
        for _, record in matches[:3]
    ]
    estimated_matches = len(matches)
    coverage_delta = round(min(0.35, 0.04 * estimated_matches), 3)

    return SourceProposalImpactResponse(
        proposal_id=proposal_id,
        estimated_matches=estimated_matches,
        sample_regulations=sample,
        coverage_delta=coverage_delta,
    )


@sources_router.post(
    "/suggest",
    response_model=List[SourceProposalResponse],
    status_code=201,
    summary="Trigger agent source suggestion",
)
def suggest_sources(
    client_id: str = Depends(validate_client),
) -> List[SourceProposalResponse]:
    """
    Invoke the source-scout agent to propose new sources for this client.
    Returns the newly created proposals.
    """
    from db import get_db
    try:
        from agents.source_scout import SourceScoutAgent
        agent = SourceScoutAgent()
        result = agent.propose_sources(client_id=client_id)
        proposals = result.get("proposals", [])
    except (AttributeError, Exception):
        # propose_sources() not yet implemented on the agent — return empty
        proposals = []

    created = []
    with get_db() as conn:
        for p in proposals:
            existing = conn.execute(
                """SELECT * FROM source_proposals
                   WHERE client_id=? AND url=? AND status IN ('pending', 'approved', 'paused')
                   ORDER BY id DESC
                   LIMIT 1""",
                (client_id, p.get("url", "")),
            ).fetchone()
            if existing is not None:
                created.append(_row_to_response(existing))
                continue

            cur = conn.execute(
                """INSERT INTO source_proposals
                   (client_id, url, title, publisher, rationale, proposed_by)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    client_id,
                    p.get("url", ""),
                    p.get("title"),
                    p.get("publisher"),
                    p.get("rationale"),
                    "source-scout",
                ),
            )
            row = conn.execute(
                "SELECT * FROM source_proposals WHERE id=?", (cur.lastrowid,)
            ).fetchone()
            created.append(_row_to_response(row))
    return created


@sources_router.post(
    "/{proposal_id}/action",
    response_model=SourceProposalResponse,
    summary="Approve, reject, or pause a source proposal",
)
def action_proposal(
    proposal_id: int,
    body: SourceProposalAction,
    client_id: str = Depends(validate_client),
) -> SourceProposalResponse:
    status_map = {"approve": "approved", "reject": "rejected", "pause": "paused"}
    new_status = status_map[body.action]

    from db import get_db
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM source_proposals WHERE id=? AND client_id=?",
            (proposal_id, client_id),
        ).fetchone()
        if existing is None:
            raise HTTPException(404, f"Source proposal {proposal_id} not found")

        conn.execute(
            """UPDATE source_proposals
               SET status=?, reviewed_by=?,
                   reviewed_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now'),
                   updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
               WHERE id=? AND client_id=?""",
            (new_status, body.reviewer, proposal_id, client_id),
        )
        row = conn.execute(
            "SELECT * FROM source_proposals WHERE id=?", (proposal_id,)
        ).fetchone()
    return _row_to_response(row)
