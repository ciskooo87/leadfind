from sqlalchemy.orm import Session

from app.collectors.reclame_aqui_provider import fetch_reclame_aqui_like_html
from app.collectors.reputation_html_provider import fetch_reputation_from_generic_html
from app.db.models import RawEvent, Source
from app.schemas.reputation import GenericHtmlReputationCollectRequest
from app.schemas.reputation_specific import ReclameAquiCollectRequest
from app.services.bootstrap import seed_sources
from app.services.reputation_normalization import normalize_reputation_raw_event


def _persist_reputation_items(db: Session, source: Source, items: list[dict], confidence: float, normalize_after_insert: bool) -> list[RawEvent]:
    created_events: list[RawEvent] = []
    for item in items:
        if item.get('external_id'):
            existing = (
                db.query(RawEvent)
                .filter(RawEvent.source_id == source.id, RawEvent.external_id == item['external_id'])
                .first()
            )
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
            confidence=confidence,
        )
        db.add(raw_event)
        db.commit()
        db.refresh(raw_event)

        if normalize_after_insert:
            raw_event = normalize_reputation_raw_event(db, raw_event)

        created_events.append(raw_event)

    return created_events


def collect_generic_html_reputation(db: Session, payload: GenericHtmlReputationCollectRequest) -> list[RawEvent]:
    seed_sources(db)
    source = db.query(Source).filter(Source.name == payload.source_name).first()
    if not source:
        raise ValueError(f'Source not found: {payload.source_name}')

    items = fetch_reputation_from_generic_html(
        url=str(payload.url),
        item_selector=payload.item_selector,
        title_selector=payload.title_selector,
        content_selector=payload.content_selector,
        company_selector=payload.company_selector,
        city_selector=payload.city_selector,
        state_selector=payload.state_selector,
        link_selector=payload.link_selector,
        website_selector=payload.website_selector,
    )
    return _persist_reputation_items(db, source, items, payload.confidence, payload.normalize_after_insert)


def collect_reclame_aqui_like(db: Session, payload: ReclameAquiCollectRequest) -> list[RawEvent]:
    seed_sources(db)
    source = db.query(Source).filter(Source.name == payload.source_name).first()
    if not source:
        raise ValueError(f'Source not found: {payload.source_name}')

    items = fetch_reclame_aqui_like_html(str(payload.url))
    return _persist_reputation_items(db, source, items, payload.confidence, payload.normalize_after_insert)
