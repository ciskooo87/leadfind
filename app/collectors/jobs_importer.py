import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.schemas.raw_event import RawEventCreate
from app.services.ingestion import ingest_raw_events


REQUIRED_FIELDS = {"source_name", "content"}


def load_job_events_from_jsonl(path: str | Path) -> list[RawEventCreate]:
    file_path = Path(path)
    events: list[RawEventCreate] = []

    with file_path.open("r", encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            missing = REQUIRED_FIELDS - payload.keys()
            if missing:
                raise ValueError(f"Linha {line_number}: campos obrigatórios ausentes: {', '.join(sorted(missing))}")
            events.append(RawEventCreate(**payload))

    return events


def import_job_events_jsonl(db: Session, path: str | Path, normalize_after_insert: bool = True):
    events = load_job_events_from_jsonl(path)
    return ingest_raw_events(db, events, normalize_after_insert=normalize_after_insert)
