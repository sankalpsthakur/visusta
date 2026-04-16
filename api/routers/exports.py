"""
Exports router — POST pdf/docx, GET download, POST import-docx.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse

from api.deps import OUTPUT_DIR, validate_client
from api.schemas_mars import DocxImportResponse, ExportJobResponse, ExportRequest
from mars.docx_export import export_sections_to_docx
from mars.pdf_export import export_sections_to_pdf
from mars.section_model import sections_from_json

exports_router = APIRouter(
    prefix="/api/clients/{client_id}/drafts/{draft_id}/exports",
    tags=["exports"],
)


def _job_row(row) -> ExportJobResponse:
    return ExportJobResponse(
        id=row["id"],
        draft_id=row["draft_id"],
        revision_id=row["revision_id"],
        format=row["format"],
        locale=row["locale"],
        status=row["status"],
        output_path=row["output_path"],
        error=row["error"],
        requested_by=row["requested_by"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _assert_draft(conn, draft_id: int, client_id: str) -> None:
    row = conn.execute(
        "SELECT id FROM report_drafts WHERE id=? AND client_id=?",
        (draft_id, client_id),
    ).fetchone()
    if row is None:
        raise HTTPException(404, f"Draft {draft_id} not found")


def _export_path(client_id: str, draft_id: int, job_id: int, fmt: str) -> Path:
    suffix = ".pdf" if fmt == "pdf" else ".docx"
    return OUTPUT_DIR / client_id / "mars" / str(draft_id) / f"export_{job_id}{suffix}"


def _process_export_job(job_id: int) -> None:
    from db import get_db
    with get_db() as conn:
        row = conn.execute("SELECT * FROM export_jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            return

        draft = conn.execute(
            "SELECT * FROM report_drafts WHERE id=?",
            (row["draft_id"],),
        ).fetchone()
        revision = conn.execute(
            "SELECT * FROM draft_revisions WHERE id=?",
            (row["revision_id"],),
        ).fetchone() if row["revision_id"] is not None else None

        if draft is None or revision is None:
            conn.execute(
                """UPDATE export_jobs
                   SET status='failed', error=?, updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                   WHERE id=?""",
                ("Missing draft or revision", job_id),
            )
            return

        conn.execute(
            """UPDATE export_jobs
               SET status='processing', updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
               WHERE id=?""",
            (job_id,),
        )

    sections = sections_from_json(revision["sections_json"])
    output_path = _export_path(draft["client_id"], draft["id"], job_id, row["format"])

    from config import load_client_registry

    registry = load_client_registry()
    client_config = registry.get(draft["client_id"], {})
    client_branding = dict(client_config.get("branding") or {})
    if client_config.get("display_name"):
        client_branding["company_name"] = client_config.get("display_name")

    try:
        if row["format"] == "pdf":
            export_sections_to_pdf(
                sections,
                output_path,
                locale=row["locale"] or draft["primary_locale"],
                client_branding=client_branding or None,
            )
        else:
            export_sections_to_docx(
                sections,
                output_path,
                locale=row["locale"] or draft["primary_locale"],
                client_branding=client_branding or None,
            )
    except Exception as exc:  # pragma: no cover - defensive
        with get_db() as conn:
            conn.execute(
                """UPDATE export_jobs
                   SET status='failed', error=?, updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                   WHERE id=?""",
                (str(exc), job_id),
            )
        return

    with get_db() as conn:
        conn.execute(
            """UPDATE export_jobs
               SET status='completed', output_path=?, updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
               WHERE id=?""",
            (str(output_path), job_id),
        )
        if row["format"] == "pdf":
            conn.execute(
                """UPDATE report_drafts
                   SET status='exported', updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                   WHERE id=?""",
                (draft["id"],),
            )


@exports_router.get("", response_model=List[ExportJobResponse], summary="List export jobs")
def list_exports(
    draft_id: int,
    client_id: str = Depends(validate_client),
) -> List[ExportJobResponse]:
    from db import get_db
    with get_db() as conn:
        _assert_draft(conn, draft_id, client_id)
        rows = conn.execute(
            "SELECT * FROM export_jobs WHERE draft_id=? ORDER BY id DESC",
            (draft_id,),
        ).fetchall()
    return [_job_row(r) for r in rows]


@exports_router.post("", response_model=ExportJobResponse, status_code=201, summary="Request export")
def request_export(
    draft_id: int,
    body: ExportRequest,
    response: Response,
    client_id: str = Depends(validate_client),
) -> ExportJobResponse:
    """
    DOCX and PDF exports both complete within the request lifecycle.
    """
    from db import get_db
    with get_db() as conn:
        draft = conn.execute(
            "SELECT * FROM report_drafts WHERE id=? AND client_id=?",
            (draft_id, client_id),
        ).fetchone()
        if draft is None:
            raise HTTPException(404, f"Draft {draft_id} not found")

        # Approval gating: PDF export only on approved drafts
        if body.format == "pdf" and draft["status"] not in ("approved", "exported"):
            raise HTTPException(
                403,
                "PDF export requires the draft to be in 'approved' status. "
                f"Current status: {draft['status']}",
            )

        revision_id = body.revision_id or draft["current_revision_id"]
        if revision_id is None:
            raise HTTPException(422, "Draft has no revision to export")

        revision = conn.execute(
            "SELECT * FROM draft_revisions WHERE id=? AND draft_id=?",
            (revision_id, draft_id),
        ).fetchone()
        if revision is None:
            raise HTTPException(422, "Revision does not belong to this draft")

        sections = sections_from_json(revision["sections_json"])
        resolved_locale = body.locale or (sections[0].locale if sections else draft["primary_locale"])

        cur = conn.execute(
            """INSERT INTO export_jobs
               (draft_id, revision_id, format, locale, status, requested_by)
               VALUES (?, ?, ?, ?, 'pending', ?)""",
            (draft_id, revision_id, body.format, resolved_locale, body.requested_by),
        )
        row = conn.execute(
            "SELECT * FROM export_jobs WHERE id=?", (cur.lastrowid,)
        ).fetchone()

    _process_export_job(row["id"])
    response.status_code = 201
    from db import get_db
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM export_jobs WHERE id=?",
            (row["id"],),
        ).fetchone()

    return _job_row(row)


@exports_router.get("/{job_id}", response_model=ExportJobResponse, summary="Get export job status")
def get_export_job(
    draft_id: int,
    job_id: int,
    client_id: str = Depends(validate_client),
) -> ExportJobResponse:
    from db import get_db
    with get_db() as conn:
        _assert_draft(conn, draft_id, client_id)
        row = conn.execute(
            "SELECT * FROM export_jobs WHERE id=? AND draft_id=?",
            (job_id, draft_id),
        ).fetchone()
    if row is None:
        raise HTTPException(404, f"Export job {job_id} not found")
    return _job_row(row)


@exports_router.get("/{job_id}/download", summary="Download exported file")
def download_export(
    draft_id: int,
    job_id: int,
    client_id: str = Depends(validate_client),
) -> FileResponse:
    from db import get_db
    with get_db() as conn:
        _assert_draft(conn, draft_id, client_id)
        row = conn.execute(
            "SELECT * FROM export_jobs WHERE id=? AND draft_id=?",
            (job_id, draft_id),
        ).fetchone()
    if row is None:
        raise HTTPException(404, f"Export job {job_id} not found")
    if row["status"] != "completed" or not row["output_path"]:
        raise HTTPException(404, "Export file not yet available")

    path = Path(row["output_path"])
    if not path.exists():
        raise HTTPException(404, "Export file missing from disk")

    media_type = "application/pdf" if row["format"] == "pdf" else (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    return FileResponse(path=str(path), media_type=media_type, filename=path.name)


@exports_router.post(
    "/import-docx",
    response_model=DocxImportResponse,
    status_code=201,
    summary="Import DOCX as new revision",
)
async def import_docx(
    draft_id: int,
    client_id: str = Depends(validate_client),
    file: UploadFile = File(...),
) -> DocxImportResponse:
    """
    Accept an uploaded DOCX file and parse it into a new draft revision (stub).
    Full parsing logic implemented in Phase 4 via mars/docx_import.py.
    """
    from db import get_db
    from mars.docx_import import parse_docx_to_sections
    from mars.section_model import sections_to_json

    content = await file.read()

    with get_db() as conn:
        draft = conn.execute(
            "SELECT * FROM report_drafts WHERE id=? AND client_id=?",
            (draft_id, client_id),
        ).fetchone()
        if draft is None:
            raise HTTPException(404, f"Draft {draft_id} not found")

        sections, warnings = parse_docx_to_sections(content, draft["primary_locale"])
        if not sections:
            detail = warnings[0] if warnings else "No sections could be parsed from the DOCX upload."
            raise HTTPException(422, detail)

        last_rev = conn.execute(
            "SELECT MAX(revision_number) AS max_rev FROM draft_revisions WHERE draft_id=?",
            (draft_id,),
        ).fetchone()
        next_rev = (last_rev["max_rev"] or 0) + 1

        cur = conn.execute(
            """INSERT INTO draft_revisions
               (draft_id, revision_number, sections_json, authored_by, note)
               VALUES (?, ?, ?, ?, ?)""",
            (
                draft_id,
                next_rev,
                sections_to_json(sections),
                "docx-import",
                f"Imported from {file.filename}",
            ),
        )
        rev_id = cur.lastrowid

        conn.execute("DELETE FROM approval_states WHERE draft_id=?", (draft_id,))

        conn.execute(
            """UPDATE report_drafts
               SET status='revision', updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
               WHERE id=? AND status IN ('approved', 'exported')""",
            (draft_id,),
        )

        conn.execute(
            """UPDATE report_drafts
               SET current_revision_id=?, updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
               WHERE id=?""",
            (rev_id, draft_id),
        )

    return DocxImportResponse(
        draft_id=draft_id,
        revision_id=rev_id,
        sections_imported=len(sections),
        warnings=warnings,
    )
