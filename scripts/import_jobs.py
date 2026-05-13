import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.collectors.jobs_importer import import_job_events_jsonl
from app.db.session import SessionLocal


def main():
    parser = argparse.ArgumentParser(description="Importa eventos de vagas em JSONL para o LeadFind")
    parser.add_argument("path", help="Caminho do arquivo JSONL")
    parser.add_argument("--no-normalize", action="store_true", help="Insere sem normalizar automaticamente")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        events = import_job_events_jsonl(db, args.path, normalize_after_insert=not args.no_normalize)
        print(f"Importados {len(events)} eventos")
        for event in events:
            print(
                f"id={event.id} source_id={event.source_id} company_id={event.company_id} "
                f"status={event.normalized_status} signals={event.normalized_signal_type}"
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
