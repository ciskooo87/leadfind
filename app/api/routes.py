from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.base import Base
from app.db.models import Company, LeadSnapshot, Signal
from app.db.session import engine
from app.schemas.company import CompanyCreate, CompanyRead
from app.schemas.lead import LeadRead
from app.schemas.signal import SignalCreate, SignalRead
from app.services.scoring import score_company

Base.metadata.create_all(bind=engine)

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "service": "leadfind"}


@router.post("/companies", response_model=CompanyRead)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(mode="json")
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

    data = payload.model_dump(mode="json")
    signal = Signal(**data)
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return signal


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
