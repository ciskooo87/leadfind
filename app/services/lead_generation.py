from sqlalchemy.orm import Session

from app.db.models import Company, LeadSnapshot, Signal
from app.services.lead_formatter import format_executive_lead
from app.services.scoring import score_company
from app.services.webhooks import dispatch_snapshot_to_eligible_targets


def generate_lead_snapshot(db: Session, company_id: int, auto_dispatch: bool = True) -> LeadSnapshot:
    company = db.get(Company, company_id)
    if not company:
        raise ValueError('Company not found')

    signals = db.query(Signal).filter(Signal.company_id == company_id).order_by(Signal.detected_at.desc()).all()
    result = score_company(company, signals)
    executive_lead = format_executive_lead(company, signals, result)

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
        executive_payload=executive_lead.model_dump_json(),
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    if auto_dispatch:
        dispatch_snapshot_to_eligible_targets(db, snapshot)

    return snapshot
