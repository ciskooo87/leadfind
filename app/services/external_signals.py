from sqlalchemy.orm import Session

from app.db.models import ExternalMarketSignal
from app.schemas.external_signal import ExternalMarketSignalCreate, ExternalMarketSignalRead


def create_external_signal(db: Session, payload: ExternalMarketSignalCreate) -> ExternalMarketSignalRead:
    signal = ExternalMarketSignal(**payload.model_dump())
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return ExternalMarketSignalRead(
        id=signal.id,
        signal_key=signal.signal_key,
        title=signal.title,
        source_name=signal.source_name,
        source_url=signal.source_url,
        summary=signal.summary,
        relevance_weight=signal.relevance_weight,
        active=signal.active,
        created_at=signal.created_at,
    )


def list_external_signals(db: Session, active_only: bool = False) -> list[ExternalMarketSignalRead]:
    query = db.query(ExternalMarketSignal)
    if active_only:
        query = query.filter(ExternalMarketSignal.active.is_(True))
    items = query.order_by(ExternalMarketSignal.created_at.desc()).all()
    return [
        ExternalMarketSignalRead(
            id=item.id,
            signal_key=item.signal_key,
            title=item.title,
            source_name=item.source_name,
            source_url=item.source_url,
            summary=item.summary,
            relevance_weight=item.relevance_weight,
            active=item.active,
            created_at=item.created_at,
        )
        for item in items
    ]


def external_signal_context(db: Session) -> dict[str, int]:
    items = db.query(ExternalMarketSignal).filter(ExternalMarketSignal.active.is_(True)).all()
    context: dict[str, int] = {}
    for item in items:
        context[item.signal_key] = context.get(item.signal_key, 0) + int(item.relevance_weight or 0)
    return context
