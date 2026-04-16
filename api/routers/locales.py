"""
Locales router — GET catalog, GET/PUT per-client locale settings.
"""

from __future__ import annotations

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from api.deps import validate_client
from api.schemas_mars import (
    ClientLocaleSettings,
    ClientLocaleSettingsUpdate,
    LocaleResponse,
)

locales_router = APIRouter(tags=["locales"])


@locales_router.get("/api/locales", response_model=List[LocaleResponse], summary="List EU locales")
def list_locales() -> List[LocaleResponse]:
    """Return all active EU official locales from the database."""
    from db import get_db
    with get_db() as conn:
        rows = conn.execute(
            "SELECT code, name, native_name, is_active FROM locales WHERE is_active=1 ORDER BY code"
        ).fetchall()
    return [
        LocaleResponse(
            code=row["code"],
            name=row["name"],
            native_name=row["native_name"],
            is_active=bool(row["is_active"]),
        )
        for row in rows
    ]


@locales_router.get(
    "/api/clients/{client_id}/locale-settings",
    response_model=ClientLocaleSettings,
    summary="Get client locale settings",
)
def get_client_locale_settings(
    client_id: str = Depends(validate_client),
) -> ClientLocaleSettings:
    from db import get_db
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM client_locale_settings WHERE client_id=?", (client_id,)
        ).fetchone()
    if row is None:
        # Return sensible defaults if not yet configured
        return ClientLocaleSettings(
            client_id=client_id,
            primary_locale="en",
            enabled_locales=["en"],
            fallback_locale="en",
        )
    return ClientLocaleSettings(
        client_id=row["client_id"],
        primary_locale=row["primary_locale"],
        enabled_locales=json.loads(row["enabled_locales"]),
        fallback_locale=row["fallback_locale"],
        updated_at=row["updated_at"],
    )


@locales_router.put(
    "/api/clients/{client_id}/locale-settings",
    response_model=ClientLocaleSettings,
    summary="Update client locale settings",
)
def update_client_locale_settings(
    body: ClientLocaleSettingsUpdate,
    client_id: str = Depends(validate_client),
) -> ClientLocaleSettings:
    from db import get_db
    with get_db() as conn:
        existing = conn.execute(
            "SELECT * FROM client_locale_settings WHERE client_id=?", (client_id,)
        ).fetchone()

        if existing is None:
            primary = body.primary_locale or "en"
            enabled = body.enabled_locales or [primary]
            fallback = body.fallback_locale or "en"
            conn.execute(
                """INSERT INTO client_locale_settings
                   (client_id, primary_locale, enabled_locales, fallback_locale)
                   VALUES (?, ?, ?, ?)""",
                (client_id, primary, json.dumps(enabled), fallback),
            )
        else:
            primary = body.primary_locale or existing["primary_locale"]
            enabled = body.enabled_locales if body.enabled_locales is not None else json.loads(existing["enabled_locales"])
            fallback = body.fallback_locale or existing["fallback_locale"]
            conn.execute(
                """UPDATE client_locale_settings
                   SET primary_locale=?, enabled_locales=?, fallback_locale=?,
                       updated_at=strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                   WHERE client_id=?""",
                (primary, json.dumps(enabled), fallback, client_id),
            )

        row = conn.execute(
            "SELECT * FROM client_locale_settings WHERE client_id=?", (client_id,)
        ).fetchone()

    return ClientLocaleSettings(
        client_id=row["client_id"],
        primary_locale=row["primary_locale"],
        enabled_locales=json.loads(row["enabled_locales"]),
        fallback_locale=row["fallback_locale"],
        updated_at=row["updated_at"],
    )
