from sqlalchemy.orm import Session

from app.db.models import Company, LeadSnapshot, Signal
from app.services.lead_formatter import format_executive_lead
from app.services.match_quality import average_match_confidence, score_adjustment_from_match
from app.services.scoring import score_company
from app.services.webhooks import dispatch_snapshot_to_eligible_targets


def _adjust_lead_tier(score: float) -> str:
    if score >= 81:
        return 'A'
    if score >= 61:
        return 'B'
    if score >= 41:
        return 'C'
    return 'D'


def _adjust_conversion(score: float) -> str:
    if score >= 81:
        return 'muito alta'
    if score >= 61:
        return 'alta'
    if score >= 31:
        return 'média'
    return 'baixa'


def generate_lead_snapshot(db: Session, company_id: int, auto_dispatch: bool = True) -> LeadSnapshot:
    company = db.get(Company, company_id)
    if not company:
        raise ValueError('Company not found')

    signals = db.query(Signal).filter(Signal.company_id == company_id).order_by(Signal.detected_at.desc()).all()
    result = score_company(company, signals)

    avg_match_confidence = average_match_confidence(db, company_id)
    match_adjustment, match_explanation = score_adjustment_from_match(avg_match_confidence)
    adjusted_score = round(min(max(result.score + match_adjustment, 0), 100), 2)
    result.score = adjusted_score
    result.lead_tier = _adjust_lead_tier(adjusted_score)
    result.conversion_probability = _adjust_conversion(adjusted_score)
    result.summary = (
        f"{result.summary} Qualidade média do match: {avg_match_confidence if avg_match_confidence is not None else 'desconhecida'}"
    )
    result.score_explanation = f"{result.score_explanation}; match_adjustment={match_adjustment}; {match_explanation}; final_adjusted_score={adjusted_score}"

    executive_lead = format_executive_lead(company, signals, result, avg_match_confidence=avg_match_confidence)

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
