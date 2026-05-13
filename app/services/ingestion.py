from collections.abc import Iterable

from sqlalchemy.orm import Session

from app.db.models import RawEvent, Source
from app.schemas.raw_event import RawEventCreate
from app.services.bootstrap import seed_sources
from app.services.normalization import normalize_raw_event
from app.services.payloads import to_db_payload


def ingest_raw_events(db: Session, events: Iterable[RawEventCreate], normalize_after_insert: bool = True) -> list[RawEvent]:
    seed_sources(db)
    sources = {source.name: source for source in db.query(Source).all()}
    created_events: list[RawEvent] = []

    for payload in events:
        source = sources.get(payload.source_name)
        if not source:
            raise ValueError(f"Source not found: {payload.source_name}")

        if payload.external_id:
            existing = (
                db.query(RawEvent)
                .filter(RawEvent.source_id == source.id, RawEvent.external_id == payload.external_id)
                .first()
            )
            if existing:
                created_events.append(existing)
                continue

        data = to_db_payload(payload.model_dump(mode="python"))
        data.pop("source_name")
        raw_event = RawEvent(source_id=source.id, **data)
        db.add(raw_event)
        db.commit()
        db.refresh(raw_event)

        if normalize_after_insert:
            raw_event = normalize_raw_event(db, raw_event)

        created_events.append(raw_event)

    return created_events
