"""
Templates router — CRUD, versions, clone, client overrides.
"""

from __future__ import annotations

import json
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException

from api.deps import validate_client
from api.schemas_mars import (
    TemplateCloneRequest,
    TemplateCreate,
    TemplateResponse,
    TemplateSectionsUpdate,
    TemplateThemeUpdate,
    TemplateVersionCreate,
    TemplateVersionResponse,
)

templates_router = APIRouter(prefix="/api/templates", tags=["templates"])


def _template_row(row: Any) -> TemplateResponse:
    return TemplateResponse(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        industry_profile_id=row["industry_profile_id"],
        base_locale=row["base_locale"],
        current_version=row["current_version"],
        is_published=bool(row["is_published"]),
        created_by=row["created_by"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _version_row(row: Any) -> TemplateVersionResponse:
    return TemplateVersionResponse(
        id=row["id"],
        template_id=row["template_id"],
        version_number=row["version_number"],
        sections_json=json.loads(row["sections_json"]),
        theme_tokens=json.loads(row["theme_tokens"]),
        changelog_note=row["changelog_note"],
        created_by=row["created_by"],
        created_at=row["created_at"],
    )


def _latest_version_row(conn, template_id: int):
    return conn.execute(
        """SELECT * FROM template_versions
           WHERE template_id=?
           ORDER BY version_number DESC
           LIMIT 1""",
        (template_id,),
    ).fetchone()


# ── Template CRUD ─────────────────────────────────────────────────────────────

@templates_router.get("", response_model=List[TemplateResponse], summary="List templates")
def list_templates() -> List[TemplateResponse]:
    from db import get_db
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM report_templates ORDER BY id").fetchall()
    return [_template_row(r) for r in rows]


@templates_router.post("", response_model=TemplateResponse, status_code=201, summary="Create template")
def create_template(body: TemplateCreate) -> TemplateResponse:
    from db import get_db
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO report_templates
               (name, description, industry_profile_id, base_locale, current_version)
               VALUES (?, ?, ?, ?, 0)""",
            (body.name, body.description, body.industry_profile_id, body.base_locale),
        )
        row = conn.execute(
            "SELECT * FROM report_templates WHERE id=?", (cur.lastrowid,)
        ).fetchone()
    return _template_row(row)


@templates_router.get("/{template_id}", response_model=TemplateResponse, summary="Get template")
def get_template(template_id: int) -> TemplateResponse:
    from db import get_db
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM report_templates WHERE id=?", (template_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(404, f"Template {template_id} not found")
    return _template_row(row)


@templates_router.put("/{template_id}", response_model=TemplateResponse, summary="Update template")
def update_template(template_id: int, body: TemplateCreate) -> TemplateResponse:
    from db import get_db
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM report_templates WHERE id=?", (template_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(404, f"Template {template_id} not found")
        conn.execute(
            """UPDATE report_templates
               SET name=?, description=?, industry_profile_id=?, base_locale=?,
                   updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
               WHERE id=?""",
            (body.name, body.description, body.industry_profile_id, body.base_locale, template_id),
        )
        row = conn.execute(
            "SELECT * FROM report_templates WHERE id=?", (template_id,)
        ).fetchone()
    return _template_row(row)


@templates_router.delete("/{template_id}", summary="Delete template")
def delete_template(template_id: int) -> dict:
    from db import get_db
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM report_templates WHERE id=?", (template_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(404, f"Template {template_id} not found")
        conn.execute("DELETE FROM report_templates WHERE id=?", (template_id,))
    return {"deleted": template_id}


# ── Template versions ─────────────────────────────────────────────────────────

@templates_router.get(
    "/{template_id}/versions",
    response_model=List[TemplateVersionResponse],
    summary="List template versions",
)
def list_versions(template_id: int) -> List[TemplateVersionResponse]:
    from db import get_db
    with get_db() as conn:
        tmpl = conn.execute(
            "SELECT id FROM report_templates WHERE id=?", (template_id,)
        ).fetchone()
        if tmpl is None:
            raise HTTPException(404, f"Template {template_id} not found")
        rows = conn.execute(
            "SELECT * FROM template_versions WHERE template_id=? ORDER BY version_number",
            (template_id,),
        ).fetchall()
    return [_version_row(r) for r in rows]


@templates_router.post(
    "/{template_id}/versions",
    response_model=TemplateVersionResponse,
    status_code=201,
    summary="Create new template version",
)
def create_version(template_id: int, body: TemplateVersionCreate) -> TemplateVersionResponse:
    from db import get_db
    with get_db() as conn:
        tmpl = conn.execute(
            "SELECT * FROM report_templates WHERE id=?", (template_id,)
        ).fetchone()
        if tmpl is None:
            raise HTTPException(404, f"Template {template_id} not found")

        new_version = tmpl["current_version"] + 1
        cur = conn.execute(
            """INSERT INTO template_versions
               (template_id, version_number, sections_json, theme_tokens, changelog_note, created_by)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                template_id,
                new_version,
                json.dumps(body.sections_json),
                json.dumps(body.theme_tokens),
                body.changelog_note,
                body.created_by,
            ),
        )
        conn.execute(
            """UPDATE report_templates
               SET current_version=?, updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
               WHERE id=?""",
            (new_version, template_id),
        )
        row = conn.execute(
            "SELECT * FROM template_versions WHERE id=?", (cur.lastrowid,)
        ).fetchone()
    return _version_row(row)


@templates_router.put(
    "/{template_id}/sections",
    response_model=TemplateVersionResponse,
    summary="Create a new template version from updated sections",
)
def update_sections(template_id: int, body: TemplateSectionsUpdate) -> TemplateVersionResponse:
    from db import get_db

    with get_db() as conn:
        tmpl = conn.execute(
            "SELECT * FROM report_templates WHERE id=?",
            (template_id,),
        ).fetchone()
        if tmpl is None:
            raise HTTPException(404, f"Template {template_id} not found")

        latest_ver = _latest_version_row(conn, template_id)
        theme_tokens = json.loads(latest_ver["theme_tokens"]) if latest_ver else {}
        new_version = tmpl["current_version"] + 1
        cur = conn.execute(
            """INSERT INTO template_versions
               (template_id, version_number, sections_json, theme_tokens, changelog_note, created_by)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                template_id,
                new_version,
                json.dumps([section.model_dump() for section in body.sections]),
                json.dumps(theme_tokens),
                body.changelog,
                body.created_by,
            ),
        )
        conn.execute(
            """UPDATE report_templates
               SET current_version=?, updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
               WHERE id=?""",
            (new_version, template_id),
        )
        row = conn.execute(
            "SELECT * FROM template_versions WHERE id=?",
            (cur.lastrowid,),
        ).fetchone()

    return _version_row(row)


@templates_router.put(
    "/{template_id}/theme",
    response_model=TemplateResponse,
    summary="Create a new template version from updated theme tokens",
)
def update_theme(template_id: int, body: TemplateThemeUpdate) -> TemplateResponse:
    from db import get_db

    with get_db() as conn:
        tmpl = conn.execute(
            "SELECT * FROM report_templates WHERE id=?",
            (template_id,),
        ).fetchone()
        if tmpl is None:
            raise HTTPException(404, f"Template {template_id} not found")

        latest_ver = _latest_version_row(conn, template_id)
        sections_json = latest_ver["sections_json"] if latest_ver else "[]"
        new_version = tmpl["current_version"] + 1
        conn.execute(
            """INSERT INTO template_versions
               (template_id, version_number, sections_json, theme_tokens, changelog_note, created_by)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                template_id,
                new_version,
                sections_json,
                json.dumps(body.tokens),
                body.changelog or "Theme update",
                body.created_by,
            ),
        )
        conn.execute(
            """UPDATE report_templates
               SET current_version=?, updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
               WHERE id=?""",
            (new_version, template_id),
        )
        row = conn.execute(
            "SELECT * FROM report_templates WHERE id=?",
            (template_id,),
        ).fetchone()

    return _template_row(row)


# ── Clone ──────────────────────────────────────────────────────────────────────

@templates_router.post(
    "/{template_id}/clone",
    response_model=TemplateResponse,
    status_code=201,
    summary="Clone template",
)
def clone_template(template_id: int, body: TemplateCloneRequest) -> TemplateResponse:
    from db import get_db
    with get_db() as conn:
        source = conn.execute(
            "SELECT * FROM report_templates WHERE id=?", (template_id,)
        ).fetchone()
        if source is None:
            raise HTTPException(404, f"Template {template_id} not found")

        # Get latest version's sections/tokens to copy
        latest_ver = conn.execute(
            """SELECT sections_json, theme_tokens FROM template_versions
               WHERE template_id=? ORDER BY version_number DESC LIMIT 1""",
            (template_id,),
        ).fetchone()

        cur = conn.execute(
            """INSERT INTO report_templates
               (name, description, industry_profile_id, base_locale, current_version)
               VALUES (?, ?, ?, ?, 1)""",
            (
                body.name,
                body.description or source["description"],
                source["industry_profile_id"],
                source["base_locale"],
            ),
        )
        new_tmpl_id = cur.lastrowid

        if latest_ver:
            conn.execute(
                """INSERT INTO template_versions
                   (template_id, version_number, sections_json, theme_tokens, changelog_note)
                   VALUES (?, 1, ?, ?, ?)""",
                (
                    new_tmpl_id,
                    latest_ver["sections_json"],
                    latest_ver["theme_tokens"],
                    f"Cloned from template {template_id}",
                ),
            )

        row = conn.execute(
            "SELECT * FROM report_templates WHERE id=?", (new_tmpl_id,)
        ).fetchone()
    return _template_row(row)


# ── Client overrides ──────────────────────────────────────────────────────────

@templates_router.get(
    "/{template_id}/versions/{version_id}/overrides/{client_id}",
    summary="Get client template override",
)
def get_override(
    template_id: int,
    version_id: int,
    client_id: str = Depends(validate_client),
) -> dict:
    from db import get_db
    with get_db() as conn:
        row = conn.execute(
            """SELECT * FROM client_template_overrides
               WHERE client_id=? AND template_version_id=?""",
            (client_id, version_id),
        ).fetchone()
    if row is None:
        return {"client_id": client_id, "template_version_id": version_id, "overrides": {}}
    return {
        "id": row["id"],
        "client_id": row["client_id"],
        "template_version_id": row["template_version_id"],
        "overrides": json.loads(row["overrides_json"]),
        "is_active": bool(row["is_active"]),
    }


@templates_router.put(
    "/{template_id}/versions/{version_id}/overrides/{client_id}",
    summary="Set client template override",
)
def set_override(
    template_id: int,
    version_id: int,
    overrides: dict,
    client_id: str = Depends(validate_client),
) -> dict:
    from db import get_db
    with get_db() as conn:
        existing = conn.execute(
            """SELECT id FROM client_template_overrides
               WHERE client_id=? AND template_version_id=?""",
            (client_id, version_id),
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE client_template_overrides
                   SET overrides_json=?, updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                   WHERE client_id=? AND template_version_id=?""",
                (json.dumps(overrides), client_id, version_id),
            )
        else:
            conn.execute(
                """INSERT INTO client_template_overrides
                   (client_id, template_version_id, overrides_json)
                   VALUES (?, ?, ?)""",
                (client_id, version_id, json.dumps(overrides)),
            )
    return {"client_id": client_id, "template_version_id": version_id, "overrides": overrides}
