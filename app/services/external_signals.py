from sqlalchemy.orm import Session

from app.db.models import ExternalMarketSignal
from app.schemas.external_signal import ExternalMarketSignalCreate, ExternalMarketSignalRead, ExternalMarketSignalUpdate


def _to_read(signal: ExternalMarketSignal) -> ExternalMarketSignalRead:
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


def create_external_signal(db: Session, payload: ExternalMarketSignalCreate) -> ExternalMarketSignalRead:
    signal = ExternalMarketSignal(**payload.model_dump())
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return _to_read(signal)


def list_external_signals(db: Session, active_only: bool = False) -> list[ExternalMarketSignalRead]:
    query = db.query(ExternalMarketSignal)
    if active_only:
        query = query.filter(ExternalMarketSignal.active.is_(True))
    items = query.order_by(ExternalMarketSignal.created_at.desc()).all()
    return [_to_read(item) for item in items]


def get_external_signal(db: Session, signal_id: int) -> ExternalMarketSignalRead | None:
    signal = db.get(ExternalMarketSignal, signal_id)
    return _to_read(signal) if signal else None


def update_external_signal(db: Session, signal_id: int, payload: ExternalMarketSignalUpdate) -> ExternalMarketSignalRead | None:
    signal = db.get(ExternalMarketSignal, signal_id)
    if not signal:
        return None
    for key, value in payload.model_dump().items():
        setattr(signal, key, value)
    db.commit()
    db.refresh(signal)
    return _to_read(signal)


def toggle_external_signal(db: Session, signal_id: int) -> ExternalMarketSignalRead | None:
    signal = db.get(ExternalMarketSignal, signal_id)
    if not signal:
        return None
    signal.active = not signal.active
    db.commit()
    db.refresh(signal)
    return _to_read(signal)


def delete_external_signal(db: Session, signal_id: int) -> bool:
    signal = db.get(ExternalMarketSignal, signal_id)
    if not signal:
        return False
    db.delete(signal)
    db.commit()
    return True


def external_signal_context(db: Session) -> dict[str, int]:
    items = db.query(ExternalMarketSignal).filter(ExternalMarketSignal.active.is_(True)).all()
    context: dict[str, int] = {}
    for item in items:
        context[item.signal_key] = context.get(item.signal_key, 0) + int(item.relevance_weight or 0)
    return context
