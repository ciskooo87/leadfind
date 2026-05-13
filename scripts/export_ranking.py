import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.session import SessionLocal
from app.services.exporters import ranking_to_csv_bytes, ranking_to_json_bytes
from app.services.lead_ranking import rank_latest_leads


def main():
    parser = argparse.ArgumentParser(description='Exporta ranking de leads')
    parser.add_argument('--format', choices=['csv', 'json'], default='json')
    parser.add_argument('--output', required=True)
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--min-score', type=float, default=None)
    parser.add_argument('--tier', default=None)
    parser.add_argument('--sector', default=None)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        ranking = rank_latest_leads(db, limit=args.limit, min_score=args.min_score, tier=args.tier, sector=args.sector)
        content = ranking_to_csv_bytes(ranking) if args.format == 'csv' else ranking_to_json_bytes(ranking)
        Path(args.output).write_bytes(content)
        print(f'Exportado para {args.output}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
