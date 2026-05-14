from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.data.signal_taxonomy import SOURCE_SEEDS
from app.db.models import Source


def seed_sources(db: Session) -> None:
    for item in SOURCE_SEEDS:
        exists = db.query(Source.id).filter(Source.name == item['name']).first()
        if exists:
            continue
        try:
            db.add(Source(**item))
            db.commit()
        except IntegrityError:
            db.rollback()
