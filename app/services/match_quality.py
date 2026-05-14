from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import RawEvent


def average_match_confidence(db: Session, company_id: int) -> float | None:
    value = (
        db.query(func.avg(RawEvent.match_confidence))
        .filter(RawEvent.company_id == company_id, RawEvent.match_confidence.isnot(None))
        .scalar()
    )
    return float(value) if value is not None else None


def match_quality_label(avg_match_confidence: float | None) -> str:
    if avg_match_confidence is None:
        return 'desconhecida'
    if avg_match_confidence >= 1.0:
        return 'alta'
    if avg_match_confidence >= 0.8:
        return 'média'
    return 'baixa'


def score_adjustment_from_match(avg_match_confidence: float | None) -> tuple[float, str]:
    if avg_match_confidence is None:
        return 0.0, 'match_quality=unknown'
    if avg_match_confidence >= 1.0:
        return 4.0, f'match_quality=high(avg={round(avg_match_confidence, 2)})'
    if avg_match_confidence >= 0.8:
        return 1.5, f'match_quality=medium(avg={round(avg_match_confidence, 2)})'
    return -6.0, f'match_quality=low(avg={round(avg_match_confidence, 2)})'
