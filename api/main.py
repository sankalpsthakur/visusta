"""
Visusta ESG Regulatory Intelligence Platform — FastAPI application factory.

Keeps: app creation, CORS, static mounts, global routes, include_router calls.
Business logic lives in api/routers/*.py.
"""

from __future__ import annotations

import json
import re
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ── Project root on sys.path ───────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from api.deps import (
    CHARTS_DIR,
    OUTPUT_DIR,
    REGULATORY_DATA_DIR,
    _build_client_response,
    _client_changelog_dir,
    _list_periods,
    _read_json,
)
from api.routers.clients import client_router, run_audit_endpoint  # re-exported for back-compat
from api.routers.locales import locales_router
from api.routers.keywords import keywords_router
from api.routers.sources import sources_router
from api.routers.templates import templates_router
from api.routers.drafts import drafts_router
from api.routers.exports import exports_router
from api.schemas import (
    ClientCreate,
    ClientResponse,
    ClientSummary,
    HealthResponse,
    OverviewResponse,
)

# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    from db.migrate import run_migrations
    run_migrations()
    yield


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Visusta ESG Regulatory Intelligence API",
    description="Multi-client REST API for the Visusta ESG regulatory screening platform.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3100",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3100",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+$|https://.*\.onrender\.com$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.mount("/charts", StaticFiles(directory=str(CHARTS_DIR)), name="charts")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")


# ── Global routes ─────────────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse, summary="System health")
def health() -> HealthResponse:
    try:
        from config import get_config
        get_config()
        config_status = "ok"
    except Exception as exc:
        config_status = f"error: {exc}"

    total_changelogs = 0
    total_states = 0
    last_period: Optional[str] = None

    if REGULATORY_DATA_DIR.exists():
        for client_dir in REGULATORY_DATA_DIR.iterdir():
            if client_dir.is_dir():
                cl_periods = _list_periods(client_dir / "changelogs")
                st_periods = _list_periods(client_dir / "states")
                total_changelogs += len(cl_periods)
                total_states += len(st_periods)
                if cl_periods:
                    candidate = cl_periods[-1]
                    if last_period is None or candidate > last_period:
                        last_period = candidate

    return HealthResponse(
        status="ok",
        last_screening_date=last_period,
        config_status=config_status,
        data_dir_exists=REGULATORY_DATA_DIR.exists(),
        changelog_count=total_changelogs,
        state_count=total_states,
    )


@app.get("/api/clients", response_model=List[ClientResponse], summary="List clients")
def list_clients_endpoint() -> List[ClientResponse]:
    from config import list_clients
    clients = list_clients()
    return [_build_client_response(c["client_id"], c) for c in clients]


@app.post("/api/clients", response_model=ClientResponse, summary="Create client", status_code=201)
def create_client(body: ClientCreate) -> ClientResponse:
    from config import load_client_registry, save_client_registry

    if body.client_id:
        slug = body.client_id
    else:
        slug = re.sub(r"[^a-z0-9]+", "-", body.display_name.lower()).strip("-")

    registry = load_client_registry()
    if slug in registry:
        raise HTTPException(status_code=409, detail=f"Client already exists: {slug}")

    entry: Dict[str, Any] = {
        "display_name": body.display_name,
        "facilities": [f.model_dump() for f in body.facilities],
        "allowed_countries": body.allowed_countries,
        "required_topics": body.required_topics,
    }
    if body.branding:
        entry["branding"] = body.branding
    if body.created_at:
        entry["created_at"] = body.created_at

    registry[slug] = entry
    save_client_registry(registry)

    (REGULATORY_DATA_DIR / slug / "changelogs").mkdir(parents=True, exist_ok=True)
    (REGULATORY_DATA_DIR / slug / "states").mkdir(parents=True, exist_ok=True)
    (REGULATORY_DATA_DIR / slug / "audits").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / slug / "pdf").mkdir(parents=True, exist_ok=True)

    return ClientResponse(
        client_id=slug,
        display_name=body.display_name,
        facilities=body.facilities,
        allowed_countries=body.allowed_countries,
        required_topics=body.required_topics,
        branding=body.branding,
        created_at=body.created_at,
    )


@app.get("/api/overview", response_model=OverviewResponse, summary="Cross-client summary")
def overview() -> OverviewResponse:
    from config import list_clients
    summaries = []
    for c in list_clients():
        client_id = c["client_id"]
        cl_dir = _client_changelog_dir(client_id)
        periods = _list_periods(cl_dir)
        last_screening = periods[-1] if periods else None
        changes_detected = 0
        critical_count = 0
        if last_screening:
            try:
                data = _read_json(cl_dir / f"{last_screening}.json")
                if isinstance(data, dict):
                    for v in data.values():
                        if isinstance(v, list):
                            changes_detected += len(v)
            except Exception:
                pass
        summaries.append(ClientSummary(
            client_id=client_id,
            display_name=c.get("display_name", client_id),
            last_screening=last_screening,
            changes_detected=changes_detected,
            critical_count=critical_count,
        ))
    return OverviewResponse(clients=summaries)


# ── Include routers ────────────────────────────────────────────────────────────

app.include_router(client_router)
app.include_router(locales_router)
app.include_router(keywords_router)
app.include_router(sources_router)
app.include_router(templates_router)
app.include_router(drafts_router)
app.include_router(exports_router)
