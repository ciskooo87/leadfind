import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.session import SessionLocal
from app.schemas.provider import JsonJobsCollectRequest
from app.services.provider_ingestion import collect_json_jobs


def main():
    parser = argparse.ArgumentParser(description="Coleta vagas de um feed JSON para o LeadFind")
    parser.add_argument("url")
    parser.add_argument("--source-name", default="Indeed")
    parser.add_argument("--items-path", default="jobs")
    parser.add_argument("--title-path", default="title")
    parser.add_argument("--content-path", default="description")
    parser.add_argument("--company-path", default="company.name")
    parser.add_argument("--city-path", default="location.city")
    parser.add_argument("--state-path", default="location.state")
    parser.add_argument("--link-path", default="url")
    parser.add_argument("--website-path", default="company.website")
    parser.add_argument("--external-id-path", default="id")
    parser.add_argument("--confidence", type=float, default=0.78)
    parser.add_argument("--no-normalize", action="store_true")
    args = parser.parse_args()

    payload = JsonJobsCollectRequest(
        url=args.url,
        source_name=args.source_name,
        items_path=args.items_path,
        title_path=args.title_path,
        content_path=args.content_path,
        company_path=args.company_path,
        city_path=args.city_path,
        state_path=args.state_path,
        link_path=args.link_path,
        website_path=args.website_path,
        external_id_path=args.external_id_path,
        confidence=args.confidence,
        normalize_after_insert=not args.no_normalize,
    )

    db = SessionLocal()
    try:
        events = collect_json_jobs(db, payload)
        print(f"Coletados {len(events)} eventos")
        for event in events:
            print(f"id={event.id} company_id={event.company_id} status={event.normalized_status} signals={event.normalized_signal_type}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
