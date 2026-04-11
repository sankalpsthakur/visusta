"""
Visusta ESG Regulatory Intelligence Platform — FastAPI backend.

Client-scoped REST API wrapping pipeline.py, regulatory_screening.py,
gap_analysis.py, and the config client registry.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Make sure the project root is on sys.path so local modules resolve.
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from api.schemas import (
    AuditResponse,
    ClientCreate,
    ClientResponse,
    ClientSummary,
    EvidenceCreate,
    EvidenceListResponse,
    EvidenceRecord,
    FacilitySchema,
    FindingSchema,
    HealthResponse,
    MonthlyReportRequest,
    OverviewResponse,
    PeriodListResponse,
    QuarterlyReportRequest,
    ReportPreferences,
    ScreeningRunRequest,
    SourceConfig,
    Thresholds,
    TopicsResponse,
)

# ── Directory constants ────────────────────────────────────────────────────────
REGULATORY_DATA_DIR = PROJECT_ROOT / "regulatory_data"
OUTPUT_DIR = PROJECT_ROOT / "output"
CHARTS_DIR = PROJECT_ROOT / "charts"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Visusta ESG Regulatory Intelligence API",
    description="Multi-client REST API for the Visusta ESG regulatory screening platform.",
    version="2.0.0",
)

# CORS — allow Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving
app.mount("/charts", StaticFiles(directory=str(CHARTS_DIR)), name="charts")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _list_periods(directory: Path) -> List[str]:
    """Return sorted list of YYYY-MM period strings from JSON filenames.

    Excludes migration backup files (*.old.json) and anything whose stem
    is not a valid YYYY-MM period.
    """
    if not directory.exists():
        return []
    import re
    period_re = re.compile(r"^\d{4}-\d{2}$")
    return sorted(
        p.stem for p in directory.glob("*.json")
        if not p.name.endswith(".old.json") and period_re.match(p.stem)
    )


def _read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _serialize(obj: Any) -> Any:
    """Recursively serialize dataclass dicts, converting Enum keys/values and dates."""
    if isinstance(obj, dict):
        return {
            (k.value if isinstance(k, Enum) else k): _serialize(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_serialize(i) for i in obj]
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj


def _client_changelog_dir(client_id: str) -> Path:
    return REGULATORY_DATA_DIR / client_id / "changelogs"


def _client_state_dir(client_id: str) -> Path:
    return REGULATORY_DATA_DIR / client_id / "states"


def _client_output_dir(client_id: str) -> Path:
    return OUTPUT_DIR / client_id / "pdf"


# ── Client dependency ─────────────────────────────────────────────────────────

def validate_client(client_id: str) -> str:
    """FastAPI dependency: raise 404 if client_id is not in the registry."""
    from config import list_clients
    known = {c["client_id"] for c in list_clients()}
    if client_id not in known:
        raise HTTPException(status_code=404, detail=f"Client not found: {client_id}")
    return client_id


# ── Global routes ─────────────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse, summary="System health")
def health() -> HealthResponse:
    """Return platform health: config status, data directory connectivity, counts."""
    try:
        from config import get_config
        get_config()
        config_status = "ok"
    except Exception as exc:
        config_status = f"error: {exc}"

    # Aggregate counts across all clients
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


def _build_client_response(client_id: str, c: Dict[str, Any]) -> ClientResponse:
    facilities = [
        FacilitySchema(name=f["name"], jurisdiction=f["jurisdiction"])
        if isinstance(f, dict)
        else FacilitySchema(name=f, jurisdiction="")
        for f in c.get("facilities", [])
    ]
    sources = [SourceConfig(**s) for s in c.get("sources", [])]
    raw_thresh = c.get("thresholds", {})
    thresholds = Thresholds(**raw_thresh) if raw_thresh else Thresholds()
    raw_prefs = c.get("report_preferences", {})
    report_preferences = ReportPreferences(**raw_prefs) if raw_prefs else ReportPreferences()
    return ClientResponse(
        client_id=client_id,
        display_name=c.get("display_name", client_id),
        facilities=facilities,
        allowed_countries=c.get("allowed_countries", []),
        required_topics=c.get("required_topics", []),
        branding=c.get("branding"),
        created_at=c.get("created_at"),
        sources=sources,
        thresholds=thresholds,
        report_preferences=report_preferences,
    )


@app.get("/api/clients", response_model=List[ClientResponse], summary="List clients")
def list_clients_endpoint() -> List[ClientResponse]:
    """Return all registered clients."""
    from config import list_clients
    clients = list_clients()
    return [_build_client_response(c["client_id"], c) for c in clients]


@app.post("/api/clients", response_model=ClientResponse, summary="Create client", status_code=201)
def create_client(body: ClientCreate) -> ClientResponse:
    """Register a new client in the registry."""
    from config import load_client_registry, save_client_registry
    import re

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

    # Ensure data directories exist
    (REGULATORY_DATA_DIR / slug / "changelogs").mkdir(parents=True, exist_ok=True)
    (REGULATORY_DATA_DIR / slug / "states").mkdir(parents=True, exist_ok=True)
    (REGULATORY_DATA_DIR / slug / "audits").mkdir(parents=True, exist_ok=True)
    _client_output_dir(slug).mkdir(parents=True, exist_ok=True)

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
    """Return a high-level summary across all clients."""
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
                # Try to count changes from common changelog shapes
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


# ── Client-scoped router ───────────────────────────────────────────────────────

client_router = APIRouter(prefix="/api/clients/{client_id}", tags=["clients"])


@client_router.get("", response_model=ClientResponse, summary="Client detail")
def get_client(client_id: str = Depends(validate_client)) -> ClientResponse:
    """Return full detail for a single client."""
    from config import load_client_registry
    registry = load_client_registry()
    return _build_client_response(client_id, registry[client_id])


@client_router.put("", response_model=ClientResponse, summary="Update client")
def update_client(
    body: ClientCreate,
    client_id: str = Depends(validate_client),
) -> ClientResponse:
    """Update an existing client's configuration."""
    from config import load_client_registry, save_client_registry
    registry = load_client_registry()
    existing = registry[client_id]

    existing["display_name"] = body.display_name
    existing["facilities"] = [f.model_dump() for f in body.facilities]
    existing["allowed_countries"] = body.allowed_countries
    existing["required_topics"] = body.required_topics
    if body.branding is not None:
        existing["branding"] = body.branding
    if body.created_at is not None:
        existing["created_at"] = body.created_at

    registry[client_id] = existing
    save_client_registry(registry)

    return _build_client_response(client_id, existing)


@client_router.get(
    "/changelogs", response_model=PeriodListResponse, summary="List changelog periods"
)
def list_changelogs(client_id: str = Depends(validate_client)) -> PeriodListResponse:
    """List all available monthly changelog periods for a client."""
    return PeriodListResponse(periods=_list_periods(_client_changelog_dir(client_id)))


@client_router.get("/changelogs/{period}", summary="Get changelog for a period")
def get_changelog(
    period: str,
    client_id: str = Depends(validate_client),
) -> Any:
    """Return the changelog JSON for a given period, e.g. 2026-02."""
    path = _client_changelog_dir(client_id) / f"{period}.json"
    if not path.exists():
        raise HTTPException(
            status_code=404, detail=f"Changelog for period '{period}' not found."
        )
    return _read_json(path)


@client_router.get(
    "/states", response_model=PeriodListResponse, summary="List state snapshot periods"
)
def list_states(client_id: str = Depends(validate_client)) -> PeriodListResponse:
    """List all available regulatory state snapshot periods for a client."""
    return PeriodListResponse(periods=_list_periods(_client_state_dir(client_id)))


@client_router.get("/states/{period}", summary="Get state snapshot for a period")
def get_state(
    period: str,
    client_id: str = Depends(validate_client),
) -> Any:
    """Return the regulatory state JSON for a given period, e.g. 2026-02."""
    path = _client_state_dir(client_id) / f"{period}.json"
    if not path.exists():
        raise HTTPException(
            status_code=404, detail=f"State snapshot for period '{period}' not found."
        )
    return _read_json(path)


@client_router.post("/reports/monthly", summary="Generate monthly PDF report")
def generate_monthly_report(
    request: MonthlyReportRequest,
    client_id: str = Depends(validate_client),
) -> FileResponse:
    """
    Run the monthly screening pipeline for a client and return the generated PDF.
    """
    period = request.period
    out_dir = _client_output_dir(client_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_pdf = out_dir / f"Monthly_Impact_Report_{period}.pdf"

    prefs = {k: v for k, v in {
        "tone": request.tone,
        "depth": request.depth,
        "chart_mix": request.chart_mix,
        "section_order": request.section_order,
    }.items() if v is not None} or None

    try:
        from pipeline import generate_monthly_pdf
        result_path_str = generate_monthly_pdf(
            client_id=client_id,
            period=period,
            output_path=str(output_pdf),
            preferences=prefs,
        )
        result_path = Path(result_path_str)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Monthly report generation failed: {exc}"
        )

    if not result_path.exists():
        raise HTTPException(status_code=500, detail="Report file was not created.")

    media_type = "application/pdf" if result_path.suffix == ".pdf" else "application/json"
    return FileResponse(path=str(result_path), media_type=media_type, filename=result_path.name)


@client_router.post("/reports/quarterly", summary="Generate quarterly PDF brief")
def generate_quarterly_report(
    request: QuarterlyReportRequest,
    client_id: str = Depends(validate_client),
) -> FileResponse:
    """
    Run the full monthly→quarterly pipeline for a client and return the generated PDF.
    """
    quarter = f"Q{request.quarter}"
    year = request.year
    out_dir = _client_output_dir(client_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_pdf = out_dir / f"Quarterly_Strategic_Brief_{quarter}_{year}.pdf"

    prefs = {k: v for k, v in {
        "tone": request.tone,
        "depth": request.depth,
        "chart_mix": request.chart_mix,
        "section_order": request.section_order,
    }.items() if v is not None} or None

    try:
        from pipeline import generate_quarterly_pdf
        result_path_str = generate_quarterly_pdf(
            client_id=client_id,
            quarter=quarter,
            year=year,
            output_path=str(output_pdf),
            preferences=prefs,
        )
        result_path = Path(result_path_str)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Quarterly report generation failed: {exc}"
        )

    if not result_path.exists():
        raise HTTPException(status_code=500, detail="Report file was not created.")

    media_type = "application/pdf" if result_path.suffix == ".pdf" else "application/json"
    return FileResponse(path=str(result_path), media_type=media_type, filename=result_path.name)


@client_router.post("/screening/run", summary="Trigger a monthly screening run")
def run_screening(
    request: ScreeningRunRequest,
    client_id: str = Depends(validate_client),
) -> Any:
    """
    Trigger a monthly screening run for a client and return the changelog JSON.
    """
    period = request.period

    try:
        from pipeline import run_monthly_pipeline
        changelog = run_monthly_pipeline(client_id=client_id, period=period)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Screening run failed: {exc}")

    try:
        result = _serialize(asdict(changelog))
    except Exception:
        result = {"period": period, "status": "completed"}

    return JSONResponse(content=result)


@client_router.get("/audit", response_model=AuditResponse, summary="Run gap analysis audit")
def run_audit_endpoint(client_id: str = Depends(validate_client)) -> AuditResponse:
    """Run the gap analysis auditor for a client and return all findings."""
    try:
        from gap_analysis import run_audit
        report = run_audit(client_id=client_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Audit failed: {exc}")

    findings = [
        FindingSchema(
            severity=f.severity,
            category=f.category,
            location=f.location,
            message=f.message,
            evidence=f.evidence,
        )
        for f in report.findings
    ]

    return AuditResponse(finding_count=len(findings), findings=findings)


@client_router.get("/topics", response_model=TopicsResponse, summary="ESG topics for client")
def list_topics(client_id: str = Depends(validate_client)) -> TopicsResponse:
    """Return the list of ESG topics monitored for this client."""
    try:
        from config import get_client_config
        cfg = get_client_config(client_id)
        topics = cfg.screening.required_topics
    except Exception:
        topics = ["ghg", "packaging", "water", "waste", "social_human_rights"]

    return TopicsResponse(topics=topics)


@client_router.get("/sources", response_model=List[SourceConfig], summary="Data sources for client")
def get_sources(client_id: str = Depends(validate_client)) -> List[SourceConfig]:
    """Return configured regulatory data sources for a client."""
    from config import load_client_registry
    registry = load_client_registry()
    return [SourceConfig(**s) for s in registry[client_id].get("sources", [])]


@client_router.put("/sources", response_model=List[SourceConfig], summary="Update data sources for client")
def update_sources(
    sources: List[SourceConfig],
    client_id: str = Depends(validate_client),
) -> List[SourceConfig]:
    """Replace the regulatory data sources list for a client."""
    from config import load_client_registry, save_client_registry
    registry = load_client_registry()
    registry[client_id]["sources"] = [s.model_dump() for s in sources]
    save_client_registry(registry)
    return sources


@client_router.get("/thresholds", response_model=Thresholds, summary="Thresholds for client")
def get_thresholds(client_id: str = Depends(validate_client)) -> Thresholds:
    """Return screening thresholds for a client."""
    from config import load_client_registry
    registry = load_client_registry()
    raw = registry[client_id].get("thresholds", {})
    return Thresholds(**raw) if raw else Thresholds()


@client_router.put("/thresholds", response_model=Thresholds, summary="Update thresholds for client")
def update_thresholds(
    thresholds: Thresholds,
    client_id: str = Depends(validate_client),
) -> Thresholds:
    """Replace screening thresholds for a client."""
    from config import load_client_registry, save_client_registry
    registry = load_client_registry()
    registry[client_id]["thresholds"] = thresholds.model_dump()
    save_client_registry(registry)
    return thresholds


@client_router.get("/preferences", response_model=ReportPreferences, summary="Report preferences for client")
def get_preferences(client_id: str = Depends(validate_client)) -> ReportPreferences:
    """Return report preferences for a client."""
    from config import load_client_registry
    registry = load_client_registry()
    raw = registry[client_id].get("report_preferences", {})
    return ReportPreferences(**raw) if raw else ReportPreferences()


@client_router.put("/preferences", response_model=ReportPreferences, summary="Update report preferences for client")
def update_preferences(
    preferences: ReportPreferences,
    client_id: str = Depends(validate_client),
) -> ReportPreferences:
    """Replace report preferences for a client."""
    from config import load_client_registry, save_client_registry
    registry = load_client_registry()
    registry[client_id]["report_preferences"] = preferences.model_dump()
    save_client_registry(registry)
    return preferences


@client_router.get("/evidence", response_model=EvidenceListResponse, summary="List evidence records")
def list_evidence(client_id: str = Depends(validate_client)) -> EvidenceListResponse:
    evidence_dir = REGULATORY_DATA_DIR / client_id / "evidence"
    if not evidence_dir.exists():
        return EvidenceListResponse(evidence=[], total=0)
    records = []
    for f in sorted(evidence_dir.glob("*.json")):
        with open(f) as fh:
            records.append(EvidenceRecord(**json.load(fh)))
    return EvidenceListResponse(evidence=records, total=len(records))


@client_router.get("/evidence/{evidence_id}", response_model=EvidenceRecord, summary="Get evidence record")
def get_evidence(evidence_id: str, client_id: str = Depends(validate_client)) -> EvidenceRecord:
    path = REGULATORY_DATA_DIR / client_id / "evidence" / f"{evidence_id}.json"
    if not path.exists():
        raise HTTPException(404, f"Evidence {evidence_id} not found")
    with open(path) as f:
        return EvidenceRecord(**json.load(f))


@client_router.post("/evidence", response_model=EvidenceRecord, status_code=201, summary="Create evidence record")
def create_evidence(body: EvidenceCreate, client_id: str = Depends(validate_client)) -> EvidenceRecord:
    from agents.source_scout import SourceScoutAgent
    agent = SourceScoutAgent()
    meta = {k: v for k, v in body.model_dump().items() if k != "url" and v is not None}
    result = agent.run({"client_id": client_id, "urls": [body.url], "metadata": meta})
    evidence_id = result["evidence_ids"][0]
    return get_evidence(evidence_id, client_id)


@client_router.delete("/evidence/{evidence_id}", summary="Delete evidence record")
def delete_evidence(evidence_id: str, client_id: str = Depends(validate_client)) -> dict:
    path = REGULATORY_DATA_DIR / client_id / "evidence" / f"{evidence_id}.json"
    if not path.exists():
        raise HTTPException(404, f"Evidence {evidence_id} not found")
    path.unlink()
    return {"deleted": evidence_id}


@client_router.post("/evidence/upload", response_model=EvidenceRecord, status_code=201, summary="Upload file as evidence")
async def upload_evidence(
    file: UploadFile = File(...),
    client_id: str = Depends(validate_client),
) -> EvidenceRecord:
    import hashlib
    from datetime import date

    files_dir = REGULATORY_DATA_DIR / client_id / "evidence" / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    today = date.today().isoformat()
    h = file_hash[:8]
    evidence_id = f"ev-{today[:7]}-{h}"

    stored_filename = f"{evidence_id}_{file.filename}"
    stored_path = files_dir / stored_filename
    with open(stored_path, "wb") as fh:
        fh.write(content)

    record = {
        "evidence_id": evidence_id,
        "client_id": client_id,
        "source_id": "upload",
        "source_name": "File Upload",
        "url": f"file://evidence/files/{stored_filename}",
        "access_date": today,
        "document_title": file.filename or "",
        "snippet": "",
        "hash": f"sha256:{file_hash}",
        "attached_by": "upload-endpoint",
        "confidence": 1.0,
        "topic": "unknown",
        "related_regulation_id": "",
    }

    record_path = REGULATORY_DATA_DIR / client_id / "evidence" / f"{evidence_id}.json"
    with open(record_path, "w") as fh:
        json.dump(record, fh, indent=2)

    return EvidenceRecord(**record)


# Mount the client-scoped router
app.include_router(client_router)
