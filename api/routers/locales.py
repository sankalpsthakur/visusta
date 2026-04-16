"""
Locales router — GET catalog, GET/PUT per-client locale settings.
"""

from __future__ import annotations

import json
from typing import List, Sequence

from fastapi import APIRouter, Depends, HTTPException

from api.deps import validate_client
from api.schemas_mars import (
    ClientLocaleSettings,
    ClientLocaleSettingsUpdate,
    LocaleResponse,
)

locales_router = APIRouter(tags=["locales"])


# Alias map for locale codes that clients commonly submit but which are not
# canonical ISO 639-1 entries in the `locales` table. Keys are already
# lowercased + region-stripped before lookup, so only the bare alias goes here.
_LOCALE_ALIASES: dict[str, str] = {
    # Norwegian macro-language → Bokmål (the ISO 639-1 default written form).
    "no": "nb",
    "nor": "nb",
    # Iso 639-2/T three-letter forms commonly submitted from external clients.
    "nob": "nb",
    "nno": "nn",
    # Greek has two ISO 639-1 codes; map the alpha-3 to the seeded code.
    "ell": "el",
    "gre": "el",
}


def _normalize_locale(code: str) -> str:
    """Normalize a locale code for use at the API boundary.

    - Lowercases the input.
    - Strips any region/script tag (``en-GB`` → ``en``, ``no-NO`` → ``no``).
    - Applies :data:`_LOCALE_ALIASES` (``no`` → ``nb``, ``nor`` → ``nb``).

    The return value is still unvalidated against the active `locales` table —
    callers must look it up before trusting it. Empty / non-string input is
    returned as an empty string so downstream validators produce a sensible
    error rather than a crash.
    """
    if not isinstance(code, str):
        return ""
    trimmed = code.strip().lower()
    if not trimmed:
        return ""
    # Strip region or script subtag: ``no-NO``, ``zh-Hant``, ``en_GB`` all collapse.
    for sep in ("-", "_"):
        if sep in trimmed:
            trimmed = trimmed.split(sep, 1)[0]
    return _LOCALE_ALIASES.get(trimmed, trimmed)


def _active_locale_codes(conn) -> List[str]:
    """Return all currently active locale codes, sorted, for error messages."""
    rows = conn.execute(
        "SELECT code FROM locales WHERE is_active=1 ORDER BY code"
    ).fetchall()
    return [row["code"] for row in rows]


def _require_known_locale(conn, code: str, *, field: str) -> str:
    """Normalize and verify that ``code`` exists in the active locales table.

    Raises :class:`HTTPException` (422) with the list of valid codes if not.
    Returns the normalized code on success.
    """
    normalized = _normalize_locale(code)
    active = _active_locale_codes(conn)
    if normalized not in active:
        raise HTTPException(
            status_code=422,
            detail={
                "error": f"Unknown locale for {field}: {code!r}",
                "normalized": normalized,
                "valid_codes": active,
            },
        )
    return normalized


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

        # Normalize + validate only the fields the caller is actually setting.
        # Legacy DB values are trusted so a previous bad save doesn't lock a
        # client out of PATCH-style updates that touch different fields.
        if body.primary_locale is not None:
            primary = _require_known_locale(conn, body.primary_locale, field="primary_locale")
        elif existing is not None:
            primary = existing["primary_locale"]
        else:
            primary = "en"

        if body.enabled_locales is not None:
            if not body.enabled_locales:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "enabled_locales must contain at least one locale",
                        "valid_codes": _active_locale_codes(conn),
                    },
                )
            # Preserve caller order, dedupe, and normalize+validate each entry.
            normalized_enabled: List[str] = []
            seen: set[str] = set()
            for raw in body.enabled_locales:
                code = _require_known_locale(conn, raw, field="enabled_locales")
                if code not in seen:
                    seen.add(code)
                    normalized_enabled.append(code)
            enabled = normalized_enabled
        elif existing is not None:
            enabled = json.loads(existing["enabled_locales"])
        else:
            enabled = [primary]

        if body.fallback_locale is not None:
            fallback = _require_known_locale(conn, body.fallback_locale, field="fallback_locale")
        elif existing is not None:
            fallback = existing["fallback_locale"]
        else:
            fallback = "en"

        if existing is None:
            conn.execute(
                """INSERT INTO client_locale_settings
                   (client_id, primary_locale, enabled_locales, fallback_locale)
                   VALUES (?, ?, ?, ?)""",
                (client_id, primary, json.dumps(enabled), fallback),
            )
        else:
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
