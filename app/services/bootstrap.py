from sqlalchemy.orm import Session

from app.data.signal_taxonomy import SOURCE_SEEDS
from app.db.models import Source


def seed_sources(db: Session) -> None:
    existing = {source.name for source in db.query(Source).all()}
    created = False
    for item in SOURCE_SEEDS:
        if item["name"] in existing:
            continue
        db.add(Source(**item))
        created = True
    if created:
        db.commit()
