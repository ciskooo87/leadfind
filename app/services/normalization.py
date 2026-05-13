import re
import unicodedata

from sqlalchemy.orm import Session

from app.data.signal_taxonomy import JOB_SIGNAL_RULES
from app.db.models import RawEvent, Signal, Source
from app.services.company_resolution import match_company


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().strip()
    return re.sub(r"\s+", " ", value)


def infer_signals_from_job_text(text: str) -> list[tuple[str, str, float]]:
    normalized = normalize_text(text)
    inferred: list[tuple[str, str, float]] = []
    seen: set[str] = set()
    for keyword, value in JOB_SIGNAL_RULES.items():
        category, signal_type, confidence = value
        if keyword in normalized and signal_type not in seen:
            inferred.append((category, signal_type, confidence))
            seen.add(signal_type)
    return inferred


def _signal_exists(db: Session, company_id: int, signal_type: str, source_name: str, source_url: str | None) -> bool:
    return (
        db.query(Signal)
        .filter(
            Signal.company_id == company_id,
            Signal.signal_type == signal_type,
            Signal.source_name == source_name,
            Signal.source_url == source_url,
        )
        .first()
        is not None
    )


def normalize_raw_event(db: Session, raw_event: RawEvent) -> RawEvent:
    source = db.get(Source, raw_event.source_id)
    company = match_company(
        db,
        company_name=raw_event.company_name_raw,
        website=raw_event.company_website_raw,
        city=raw_event.city_raw,
        state=raw_event.state_raw,
    )
    if company:
        raw_event.company_id = company.id

    inferred_signals: list[tuple[str, str, float]] = []
    if source and source.source_type == "jobs":
        inferred_signals = infer_signals_from_job_text(f"{raw_event.title or ''} {raw_event.content}")

    if inferred_signals:
        raw_event.normalized_signal_type = ",".join(signal_type for _, signal_type, _ in inferred_signals)
        raw_event.normalized_status = "normalized"
        raw_event.confidence = max(raw_event.confidence, max(conf for _, _, conf in inferred_signals))

        if company:
            created_any = False
            for category, signal_type, inferred_confidence in inferred_signals:
                if _signal_exists(db, company.id, signal_type, source.name, raw_event.source_url):
                    continue
                signal = Signal(
                    company_id=company.id,
                    category=category,
                    signal_type=signal_type,
                    source_name=source.name,
                    source_url=raw_event.source_url,
                    excerpt=raw_event.content[:2000],
                    detected_at=raw_event.occurred_at,
                    confidence=min((max(raw_event.confidence, inferred_confidence) + source.reliability_score) / 2, 1.0),
                )
                db.add(signal)
                created_any = True
            raw_event.normalized_status = "signal_created" if created_any else "duplicate_signal"
    else:
        raw_event.normalized_status = "ignored"

    db.add(raw_event)
    db.commit()
    db.refresh(raw_event)
    return raw_event
