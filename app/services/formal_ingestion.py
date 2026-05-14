from sqlalchemy.orm import Session

from app.collectors.formal_acts_provider import fetch_formal_acts_like_html
from app.db.models import RawEvent, Source
from app.schemas.formal import FormalActsCollectRequest
from app.services.bootstrap import seed_sources
from app.services.formal_normalization import normalize_formal_raw_event


def collect_formal_acts_like(db: Session, payload: FormalActsCollectRequest) -> list[RawEvent]:
    seed_sources(db)
    source = db.query(Source).filter(Source.name == payload.source_name).first()
    if not source:
        raise ValueError(f'Source not found: {payload.source_name}')

    items = fetch_formal_acts_like_html(str(payload.url))
    created_events: list[RawEvent] = []
    for item in items:
        if item.get('external_id'):
            existing = db.query(RawEvent).filter(RawEvent.source_id == source.id, RawEvent.external_id == item['external_id']).first()
            if existing:
                created_events.append(existing)
                continue
        raw_event = RawEvent(
            source_id=source.id,
            external_id=item.get('external_id'),
            source_url=item.get('source_url'),
            title=item.get('title'),
            content=item.get('content') or '',
            company_name_raw=item.get('company_name_raw'),
            company_website_raw=item.get('company_website_raw'),
            city_raw=item.get('city_raw'),
            state_raw=item.get('state_raw'),
            confidence=payload.confidence,
        )
        db.add(raw_event)
        db.commit()
        db.refresh(raw_event)
        if payload.normalize_after_insert:
            raw_event = normalize_formal_raw_event(db, raw_event)
        created_events.append(raw_event)
    return created_events
