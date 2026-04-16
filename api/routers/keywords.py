"""
Keywords router — CRUD + preview endpoint.
"""

from __future__ import annotations

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException

from api.deps import validate_client
from api.schemas_mars import (
    KeywordPreviewRequest,
    KeywordPreviewResponse,
    KeywordRuleCreate,
    KeywordRuleResponse,
)

keywords_router = APIRouter(
    prefix="/api/clients/{client_id}/keywords",
    tags=["keywords"],
)


def _row_to_response(row: Any) -> KeywordRuleResponse:
    return KeywordRuleResponse(
        id=row["id"],
        client_id=row["client_id"],
        phrase=row["phrase"],
        locale=row["locale"],
        weight=row["weight"],
        category=row["category"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@keywords_router.get("", response_model=List[KeywordRuleResponse], summary="List keyword rules")
def list_keywords(client_id: str = Depends(validate_client)) -> List[KeywordRuleResponse]:
    from db import get_db
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM keyword_rules WHERE client_id=? AND is_active=1 ORDER BY id",
            (client_id,),
        ).fetchall()
    return [_row_to_response(r) for r in rows]


@keywords_router.post("", response_model=KeywordRuleResponse, status_code=201, summary="Create keyword rule")
def create_keyword(
    body: KeywordRuleCreate,
    client_id: str = Depends(validate_client),
) -> KeywordRuleResponse:
    from db import get_db
    try:
        with get_db() as conn:
            cur = conn.execute(
                """INSERT INTO keyword_rules (client_id, phrase, locale, weight, category)
                   VALUES (?, ?, ?, ?, ?)""",
                (client_id, body.phrase, body.locale, body.weight, body.category),
            )
            row = conn.execute(
                "SELECT * FROM keyword_rules WHERE id=?", (cur.lastrowid,)
            ).fetchone()
    except Exception as exc:
        if "UNIQUE" in str(exc):
            raise HTTPException(409, f"Keyword '{body.phrase}' already exists for locale '{body.locale}'")
        raise
    return _row_to_response(row)


@keywords_router.get("/{keyword_id}", response_model=KeywordRuleResponse, summary="Get keyword rule")
def get_keyword(
    keyword_id: int,
    client_id: str = Depends(validate_client),
) -> KeywordRuleResponse:
    from db import get_db
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM keyword_rules WHERE id=? AND client_id=?",
            (keyword_id, client_id),
        ).fetchone()
    if row is None:
        raise HTTPException(404, f"Keyword rule {keyword_id} not found")
    return _row_to_response(row)


@keywords_router.put("/{keyword_id}", response_model=KeywordRuleResponse, summary="Update keyword rule")
def update_keyword(
    keyword_id: int,
    body: KeywordRuleCreate,
    client_id: str = Depends(validate_client),
) -> KeywordRuleResponse:
    from db import get_db
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM keyword_rules WHERE id=? AND client_id=?",
            (keyword_id, client_id),
        ).fetchone()
        if existing is None:
            raise HTTPException(404, f"Keyword rule {keyword_id} not found")
        conn.execute(
            """UPDATE keyword_rules
               SET phrase=?, locale=?, weight=?, category=?,
                   updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
               WHERE id=? AND client_id=?""",
            (body.phrase, body.locale, body.weight, body.category, keyword_id, client_id),
        )
        row = conn.execute(
            "SELECT * FROM keyword_rules WHERE id=?", (keyword_id,)
        ).fetchone()
    return _row_to_response(row)


@keywords_router.delete("/{keyword_id}", summary="Soft-delete keyword rule")
def delete_keyword(
    keyword_id: int,
    client_id: str = Depends(validate_client),
) -> dict:
    from db import get_db
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM keyword_rules WHERE id=? AND client_id=?",
            (keyword_id, client_id),
        ).fetchone()
        if existing is None:
            raise HTTPException(404, f"Keyword rule {keyword_id} not found")
        conn.execute(
            """UPDATE keyword_rules
               SET is_active=0, updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
               WHERE id=? AND client_id=?""",
            (keyword_id, client_id),
        )
    return {"deleted": keyword_id}


@keywords_router.post("/preview", response_model=KeywordPreviewResponse, summary="Preview keyword matches")
def preview_keywords(
    body: KeywordPreviewRequest,
    client_id: str = Depends(validate_client),
) -> KeywordPreviewResponse:
    """Find occurrences of each phrase in the provided sample text."""
    import re
    matches = []
    text = body.sample_text
    for phrase in body.phrases:
        for m in re.finditer(re.escape(phrase), text, re.IGNORECASE):
            start, end = m.start(), m.end()
            ctx_start = max(0, start - 40)
            ctx_end = min(len(text), end + 40)
            matches.append({
                "phrase": phrase,
                "start": start,
                "end": end,
                "context": text[ctx_start:ctx_end],
            })
    return KeywordPreviewResponse(matches=matches, match_count=len(matches))
