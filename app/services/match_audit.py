from app.db.models import RawEvent
from app.services.company_resolution import MatchResult


def apply_match_audit(raw_event: RawEvent, match_result: MatchResult) -> None:
    if match_result.company:
        raw_event.company_id = match_result.company.id
    raw_event.match_confidence = match_result.score or None
    raw_event.match_explanation = match_result.explanation
