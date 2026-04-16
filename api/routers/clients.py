"""
Client-scoped API router — wraps pipeline, regulatory_screening, gap_analysis, and config.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from api.deps import (
    REGULATORY_DATA_DIR,
    _build_client_response,
    _client_changelog_dir,
    _client_output_dir,
    _client_state_dir,
    _list_periods,
    _read_json,
    _serialize,
    validate_client,
)
from api.schemas import (
    AuditResponse,
    ClientCreate,
    ClientResponse,
    EvidenceCreate,
    EvidenceListResponse,
    EvidenceRecord,
    FindingSchema,
    MonthlyReportRequest,
    PeriodListResponse,
    QuarterlyReportRequest,
    ReportPreferences,
    ScreeningRunRequest,
    SourceConfig,
    Thresholds,
    TopicsResponse,
)

client_router = APIRouter(prefix="/api/clients/{client_id}", tags=["clients"])


@client_router.get("", response_model=ClientResponse, summary="Client detail")
def get_client(client_id: str = Depends(validate_client)) -> ClientResponse:
    from config import load_client_registry
    registry = load_client_registry()
    return _build_client_response(client_id, registry[client_id])


@client_router.put("", response_model=ClientResponse, summary="Update client")
def update_client(
    body: ClientCreate,
    client_id: str = Depends(validate_client),
) -> ClientResponse:
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
    return PeriodListResponse(periods=_list_periods(_client_changelog_dir(client_id)))


@client_router.get("/changelogs/{period}", summary="Get changelog for a period")
def get_changelog(
    period: str,
    client_id: str = Depends(validate_client),
) -> Any:
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
    return PeriodListResponse(periods=_list_periods(_client_state_dir(client_id)))


@client_router.get("/states/{period}", summary="Get state snapshot for a period")
def get_state(
    period: str,
    client_id: str = Depends(validate_client),
) -> Any:
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
            gap_type=f.gap_type,
        )
        for f in report.findings
    ]
    return AuditResponse(finding_count=len(findings), findings=findings)


@client_router.get("/topics", response_model=TopicsResponse, summary="ESG topics for client")
def list_topics(client_id: str = Depends(validate_client)) -> TopicsResponse:
    try:
        from config import get_client_config
        cfg = get_client_config(client_id)
        topics = cfg.screening.required_topics
    except Exception:
        topics = ["ghg", "packaging", "water", "waste", "social_human_rights"]
    return TopicsResponse(topics=topics)


@client_router.get("/sources", response_model=List[SourceConfig], summary="Data sources for client")
def get_sources(client_id: str = Depends(validate_client)) -> List[SourceConfig]:
    from config import load_client_registry
    registry = load_client_registry()
    return [SourceConfig(**s) for s in registry[client_id].get("sources", [])]


@client_router.put("/sources", response_model=List[SourceConfig], summary="Update data sources for client")
def update_sources(
    sources: List[SourceConfig],
    client_id: str = Depends(validate_client),
) -> List[SourceConfig]:
    from config import load_client_registry, save_client_registry
    registry = load_client_registry()
    registry[client_id]["sources"] = [s.model_dump() for s in sources]
    save_client_registry(registry)
    return sources


@client_router.get("/thresholds", response_model=Thresholds, summary="Thresholds for client")
def get_thresholds(client_id: str = Depends(validate_client)) -> Thresholds:
    from config import load_client_registry
    registry = load_client_registry()
    raw = registry[client_id].get("thresholds", {})
    return Thresholds(**raw) if raw else Thresholds()


@client_router.put("/thresholds", response_model=Thresholds, summary="Update thresholds for client")
def update_thresholds(
    thresholds: Thresholds,
    client_id: str = Depends(validate_client),
) -> Thresholds:
    from config import load_client_registry, save_client_registry
    registry = load_client_registry()
    registry[client_id]["thresholds"] = thresholds.model_dump()
    save_client_registry(registry)
    return thresholds


@client_router.get("/preferences", response_model=ReportPreferences, summary="Report preferences for client")
def get_preferences(client_id: str = Depends(validate_client)) -> ReportPreferences:
    from config import load_client_registry
    registry = load_client_registry()
    raw = registry[client_id].get("report_preferences", {})
    return ReportPreferences(**raw) if raw else ReportPreferences()


@client_router.put("/preferences", response_model=ReportPreferences, summary="Update report preferences for client")
def update_preferences(
    preferences: ReportPreferences,
    client_id: str = Depends(validate_client),
) -> ReportPreferences:
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


@client_router.post(
    "/evidence/upload",
    response_model=EvidenceRecord,
    status_code=201,
    summary="Upload file as evidence",
)
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
