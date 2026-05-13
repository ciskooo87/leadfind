from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.base import Base
from app.db.models import Company, LeadSnapshot, RawEvent, Signal, Source
from app.db.session import engine
from app.schemas.company import CompanyCreate, CompanyRead
from app.schemas.lead import LeadRead
from app.schemas.raw_event import RawEventBatchCreate, RawEventCreate, RawEventRead
from app.schemas.signal import SignalCreate, SignalRead
from app.schemas.source import SourceRead
from app.services.bootstrap import seed_sources
from app.services.ingestion import ingest_raw_events
from app.services.normalization import normalize_raw_event
from app.services.payloads import to_db_payload
from app.services.scoring import score_company

Base.metadata.create_all(bind=engine)

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)):
    seed_sources(db)
    return {"status": "ok", "service": "leadfind"}


@router.get("/sources", response_model=list[SourceRead])
def list_sources(db: Session = Depends(get_db)):
    seed_sources(db)
    return db.query(Source).order_by(Source.name.asc()).all()


@router.post("/companies", response_model=CompanyRead)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    data = to_db_payload(payload.model_dump(mode="python"))
    company = Company(**data)
    db.add(company)
    db.commit()
    db.refresh(company)
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


@router.post("/leads/generate/{company_id}", response_model=LeadRead)
def generate_lead(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    signals = db.query(Signal).filter(Signal.company_id == company_id).order_by(Signal.detected_at.desc()).all()
    result = score_company(company, signals)

    snapshot = LeadSnapshot(
        company_id=company_id,
        score=result.score,
        conversion_probability=result.conversion_probability,
        lead_tier=result.lead_tier,
        summary=result.summary,
        hypothesis_of_pain=result.hypothesis_of_pain,
        best_approach=result.best_approach,
        recommended_product=result.recommended_product,
        timing=result.timing,
        risk=result.risk,
        score_explanation=result.score_explanation,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

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


@router.get("/leads/{company_id}", response_model=list[LeadRead])
def list_leads(company_id: int, db: Session = Depends(get_db)):
    snapshots = db.query(LeadSnapshot).filter(LeadSnapshot.company_id == company_id).order_by(LeadSnapshot.created_at.desc()).all()
    return [
        LeadRead(
            company_id=s.company_id,
            score=s.score,
            conversion_probability=s.conversion_probability,
            lead_tier=s.lead_tier,
            summary=s.summary,
            hypothesis_of_pain=s.hypothesis_of_pain,
            best_approach=s.best_approach,
            recommended_product=s.recommended_product,
            timing=s.timing,
            risk=s.risk,
            score_explanation=s.score_explanation,
            created_at=s.created_at,
        )
        for s in snapshots
    ]
