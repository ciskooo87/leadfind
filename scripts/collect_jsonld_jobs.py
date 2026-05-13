import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.session import SessionLocal
from app.schemas.provider import JsonLdJobsCollectRequest
from app.services.provider_ingestion import collect_jsonld_jobs


def main():
    parser = argparse.ArgumentParser(description="Coleta vagas de páginas com JSON-LD JobPosting")
    parser.add_argument("url")
    parser.add_argument("--source-name", default="Corporate Careers")
    parser.add_argument("--confidence", type=float, default=0.84)
    parser.add_argument("--no-normalize", action="store_true")
    args = parser.parse_args()

    payload = JsonLdJobsCollectRequest(
        url=args.url,
        source_name=args.source_name,
        confidence=args.confidence,
        normalize_after_insert=not args.no_normalize,
    )

    db = SessionLocal()
    try:
        events = collect_jsonld_jobs(db, payload)
        print(f"Coletados {len(events)} eventos")
        for event in events:
            print(f"id={event.id} company_id={event.company_id} status={event.normalized_status} signals={event.normalized_signal_type}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
