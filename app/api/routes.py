import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.base import Base
from app.db.models import Company, LeadSnapshot, RawEvent, Signal, Source, Watchlist
from app.db.session import engine
from app.schemas.company import CompanyCreate, CompanyMatchRequest, CompanyRead
from app.schemas.lead import LeadExecutiveRead, LeadRead
from app.schemas.legal import GenericHtmlLegalCollectRequest
from app.schemas.news import GenericHtmlNewsCollectRequest
from app.schemas.provider import GenericHtmlJobsCollectRequest, JsonJobsCollectRequest, JsonLdJobsCollectRequest
from app.schemas.ranking import LeadRankingResponse
from app.schemas.raw_event import RawEventBatchCreate, RawEventCreate, RawEventRead
from app.schemas.signal import SignalCreate, SignalRead
from app.schemas.source import SourceRead
from app.schemas.watchlist import WatchlistCreate, WatchlistRead, WatchlistRunResult
from app.services.bootstrap import seed_sources
from app.services.company_resolution import match_company
from app.services.ingestion import ingest_raw_events
from app.services.lead_formatter import format_executive_lead
from app.services.lead_generation import generate_lead_snapshot
from app.services.lead_ranking import rank_latest_leads
from app.services.legal_ingestion import collect_generic_html_legal
from app.services.news_ingestion import collect_generic_html_news
from app.services.normalization import normalize_raw_event
from app.services.payloads import to_db_payload
from app.services.provider_ingestion import collect_generic_html_jobs, collect_json_jobs, collect_jsonld_jobs
from app.services.scoring import score_company
from app.services.watchlists import create_watchlist, list_watchlists, run_watchlist

Base.metadata.create_all(bind=engine)

router = APIRouter()


def _build_lead_read(snapshot: LeadSnapshot) -> LeadRead:
    return LeadRead(
        company_id=snapshot.company_id,
        score=snapshot.score,
        conversion_probability=snapshot.conversion_probability,
        lead_tier=snapshot.lead_tier,
        summary=snapshot.summary,
        hypothesis_of_pain=snapshot.hypothesis_of_pain,
        best_approach=snapshot.best_approach,
        recommended_product=snapshot.recommended_product,
        timing=snapshot.timing,
        risk=snapshot.risk,
        score_explanation=snapshot.score_explanation,
        created_at=snapshot.created_at,
    )


@router.get("/health")
def health(db: Session = Depends(get_db)):
    seed_sources(db)
    return {"status": "ok", "service": "leadfind"}


@router.get("/sources", response_model=list[SourceRead])
def list_sources(db: Session = Depends(get_db)):
    seed_sources(db)
    return db.query(Source).order_by(Source.name.asc()).all()


@router.get("/leads/ranking", response_model=LeadRankingResponse)
def get_leads_ranking(
    limit: int = Query(default=20, ge=1, le=100),
    min_score: float | None = Query(default=None, ge=0, le=100),
    tier: str | None = Query(default=None),
    sector: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return rank_latest_leads(db, limit=limit, min_score=min_score, tier=tier, sector=sector)


@router.get("/watchlists", response_model=list[WatchlistRead])
def get_watchlists(active_only: bool = Query(default=False), db: Session = Depends(get_db)):
    return list_watchlists(db, active_only=active_only)


@router.post("/watchlists", response_model=WatchlistRead)
def create_watchlist_route(payload: WatchlistCreate, db: Session = Depends(get_db)):
    return create_watchlist(db, payload)


@router.post("/watchlists/{watchlist_id}/run", response_model=WatchlistRunResult)
def run_watchlist_route(watchlist_id: int, db: Session = Depends(get_db)):
    watchlist = db.get(Watchlist, watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    try:
        return run_watchlist(db, watchlist)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/companies", response_model=CompanyRead)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    data = to_db_payload(payload.model_dump(mode="python"))
    company = Company(**data)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.post("/companies/match", response_model=CompanyRead | None)
def resolve_company_match(payload: CompanyMatchRequest, db: Session = Depends(get_db)):
    company = match_company(
        db,
        company_name=payload.company_name,
        website=str(payload.website) if payload.website else None,
        city=payload.city,
        state=payload.state,
        cnpj_root=payload.cnpj_root,
    )
    return company


@router.post("/signals", response_model=SignalRead)
def create_signal(payload: SignalCreate, db: Session = Depends(get_db)):
    company = db.get(Company, payload.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    data = to_db_payload(payload.model_dump(mode="python"))
    signal = Signal(**data)
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return signal


@router.post("/raw-events", response_model=RawEventRead)
def create_raw_event(payload: RawEventCreate, db: Session = Depends(get_db)):
    seed_sources(db)
    source = db.query(Source).filter(Source.name == payload.source_name).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if payload.external_id:
        existing = (
            db.query(RawEvent)
            .filter(RawEvent.source_id == source.id, RawEvent.external_id == payload.external_id)
            .first()
        )
        if existing:
            return existing

    data = to_db_payload(payload.model_dump(mode="python"))
    data.pop("source_name")
    raw_event = RawEvent(source_id=source.id, **data)
    db.add(raw_event)
    db.commit()
    db.refresh(raw_event)
    return raw_event


@router.post("/raw-events/batch", response_model=list[RawEventRead])
def create_raw_events_batch(payload: RawEventBatchCreate, db: Session = Depends(get_db)):
    try:
        return ingest_raw_events(db, payload.events, normalize_after_insert=payload.normalize_after_insert)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/raw-events/{raw_event_id}/normalize", response_model=RawEventRead)
def normalize_event(raw_event_id: int, db: Session = Depends(get_db)):
    raw_event = db.get(RawEvent, raw_event_id)
    if not raw_event:
        raise HTTPException(status_code=404, detail="Raw event not found")
    return normalize_raw_event(db, raw_event)


@router.post("/providers/generic-html-jobs/collect", response_model=list[RawEventRead])
def collect_jobs_from_generic_html(payload: GenericHtmlJobsCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_generic_html_jobs(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/providers/json-jobs/collect", response_model=list[RawEventRead])
def collect_jobs_from_json(payload: JsonJobsCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_json_jobs(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/providers/jsonld-jobs/collect", response_model=list[RawEventRead])
def collect_jobs_from_jsonld(payload: JsonLdJobsCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_jsonld_jobs(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/providers/generic-html-news/collect", response_model=list[RawEventRead])
def collect_news_from_generic_html(payload: GenericHtmlNewsCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_generic_html_news(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/providers/generic-html-legal/collect", response_model=list[RawEventRead])
def collect_legal_from_generic_html(payload: GenericHtmlLegalCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_generic_html_legal(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/leads/generate/{company_id}", response_model=LeadRead)
def generate_lead(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    snapshot = generate_lead_snapshot(db, company_id)
    return _build_lead_read(snapshot)


@router.get("/leads/{company_id}", response_model=list[LeadRead])
def list_leads(company_id: int, db: Session = Depends(get_db)):
    snapshots = db.query(LeadSnapshot).filter(LeadSnapshot.company_id == company_id).order_by(LeadSnapshot.created_at.desc()).all()
    return [_build_lead_read(s) for s in snapshots]


@router.get("/leads/{company_id}/executive", response_model=LeadExecutiveRead)
def get_latest_executive_lead(company_id: int, db: Session = Depends(get_db)):
    snapshot = (
        db.query(LeadSnapshot)
        .filter(LeadSnapshot.company_id == company_id)
        .order_by(LeadSnapshot.created_at.desc())
        .first()
    )
    if not snapshot:
        raise HTTPException(status_code=404, detail="Lead not found")

    if snapshot.executive_payload:
        return LeadExecutiveRead(**json.loads(snapshot.executive_payload))

    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    signals = db.query(Signal).filter(Signal.company_id == company_id).order_by(Signal.detected_at.desc()).all()
    result = score_company(company, signals)
    return format_executive_lead(company, signals, result)
