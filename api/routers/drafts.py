"""
Drafts router — CRUD, compose, translate, chat, section approve.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, List, Optional

import threading
import time

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from pydantic import BaseModel

from api.deps import REGULATORY_DATA_DIR, validate_client
from api.schemas_mars import (
    ApprovalAction,
    ApprovalStateResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    DraftCreate,
    DraftDetailResponse,
    DraftResponse,
    DraftSection,
    SectionEditRequest,
    SectionBlock,
    RevisionDetailResponse,
    RevisionResponse,
)
from agents.draft_chat import DraftChatAgent
from agents.draft_composer import DraftComposerAgent
from agents.translation_agent import TranslationAgent
from api.routers.locales import _normalize_locale
from mars.draft_lifecycle import validate_transition
from mars.section_model import sections_from_json, sections_to_json

drafts_router = APIRouter(
    prefix="/api/clients/{client_id}/drafts",
    tags=["drafts"],
)


def _draft_row(row: Any) -> DraftResponse:
    return DraftResponse(
        id=row["id"],
        client_id=row["client_id"],
        template_version_id=row["template_version_id"],
        title=row["title"],
        period=row["period"],
        primary_locale=row["primary_locale"],
        status=row["status"],
        current_revision_id=row["current_revision_id"],
        created_by=row["created_by"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _revision_row(row: Any) -> RevisionResponse:
    return RevisionResponse(
        id=row["id"],
        draft_id=row["draft_id"],
        revision_number=row["revision_number"],
        authored_by=row["authored_by"],
        note=row["note"],
        created_at=row["created_at"],
    )


def _revision_detail_row(row: Any) -> RevisionDetailResponse:
    sections = sections_from_json(row["sections_json"])
    return RevisionDetailResponse(
        id=row["id"],
        draft_id=row["draft_id"],
        revision_number=row["revision_number"],
        authored_by=row["authored_by"],
        note=row["note"],
        created_at=row["created_at"],
        sections=sections,
    )


# ---------------------------------------------------------------------------
# Compose job registry
#
# Compose invokes an LLM that can take 15–30s, which exceeds Render's proxy
# and the browser's default fetch timeout. We accept the request, launch the
# work as a FastAPI BackgroundTask (runs in the threadpool after the response
# is flushed), and expose a status endpoint the client polls.
#
# The registry is in-memory and process-local: a worker restart mid-compose
# loses the job. Same failure mode as the previous synchronous handler; a
# durable jobs table is out of scope for this fix.
# ---------------------------------------------------------------------------

_compose_jobs: dict[str, dict[str, Any]] = {}
_compose_jobs_lock = threading.Lock()
_COMPOSE_JOB_TTL_SECONDS = 60 * 60  # keep finished jobs queryable for an hour


def _register_compose_job(job_id: str, draft_id: int, client_id: str) -> None:
    with _compose_jobs_lock:
        # Opportunistic TTL sweep so the dict doesn't grow unbounded.
        cutoff = time.time() - _COMPOSE_JOB_TTL_SECONDS
        stale = [jid for jid, entry in _compose_jobs.items() if entry["updated_at"] < cutoff]
        for jid in stale:
            _compose_jobs.pop(jid, None)
        _compose_jobs[job_id] = {
            "job_id": job_id,
            "draft_id": draft_id,
            "client_id": client_id,
            "status": "pending",
            "error": None,
            "revision": None,
            "updated_at": time.time(),
        }


def _update_compose_job(job_id: str, **fields: Any) -> None:
    with _compose_jobs_lock:
        entry = _compose_jobs.get(job_id)
        if entry is None:
            return
        entry.update(fields)
        entry["updated_at"] = time.time()


def _get_compose_job(job_id: str) -> Optional[dict[str, Any]]:
    with _compose_jobs_lock:
        entry = _compose_jobs.get(job_id)
        return dict(entry) if entry else None


def _run_compose_job(job_id: str, draft_id: int, client_id: str, note: Optional[str]) -> None:
    """Background worker: composes the revision and stores the result on the job."""
    from db import get_db

    _update_compose_job(job_id, status="running")
    try:
        with get_db() as conn:
            draft = conn.execute(
                "SELECT * FROM report_drafts WHERE id=? AND client_id=?",
                (draft_id, client_id),
            ).fetchone()
            if draft is None:
                raise RuntimeError(f"Draft {draft_id} not found")
            template_sections = _load_template_sections(conn, draft["template_version_id"])
            changelog_payload = _load_changelog_payload(client_id, draft["period"])
            changelog = _load_changelog_entries(client_id, draft["period"])
            evidence = _load_evidence(client_id)

            agent = DraftComposerAgent()
            result = agent.run(
                {
                    "changelog": changelog,
                    "changelog_payload": changelog_payload,
                    "evidence": evidence,
                    "template_sections": template_sections,
                    "locale": draft["primary_locale"],
                }
            )
            raw_sections = result.get("sections", [])
            if not raw_sections:
                locale = draft["primary_locale"]
                raw_sections = [{
                    "section_id": str(uuid.uuid4()),
                    "heading": "Report Draft",
                    "locale": locale,
                    "blocks": [{"block_id": "b1", "block_type": "paragraph", "content": "No content generated. Add sections to the template or provide changelog data."}],
                    "facts": [],
                    "citations": [],
                    "translation_status": "original",
                    "approval_status": "pending",
                }]
            sections = _normalize_sections(
                raw_sections,
                locale=draft["primary_locale"],
                fallback_sections=template_sections,
            )
            sections = [
                section.model_copy(
                    update={
                        "section_id": template_sections[index].get("section_id", section.section_id)
                        if index < len(template_sections) else section.section_id,
                    }
                )
                for index, section in enumerate(sections)
            ]
            _clear_approvals(conn, draft_id)
            row = _insert_revision(
                conn,
                draft=draft,
                sections=sections,
                authored_by="draft-composer",
                note=note or "Composed from template and source material",
                status="composing",
            )
        revision = _revision_detail_row(row)
        _update_compose_job(job_id, status="done", revision=revision.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001 — surface any agent/DB error to the poller
        _update_compose_job(job_id, status="failed", error=str(exc) or exc.__class__.__name__)


# ---------------------------------------------------------------------------
# Chat job registry
#
# Chat-with-section invokes the DraftChatAgent LLM which, like compose, can
# take 15–30s and exceed Render's proxy timeout when done synchronously.
# Mirror the compose async pattern: accept the POST, persist the user message
# in a short Tx1 (so audit survives any downstream failure), kick off a
# background job for the LLM call + revision write, and expose a polling
# endpoint. No-section chats remain synchronous (canned reply, no LLM).
# ---------------------------------------------------------------------------

_chat_jobs: dict[str, dict[str, Any]] = {}
_chat_jobs_lock = threading.Lock()
_CHAT_JOB_TTL_SECONDS = 60 * 60  # same TTL as compose jobs


def _register_chat_job(job_id: str, draft_id: int, client_id: str) -> None:
    with _chat_jobs_lock:
        cutoff = time.time() - _CHAT_JOB_TTL_SECONDS
        stale = [jid for jid, entry in _chat_jobs.items() if entry["updated_at"] < cutoff]
        for jid in stale:
            _chat_jobs.pop(jid, None)
        _chat_jobs[job_id] = {
            "job_id": job_id,
            "draft_id": draft_id,
            "client_id": client_id,
            "status": "pending",
            "error": None,
            "message": None,
            "updated_at": time.time(),
        }


def _update_chat_job(job_id: str, **fields: Any) -> None:
    with _chat_jobs_lock:
        entry = _chat_jobs.get(job_id)
        if entry is None:
            return
        entry.update(fields)
        entry["updated_at"] = time.time()


def _get_chat_job(job_id: str) -> Optional[dict[str, Any]]:
    with _chat_jobs_lock:
        entry = _chat_jobs.get(job_id)
        return dict(entry) if entry else None


def _run_chat_job(
    job_id: str,
    draft_id: int,
    client_id: str,
    section_id: str,
    user_content: str,
) -> None:
    """Background worker: runs the chat agent, writes a new revision, stores the assistant message."""
    from db import get_db

    _update_chat_job(job_id, status="running")
    try:
        # Tx-A: read-only snapshot of everything the agent needs. The Tx1 in
        # send_chat already wrote the user message, so the history fetched
        # here includes it — the agent receives the full conversation.
        with get_db() as conn:
            draft = conn.execute(
                "SELECT * FROM report_drafts WHERE id=? AND client_id=?",
                (draft_id, client_id),
            ).fetchone()
            if draft is None:
                raise RuntimeError(f"Draft {draft_id} not found")
            if draft["current_revision_id"] is None:
                raise RuntimeError(f"Draft {draft_id} has no current revision")
            revision = conn.execute(
                "SELECT * FROM draft_revisions WHERE id=?",
                (draft["current_revision_id"],),
            ).fetchone()
            if revision is None:
                raise RuntimeError(
                    f"Current revision {draft['current_revision_id']} missing for draft {draft_id}"
                )
            source_sections = sections_from_json(revision["sections_json"])
            history_rows = conn.execute(
                """SELECT role, content FROM draft_chat_messages
                   WHERE draft_id=? ORDER BY id""",
                (draft_id,),
            ).fetchall()
            history = [{"role": row["role"], "content": row["content"]} for row in history_rows]
            draft_locale = draft["primary_locale"]

        # LLM call: NO `with get_db()` block held. Preserves the c61ffdf
        # two-tx split so other writers aren't blocked during the 15–30s agent call.
        agent = DraftChatAgent()
        result = agent.run(
            {
                "sections": [section.model_dump() for section in source_sections],
                "section_id": section_id,
                "user_message": user_content,
                "conversation_history": history,
            }
        )
        updated_sections = _normalize_sections(
            result.get("sections", []),
            locale=draft_locale,
            fallback_sections=[section.model_dump() for section in source_sections],
        )
        updated_sections = [
            section.model_copy(update={"section_id": source_sections[index].section_id})
            for index, section in enumerate(updated_sections)
        ]

        # Tx-B: fresh short-lived tx — re-read draft, clear approvals, write
        # revision, write assistant message. Mirrors the post-LLM block in the
        # previous synchronous send_chat verbatim.
        with get_db() as conn:
            draft_now = conn.execute(
                "SELECT * FROM report_drafts WHERE id=? AND client_id=?",
                (draft_id, client_id),
            ).fetchone()
            if draft_now is None:
                raise RuntimeError(f"Draft {draft_id} disappeared during chat")
            _clear_approvals(conn, draft_id)
            new_revision = _insert_revision(
                conn,
                draft=draft_now,
                sections=updated_sections,
                authored_by="draft-chat",
                note=result.get("explanation") or "Chat-assisted edit",
                status="composing",
            )
            assistant_insert = conn.execute(
                """INSERT INTO draft_chat_messages
                   (draft_id, section_id, role, content, revision_id)
                   VALUES (?, ?, 'assistant', ?, ?)""",
                (
                    draft_id,
                    section_id,
                    result.get("explanation") or "Applied requested draft changes.",
                    new_revision["id"],
                ),
            )
            row = conn.execute(
                "SELECT * FROM draft_chat_messages WHERE id=?",
                (assistant_insert.lastrowid,),
            ).fetchone()

        message = ChatMessageResponse(
            id=row["id"],
            draft_id=row["draft_id"],
            section_id=row["section_id"],
            role=row["role"],
            content=row["content"],
            revision_id=row["revision_id"],
            created_at=row["created_at"],
        )
        _update_chat_job(job_id, status="done", message=message.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001 — surface any agent/DB error to the poller
        _update_chat_job(job_id, status="failed", error=str(exc) or exc.__class__.__name__)


# ---------------------------------------------------------------------------
# Translate job registry
#
# Translate invokes the TranslationAgent LLM which, like compose and
# chat-with-section, can take 15–30s and exceeds Render's proxy timeout when
# done synchronously. Mirror the async pattern: accept the POST, run the LLM
# call + revision write in a background task, and expose a polling endpoint.
# ---------------------------------------------------------------------------

_translate_jobs: dict[str, dict[str, Any]] = {}
_translate_jobs_lock = threading.Lock()
_TRANSLATE_JOB_TTL_SECONDS = 60 * 60  # same TTL as compose/chat jobs


def _register_translate_job(job_id: str, draft_id: int, client_id: str) -> None:
    with _translate_jobs_lock:
        cutoff = time.time() - _TRANSLATE_JOB_TTL_SECONDS
        stale = [jid for jid, entry in _translate_jobs.items() if entry["updated_at"] < cutoff]
        for jid in stale:
            _translate_jobs.pop(jid, None)
        _translate_jobs[job_id] = {
            "job_id": job_id,
            "draft_id": draft_id,
            "client_id": client_id,
            "status": "pending",
            "error": None,
            "revision": None,
            "updated_at": time.time(),
        }


def _update_translate_job(job_id: str, **fields: Any) -> None:
    with _translate_jobs_lock:
        entry = _translate_jobs.get(job_id)
        if entry is None:
            return
        entry.update(fields)
        entry["updated_at"] = time.time()


def _get_translate_job(job_id: str) -> Optional[dict[str, Any]]:
    with _translate_jobs_lock:
        entry = _translate_jobs.get(job_id)
        return dict(entry) if entry else None


def _run_translate_job(
    job_id: str,
    draft_id: int,
    client_id: str,
    target_locale: str,
) -> None:
    """Background worker: runs the translation agent and writes a new revision."""
    from db import get_db

    _update_translate_job(job_id, status="running")
    try:
        # Tx-A: read-only snapshot of the draft + source revision.
        with get_db() as conn:
            draft = conn.execute(
                "SELECT * FROM report_drafts WHERE id=? AND client_id=?",
                (draft_id, client_id),
            ).fetchone()
            if draft is None:
                raise RuntimeError(f"Draft {draft_id} not found")
            if draft["current_revision_id"] is None:
                raise RuntimeError(f"Draft {draft_id} has no current revision to translate")
            src_rev = conn.execute(
                "SELECT * FROM draft_revisions WHERE id=?",
                (draft["current_revision_id"],),
            ).fetchone()
            if src_rev is None:
                raise RuntimeError(
                    f"Current revision {draft['current_revision_id']} missing for draft {draft_id}"
                )
            source_sections = sections_from_json(src_rev["sections_json"])
            source_locale = draft["primary_locale"]

        # LLM call: NO DB connection held. Keeps the 15–30s agent call off any
        # writer/reader lock, matching the compose/chat two-tx split.
        agent = TranslationAgent()
        result = agent.run(
            {
                "sections": [section.model_dump() for section in source_sections],
                "target_locale": target_locale,
                "source_locale": source_locale,
            }
        )
        translated = _normalize_sections(
            result.get("sections", []),
            locale=target_locale,
            fallback_sections=[section.model_dump() for section in source_sections],
        )
        # Preserve section identity across revisions for approvals and diffs.
        translated = [
            section.model_copy(update={"section_id": source_sections[index].section_id})
            for index, section in enumerate(translated)
        ]

        # Tx-B: fresh short-lived tx — re-read draft, clear approvals, write revision.
        with get_db() as conn:
            draft_now = conn.execute(
                "SELECT * FROM report_drafts WHERE id=? AND client_id=?",
                (draft_id, client_id),
            ).fetchone()
            if draft_now is None:
                raise RuntimeError(f"Draft {draft_id} disappeared during translate")
            _clear_approvals(conn, draft_id)
            row = _insert_revision(
                conn,
                draft=draft_now,
                sections=translated,
                authored_by="translation-agent",
                note=f"Translation to {target_locale}",
                status="composing",
                primary_locale=target_locale,
            )

        revision = _revision_detail_row(row)
        _update_translate_job(job_id, status="done", revision=revision.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001 — surface any agent/DB error to the poller
        _update_translate_job(job_id, status="failed", error=str(exc) or exc.__class__.__name__)


def _default_template_sections() -> list[dict[str, Any]]:
    return [
        {
            "section_id": "executive_summary",
            "heading": "Executive Summary",
            "order": 0,
            "prompt_template": "Summarize the current reporting period.",
            "chart_types": [],
            "max_tokens": 900,
            "required": True,
        },
        {
            "section_id": "regulatory_changes",
            "heading": "Regulatory Changes",
            "order": 1,
            "prompt_template": "Summarize key regulatory changes.",
            "chart_types": ["topic_distribution"],
            "max_tokens": 1200,
            "required": True,
        },
        {
            "section_id": "critical_actions",
            "heading": "Critical Actions",
            "order": 2,
            "prompt_template": "List urgent actions and deadlines.",
            "chart_types": [],
            "max_tokens": 700,
            "required": False,
        },
    ]


def _load_template_sections(conn, template_version_id: int | None) -> list[dict[str, Any]]:
    if template_version_id is None:
        return _default_template_sections()

    row = conn.execute(
        "SELECT sections_json FROM template_versions WHERE id=?",
        (template_version_id,),
    ).fetchone()
    if row is None:
        return _default_template_sections()

    try:
        sections = json.loads(row["sections_json"])
    except (TypeError, json.JSONDecodeError):
        sections = []

    return sections or _default_template_sections()


def _load_changelog_entries(client_id: str, period: str | None) -> list[dict[str, Any]]:
    payload = _load_changelog_payload(client_id, period)
    entries: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        for value in payload.values():
            if isinstance(value, list):
                entries.extend(item for item in value if isinstance(item, dict))
    return entries[:50]


def _load_changelog_payload(client_id: str, period: str | None) -> dict[str, Any]:
    changelog_dir = REGULATORY_DATA_DIR / client_id / "changelogs"
    if not changelog_dir.exists():
        return {}

    candidate = None
    if period:
        maybe = changelog_dir / f"{period}.json"
        if maybe.exists():
            candidate = maybe

    if candidate is None:
        files = sorted(changelog_dir.glob("*.json"))
        if not files:
            return {}
        candidate = files[-1]

    try:
        with open(candidate, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}

    return payload if isinstance(payload, dict) else {}


def _load_evidence(client_id: str) -> list[dict[str, Any]]:
    evidence_dir = REGULATORY_DATA_DIR / client_id / "evidence"
    if not evidence_dir.exists():
        return []

    evidence: list[dict[str, Any]] = []
    for path in sorted(evidence_dir.glob("*.json"))[:20]:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            evidence.append(payload)
    return evidence


def _normalize_block(raw: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}
    return {
        "block_id": raw.get("block_id") or f"b{index + 1}",
        "block_type": raw.get("block_type") or raw.get("type") or "paragraph",
        "content": raw.get("content", raw.get("text", "")),
        "metadata": raw.get("metadata", {}),
    }


def _normalize_sections(
    raw_sections: list[dict[str, Any]],
    *,
    locale: str,
    fallback_sections: list[dict[str, Any]] | None = None,
) -> list[DraftSection]:
    normalized: list[DraftSection] = []
    fallback_sections = fallback_sections or []

    for index, raw in enumerate(raw_sections):
        fallback = fallback_sections[index] if index < len(fallback_sections) else {}
        blocks = [_normalize_block(block, block_index) for block_index, block in enumerate(raw.get("blocks", []))]
        normalized.append(
            DraftSection(
                section_id=raw.get("section_id") or fallback.get("section_id") or f"section_{index + 1}",
                heading=raw.get("heading") or fallback.get("heading") or f"Section {index + 1}",
                locale=raw.get("locale") or locale,
                blocks=blocks,
                facts=list(raw.get("facts", [])),
                citations=list(raw.get("citations", [])),
                translation_status=raw.get("translation_status"),
                approval_status=raw.get("approval_status") or "pending",
            )
        )

    if not normalized and fallback_sections:
        for index, fallback in enumerate(fallback_sections):
            normalized.append(
                DraftSection(
                    section_id=fallback.get("section_id", f"section_{index + 1}"),
                    heading=fallback.get("heading", f"Section {index + 1}"),
                    locale=locale,
                    blocks=[],
                    facts=[],
                    citations=[],
                    translation_status="original",
                    approval_status="pending",
                )
            )

    return normalized


def _next_revision_number(conn, draft_id: int) -> int:
    row = conn.execute(
        "SELECT MAX(revision_number) AS max_rev FROM draft_revisions WHERE draft_id=?",
        (draft_id,),
    ).fetchone()
    return (row["max_rev"] or 0) + 1


def _clear_approvals(conn, draft_id: int) -> None:
    conn.execute("DELETE FROM approval_states WHERE draft_id=?", (draft_id,))


def _insert_revision(
    conn,
    *,
    draft: Any,
    sections: list[DraftSection],
    authored_by: str,
    note: str | None,
    status: str = "composing",
    primary_locale: str | None = None,
) -> Any:
    next_rev = _next_revision_number(conn, draft["id"])
    cur = conn.execute(
        """INSERT INTO draft_revisions
           (draft_id, revision_number, sections_json, authored_by, note)
           VALUES (?, ?, ?, ?, ?)""",
        (draft["id"], next_rev, sections_to_json(sections), authored_by, note),
    )
    rev_id = cur.lastrowid
    if primary_locale:
        conn.execute(
            """UPDATE report_drafts
               SET current_revision_id=?, status=?, primary_locale=?,
                   updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
               WHERE id=?""",
            (rev_id, status, primary_locale, draft["id"]),
        )
    else:
        conn.execute(
            """UPDATE report_drafts
               SET current_revision_id=?, status=?,
                   updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
               WHERE id=?""",
            (rev_id, status, draft["id"]),
        )
    return conn.execute(
        "SELECT * FROM draft_revisions WHERE id=?",
        (rev_id,),
    ).fetchone()


def _update_section_approval_status(conn, draft: Any, section_id: str, status: str) -> None:
    if not draft["current_revision_id"]:
        return
    current = conn.execute(
        "SELECT * FROM draft_revisions WHERE id=?",
        (draft["current_revision_id"],),
    ).fetchone()
    if current is None:
        return
    sections = sections_from_json(current["sections_json"])
    updated = [
        section.model_copy(update={"approval_status": status})
        if section.section_id == section_id else section
        for section in sections
    ]
    conn.execute(
        """UPDATE draft_revisions
           SET sections_json=?
           WHERE id=?""",
        (sections_to_json(updated), current["id"]),
    )


def _roll_up_draft_status(conn, draft: Any) -> None:
    if not draft["current_revision_id"]:
        return
    current = conn.execute(
        "SELECT * FROM draft_revisions WHERE id=?",
        (draft["current_revision_id"],),
    ).fetchone()
    if current is None:
        return
    sections = sections_from_json(current["sections_json"])
    if not sections:
        return

    approvals = conn.execute(
        """SELECT section_id, status FROM approval_states
           WHERE draft_id=? AND revision_id=?""",
        (draft["id"], draft["current_revision_id"]),
    ).fetchall()
    approval_by_section = {row["section_id"]: row["status"] for row in approvals}
    statuses = [approval_by_section.get(section.section_id, "pending") for section in sections]

    new_status = None
    if statuses and all(status == "approved" for status in statuses):
        new_status = "approved"
    elif any(status in {"rejected", "needs_revision"} for status in statuses):
        new_status = "revision"
    elif any(status == "approved" for status in statuses):
        new_status = "approval"

    if new_status and new_status != draft["status"]:
        conn.execute(
            """UPDATE report_drafts
               SET status=?, updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
               WHERE id=?""",
            (new_status, draft["id"]),
        )


# ── Draft CRUD ─────────────────────────────────────────────────────────────────

@drafts_router.get("", response_model=List[DraftResponse], summary="List drafts")
def list_drafts(client_id: str = Depends(validate_client)) -> List[DraftResponse]:
    from db import get_db
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM report_drafts WHERE client_id=? ORDER BY id DESC",
            (client_id,),
        ).fetchall()
    return [_draft_row(r) for r in rows]


@drafts_router.post("", response_model=DraftResponse, status_code=201, summary="Create draft")
def create_draft(
    body: DraftCreate,
    client_id: str = Depends(validate_client),
) -> DraftResponse:
    from db import get_db
    with get_db() as conn:
        from api.routers.locales import _require_known_locale

        primary_locale = _require_known_locale(
            conn,
            body.primary_locale,
            field="primary_locale",
        )
        cur = conn.execute(
            """INSERT INTO report_drafts
               (client_id, title, template_version_id, period, primary_locale, created_by)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                client_id,
                body.title,
                body.template_version_id,
                body.period,
                primary_locale,
                body.created_by,
            ),
        )
        row = conn.execute(
            "SELECT * FROM report_drafts WHERE id=?", (cur.lastrowid,)
        ).fetchone()
    return _draft_row(row)


@drafts_router.get("/{draft_id}", response_model=DraftDetailResponse, summary="Get draft detail")
def get_draft(
    draft_id: int,
    client_id: str = Depends(validate_client),
) -> DraftDetailResponse:
    from db import get_db
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM report_drafts WHERE id=? AND client_id=?",
            (draft_id, client_id),
        ).fetchone()
        if row is None:
            raise HTTPException(404, f"Draft {draft_id} not found")

        current_revision: Optional[RevisionDetailResponse] = None
        if row["current_revision_id"]:
            rev = conn.execute(
                "SELECT * FROM draft_revisions WHERE id=?",
                (row["current_revision_id"],),
            ).fetchone()
            if rev:
                current_revision = _revision_detail_row(rev)

    base = _draft_row(row)
    return DraftDetailResponse(
        **base.model_dump(),
        current_revision=current_revision,
    )


@drafts_router.delete("/{draft_id}", summary="Archive draft")
def archive_draft(
    draft_id: int,
    client_id: str = Depends(validate_client),
) -> dict:
    from db import get_db
    with get_db() as conn:
        row = conn.execute(
            "SELECT status FROM report_drafts WHERE id=? AND client_id=?",
            (draft_id, client_id),
        ).fetchone()
        if row is None:
            raise HTTPException(404, f"Draft {draft_id} not found")
        conn.execute(
            """UPDATE report_drafts
               SET status='archived', updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
               WHERE id=?""",
            (draft_id,),
        )
    return {"archived": draft_id}


# ── Draft status transitions ───────────────────────────────────────────────────

@drafts_router.post("/{draft_id}/transition", response_model=DraftResponse, summary="Transition draft status")
def transition_draft(
    draft_id: int,
    target_status: str,
    client_id: str = Depends(validate_client),
) -> DraftResponse:
    from db import get_db
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM report_drafts WHERE id=? AND client_id=?",
            (draft_id, client_id),
        ).fetchone()
        if row is None:
            raise HTTPException(404, f"Draft {draft_id} not found")

        if not validate_transition(row["status"], target_status):
            raise HTTPException(
                422,
                f"Invalid transition: {row['status']} → {target_status}",
            )

        if target_status == "approved":
            if row["current_revision_id"] is None:
                raise HTTPException(422, "Draft has no current revision to approve")

            current = conn.execute(
                "SELECT * FROM draft_revisions WHERE id=?",
                (row["current_revision_id"],),
            ).fetchone()
            sections = sections_from_json(current["sections_json"]) if current else []
            if not sections:
                raise HTTPException(422, "Current revision has no sections to approve")

            approvals = conn.execute(
                """SELECT section_id, status FROM approval_states
                   WHERE draft_id=? AND revision_id=?""",
                (draft_id, row["current_revision_id"]),
            ).fetchall()
            approval_by_section = {approval["section_id"]: approval["status"] for approval in approvals}
            if any(approval_by_section.get(section.section_id) != "approved" for section in sections):
                raise HTTPException(
                    422,
                    "All sections must be approved before finalizing the draft.",
                )

        conn.execute(
            """UPDATE report_drafts
               SET status=?, updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
               WHERE id=?""",
            (target_status, draft_id),
        )
        updated = conn.execute(
            "SELECT * FROM report_drafts WHERE id=?", (draft_id,)
        ).fetchone()
    return _draft_row(updated)


# ── Revisions ──────────────────────────────────────────────────────────────────

@drafts_router.get("/{draft_id}/revisions", response_model=List[RevisionResponse], summary="List revisions")
def list_revisions(
    draft_id: int,
    client_id: str = Depends(validate_client),
) -> List[RevisionResponse]:
    from db import get_db
    with get_db() as conn:
        exists = conn.execute(
            "SELECT id FROM report_drafts WHERE id=? AND client_id=?",
            (draft_id, client_id),
        ).fetchone()
        if exists is None:
            raise HTTPException(404, f"Draft {draft_id} not found")
        rows = conn.execute(
            "SELECT * FROM draft_revisions WHERE draft_id=? ORDER BY revision_number",
            (draft_id,),
        ).fetchall()
    return [_revision_row(r) for r in rows]


@drafts_router.get(
    "/{draft_id}/revisions/{revision_id}",
    response_model=RevisionDetailResponse,
    summary="Get revision detail",
)
def get_revision(
    draft_id: int,
    revision_id: int,
    client_id: str = Depends(validate_client),
) -> RevisionDetailResponse:
    from db import get_db
    with get_db() as conn:
        exists = conn.execute(
            "SELECT id FROM report_drafts WHERE id=? AND client_id=?",
            (draft_id, client_id),
        ).fetchone()
        if exists is None:
            raise HTTPException(404, f"Draft {draft_id} not found")
        row = conn.execute(
            "SELECT * FROM draft_revisions WHERE id=? AND draft_id=?",
            (revision_id, draft_id),
        ).fetchone()
    if row is None:
        raise HTTPException(404, f"Revision {revision_id} not found")
    return _revision_detail_row(row)


class ComposeJobAccepted(BaseModel):
    """Response body for an accepted compose request."""

    job_id: str
    status: str = "pending"


class ComposeJobStatus(BaseModel):
    """Poll response for a compose job."""

    job_id: str
    status: str  # "pending" | "running" | "done" | "failed"
    error: Optional[str] = None
    revision: Optional[RevisionDetailResponse] = None


class ChatJobAccepted(BaseModel):
    """Response body when a chat-with-section call is accepted for async processing."""

    job_id: str
    status: str = "pending"


class ChatJobStatus(BaseModel):
    """Poll response for a chat job."""

    job_id: str
    status: str  # "pending" | "running" | "done" | "failed"
    error: Optional[str] = None
    message: Optional[ChatMessageResponse] = None


class TranslateJobAccepted(BaseModel):
    """Response body when a translate request is accepted for async processing."""

    job_id: str
    status: str = "pending"


class TranslateJobStatus(BaseModel):
    """Poll response for a translate job."""

    job_id: str
    status: str  # "pending" | "running" | "done" | "failed"
    error: Optional[str] = None
    revision: Optional[RevisionDetailResponse] = None


@drafts_router.post(
    "/{draft_id}/compose",
    response_model=ComposeJobAccepted,
    status_code=202,
    summary="Kick off a compose job; poll /compose/{job_id} for the revision",
)
def compose_draft(
    draft_id: int,
    background_tasks: BackgroundTasks,
    client_id: str = Depends(validate_client),
    note: Optional[str] = None,
) -> ComposeJobAccepted:
    """
    Accept a compose request and run the agent asynchronously.

    Compose can take 15–30s, which exceeds Render's proxy timeout. We validate
    the draft exists, register a job in the in-memory registry, and schedule
    the LLM call as a FastAPI BackgroundTask. The client polls
    `GET /compose/{job_id}` until `status == "done"` (or `"failed"`).
    """
    from db import get_db

    with get_db() as conn:
        draft = conn.execute(
            "SELECT id FROM report_drafts WHERE id=? AND client_id=?",
            (draft_id, client_id),
        ).fetchone()
        if draft is None:
            raise HTTPException(404, f"Draft {draft_id} not found")

    job_id = str(uuid.uuid4())
    _register_compose_job(job_id, draft_id=draft_id, client_id=client_id)
    background_tasks.add_task(_run_compose_job, job_id, draft_id, client_id, note)
    return ComposeJobAccepted(job_id=job_id, status="pending")


@drafts_router.get(
    "/{draft_id}/compose/{job_id}",
    response_model=ComposeJobStatus,
    summary="Poll the status of a compose job",
)
def get_compose_job(
    draft_id: int,
    job_id: str,
    client_id: str = Depends(validate_client),
) -> ComposeJobStatus:
    """Return the current status of a compose job."""
    entry = _get_compose_job(job_id)
    if entry is None:
        raise HTTPException(404, f"Compose job {job_id} not found or expired")
    if entry["client_id"] != client_id or entry["draft_id"] != draft_id:
        # Don't leak job existence across clients/drafts.
        raise HTTPException(404, f"Compose job {job_id} not found")
    revision = None
    if entry["revision"] is not None:
        revision = RevisionDetailResponse.model_validate(entry["revision"])
    return ComposeJobStatus(
        job_id=entry["job_id"],
        status=entry["status"],
        error=entry["error"],
        revision=revision,
    )


@drafts_router.post(
    "/{draft_id}/translate",
    response_model=TranslateJobAccepted,
    status_code=202,
    responses={202: {"model": TranslateJobAccepted}},
    summary="Kick off a translate job; poll /translate/{job_id} for the revision",
)
def translate_draft(
    draft_id: int,
    target_locale: str,
    background_tasks: BackgroundTasks,
    client_id: str = Depends(validate_client),
) -> TranslateJobAccepted:
    """
    Accept a translation request and run the agent asynchronously.

    Translate can take 15–30s which exceeds Render's proxy timeout. Validate
    the draft + normalize the locale at the API boundary (so aliases like
    "no"/"nor"/"no-NO" resolve to canonical codes), register a job, and
    schedule the LLM call as a FastAPI BackgroundTask. The client polls
    `GET /translate/{job_id}` until `status == "done"` (or `"failed"`).
    """
    from db import get_db

    with get_db() as conn:
        draft = conn.execute(
            "SELECT * FROM report_drafts WHERE id=? AND client_id=?",
            (draft_id, client_id),
        ).fetchone()
        if draft is None:
            raise HTTPException(404, f"Draft {draft_id} not found")
        if draft["current_revision_id"] is None:
            raise HTTPException(422, "Draft has no current revision to translate")

        # Normalize at the API boundary so aliases like "no"/"nor"/"no-NO"
        # resolve to canonical codes (e.g. "nb") before hitting the DB check.
        normalized_locale = _normalize_locale(target_locale)
        locale_row = conn.execute(
            "SELECT code FROM locales WHERE code=? AND is_active=1",
            (normalized_locale,),
        ).fetchone()
        if locale_row is None:
            raise HTTPException(
                422,
                f"Unknown locale: {target_locale!r} (normalized to {normalized_locale!r})",
            )
        target_locale = normalized_locale

    job_id = str(uuid.uuid4())
    _register_translate_job(job_id, draft_id=draft_id, client_id=client_id)
    background_tasks.add_task(_run_translate_job, job_id, draft_id, client_id, target_locale)
    return TranslateJobAccepted(job_id=job_id, status="pending")


@drafts_router.get(
    "/{draft_id}/translate/{job_id}",
    response_model=TranslateJobStatus,
    summary="Poll the status of a translate job",
)
def get_translate_job(
    draft_id: int,
    job_id: str,
    client_id: str = Depends(validate_client),
) -> TranslateJobStatus:
    """Return the current status of a translate job."""
    entry = _get_translate_job(job_id)
    if entry is None:
        raise HTTPException(404, f"Translate job {job_id} not found or expired")
    if entry["client_id"] != client_id or entry["draft_id"] != draft_id:
        # Don't leak job existence across clients/drafts.
        raise HTTPException(404, f"Translate job {job_id} not found")
    revision = None
    if entry["revision"] is not None:
        revision = RevisionDetailResponse.model_validate(entry["revision"])
    return TranslateJobStatus(
        job_id=entry["job_id"],
        status=entry["status"],
        error=entry["error"],
        revision=revision,
    )


@drafts_router.put(
    "/{draft_id}/sections/{section_id}",
    response_model=DraftSection,
    summary="Update a section and create a new revision",
)
def update_section(
    draft_id: int,
    section_id: str,
    body: SectionEditRequest,
    client_id: str = Depends(validate_client),
) -> DraftSection:
    from db import get_db

    with get_db() as conn:
        draft = conn.execute(
            "SELECT * FROM report_drafts WHERE id=? AND client_id=?",
            (draft_id, client_id),
        ).fetchone()
        if draft is None:
            raise HTTPException(404, f"Draft {draft_id} not found")
        if draft["current_revision_id"] is None:
            raise HTTPException(422, "Draft has no current revision to edit")

        revision = conn.execute(
            "SELECT * FROM draft_revisions WHERE id=?",
            (draft["current_revision_id"],),
        ).fetchone()
        sections = sections_from_json(revision["sections_json"])

        target = next((section for section in sections if section.section_id == section_id), None)
        if target is None:
            raise HTTPException(404, f"Section {section_id} not found")

        updated_blocks = (
            [SectionBlock(**_normalize_block(block.model_dump(), index)) for index, block in enumerate(body.blocks)]
            if body.blocks is not None else target.blocks
        )
        updated_section = target.model_copy(
            update={
                "blocks": updated_blocks,
                "facts": body.facts if body.facts is not None else target.facts,
                "citations": body.citations if body.citations is not None else target.citations,
                "approval_status": "pending",
            }
        )
        updated_sections = [
            updated_section if section.section_id == section_id else section
            for section in sections
        ]

        _clear_approvals(conn, draft_id)
        _insert_revision(
            conn,
            draft=draft,
            sections=updated_sections,
            authored_by="editor",
            note=body.revision_note or f"Edited section {section_id}",
            status="composing",
        )

    return updated_section


# ── Chat ───────────────────────────────────────────────────────────────────────

@drafts_router.get(
    "/{draft_id}/chat",
    response_model=List[ChatMessageResponse],
    summary="List chat messages",
)
def list_chat(
    draft_id: int,
    client_id: str = Depends(validate_client),
    section_id: Optional[str] = None,
) -> List[ChatMessageResponse]:
    from db import get_db
    with get_db() as conn:
        exists = conn.execute(
            "SELECT id FROM report_drafts WHERE id=? AND client_id=?",
            (draft_id, client_id),
        ).fetchone()
        if exists is None:
            raise HTTPException(404, f"Draft {draft_id} not found")

        if section_id:
            rows = conn.execute(
                """SELECT * FROM draft_chat_messages
                   WHERE draft_id=? AND section_id=? ORDER BY id""",
                (draft_id, section_id),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM draft_chat_messages WHERE draft_id=? ORDER BY id",
                (draft_id,),
            ).fetchall()

    return [
        ChatMessageResponse(
            id=r["id"],
            draft_id=r["draft_id"],
            section_id=r["section_id"],
            role=r["role"],
            content=r["content"],
            revision_id=r["revision_id"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@drafts_router.post(
    "/{draft_id}/chat",
    status_code=202,
    responses={
        201: {"model": ChatMessageResponse},
        202: {"model": ChatJobAccepted},
    },
    summary="Send chat message (section-scoped calls return 202 + poll URL)",
)
def send_chat(
    draft_id: int,
    body: ChatMessageCreate,
    response: Response,
    background_tasks: BackgroundTasks,
    client_id: str = Depends(validate_client),
) -> ChatMessageResponse | ChatJobAccepted:
    """
    Send a chat message. No-section messages reply synchronously with a canned
    response. Section-scoped messages invoke the LLM, which can take 15–30s and
    exceeds Render's proxy timeout — we accept the request (Tx1 persists the
    user message), schedule the LLM call + revision write as a background task,
    and return 202 with a job id for the client to poll.
    """
    from db import get_db

    # Tx 1: always persist the user message. This preserves audit even when the
    # downstream LLM call later fails or times out in the background worker.
    with get_db() as conn:
        draft = conn.execute(
            "SELECT * FROM report_drafts WHERE id=? AND client_id=?",
            (draft_id, client_id),
        ).fetchone()
        if draft is None:
            raise HTTPException(404, f"Draft {draft_id} not found")
        if draft["current_revision_id"] is None:
            raise HTTPException(422, "Draft has no current revision to edit")

        conn.execute(
            """INSERT INTO draft_chat_messages
               (draft_id, section_id, role, content, revision_id)
               VALUES (?, ?, ?, ?, ?)""",
            (
                draft_id,
                body.section_id,
                body.role,
                body.content,
                draft["current_revision_id"],
            ),
        )

    target_section_id = body.section_id
    current_revision_id = draft["current_revision_id"]

    # No section context — short-circuit with a canned reply (no LLM, stays 201 sync).
    if target_section_id is None:
        with get_db() as conn:
            assistant_insert = conn.execute(
                """INSERT INTO draft_chat_messages
                   (draft_id, section_id, role, content, revision_id)
                   VALUES (?, NULL, 'assistant', ?, ?)""",
                (
                    draft_id,
                    "I can help refine the draft. Select a section for targeted edits.",
                    current_revision_id,
                ),
            )
            row = conn.execute(
                "SELECT * FROM draft_chat_messages WHERE id=?",
                (assistant_insert.lastrowid,),
            ).fetchone()
        response.status_code = 201
        return ChatMessageResponse(
            id=row["id"],
            draft_id=row["draft_id"],
            section_id=row["section_id"],
            role=row["role"],
            content=row["content"],
            revision_id=row["revision_id"],
            created_at=row["created_at"],
        )

    # Section-scoped chat — kick the LLM + revision write off as a background job.
    job_id = str(uuid.uuid4())
    _register_chat_job(job_id, draft_id=draft_id, client_id=client_id)
    background_tasks.add_task(
        _run_chat_job,
        job_id,
        draft_id,
        client_id,
        target_section_id,
        body.content,
    )
    response.status_code = 202
    return ChatJobAccepted(job_id=job_id, status="pending")


@drafts_router.get(
    "/{draft_id}/chat/{job_id}",
    response_model=ChatJobStatus,
    summary="Poll the status of a chat job",
)
def get_chat_job(
    draft_id: int,
    job_id: str,
    client_id: str = Depends(validate_client),
) -> ChatJobStatus:
    """Return the current status of a section-scoped chat job."""
    entry = _get_chat_job(job_id)
    if entry is None:
        raise HTTPException(404, f"Chat job {job_id} not found or expired")
    if entry["client_id"] != client_id or entry["draft_id"] != draft_id:
        # Don't leak job existence across clients/drafts.
        raise HTTPException(404, f"Chat job {job_id} not found")
    message = None
    if entry["message"] is not None:
        message = ChatMessageResponse.model_validate(entry["message"])
    return ChatJobStatus(
        job_id=entry["job_id"],
        status=entry["status"],
        error=entry["error"],
        message=message,
    )


# ── Approval ───────────────────────────────────────────────────────────────────

@drafts_router.get(
    "/{draft_id}/approvals",
    response_model=List[ApprovalStateResponse],
    summary="List approval states",
)
def list_approvals(
    draft_id: int,
    client_id: str = Depends(validate_client),
) -> List[ApprovalStateResponse]:
    from db import get_db
    with get_db() as conn:
        exists = conn.execute(
            "SELECT id FROM report_drafts WHERE id=? AND client_id=?",
            (draft_id, client_id),
        ).fetchone()
        if exists is None:
            raise HTTPException(404, f"Draft {draft_id} not found")
        rows = conn.execute(
            "SELECT * FROM approval_states WHERE draft_id=? ORDER BY section_id",
            (draft_id,),
        ).fetchall()
    return [
        ApprovalStateResponse(
            id=r["id"],
            draft_id=r["draft_id"],
            section_id=r["section_id"],
            status=r["status"],
            reviewer=r["reviewer"],
            comment=r["comment"],
            revision_id=r["revision_id"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )
        for r in rows
    ]


@drafts_router.post(
    "/{draft_id}/approve",
    response_model=ApprovalStateResponse,
    summary="Approve or reject a section",
)
def approve_section(
    draft_id: int,
    body: ApprovalAction,
    client_id: str = Depends(validate_client),
) -> ApprovalStateResponse:
    from db import get_db
    with get_db() as conn:
        draft = conn.execute(
            "SELECT * FROM report_drafts WHERE id=? AND client_id=?",
            (draft_id, client_id),
        ).fetchone()
        if draft is None:
            raise HTTPException(404, f"Draft {draft_id} not found")

        # Validate section exists in current revision
        revision = conn.execute(
            "SELECT sections_json FROM draft_revisions WHERE id=?",
            (draft["current_revision_id"],),
        ).fetchone()
        if revision:
            current_sections = json.loads(revision["sections_json"])
            valid_ids = {s.get("section_id") for s in current_sections}
            if body.section_id not in valid_ids:
                raise HTTPException(404, f"Section '{body.section_id}' not found in current revision")

        existing = conn.execute(
            "SELECT id FROM approval_states WHERE draft_id=? AND section_id=?",
            (draft_id, body.section_id),
        ).fetchone()

        if existing:
            conn.execute(
                """UPDATE approval_states
                   SET status=?, reviewer=?, comment=?, revision_id=?,
                       updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                   WHERE draft_id=? AND section_id=?""",
                (
                    body.status,
                    body.reviewer,
                    body.comment,
                    draft["current_revision_id"],
                    draft_id,
                    body.section_id,
                ),
            )
        else:
            conn.execute(
                """INSERT INTO approval_states
                   (draft_id, section_id, status, reviewer, comment, revision_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    draft_id,
                    body.section_id,
                    body.status,
                    body.reviewer,
                    body.comment,
                    draft["current_revision_id"],
                ),
            )

        row = conn.execute(
            "SELECT * FROM approval_states WHERE draft_id=? AND section_id=?",
            (draft_id, body.section_id),
        ).fetchone()
        _update_section_approval_status(conn, draft, body.section_id, body.status)
        refreshed_draft = conn.execute(
            "SELECT * FROM report_drafts WHERE id=?",
            (draft_id,),
        ).fetchone()
        _roll_up_draft_status(conn, refreshed_draft)

    return ApprovalStateResponse(
        id=row["id"],
        draft_id=row["draft_id"],
        section_id=row["section_id"],
        status=row["status"],
        reviewer=row["reviewer"],
        comment=row["comment"],
        revision_id=row["revision_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
