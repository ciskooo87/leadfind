import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.models import LeadSnapshot
from app.db.session import SessionLocal
from app.schemas.lead import LeadExecutiveRead
from app.services.exporters import executive_lead_to_csv_bytes, executive_lead_to_json_bytes


def main():
    parser = argparse.ArgumentParser(description='Exporta lead executivo')
    parser.add_argument('company_id', type=int)
    parser.add_argument('--format', choices=['csv', 'json'], default='json')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        snapshot = db.query(LeadSnapshot).filter(LeadSnapshot.company_id == args.company_id).order_by(LeadSnapshot.created_at.desc()).first()
        if not snapshot or not snapshot.executive_payload:
            raise SystemExit('Lead executivo não encontrado')
        lead = LeadExecutiveRead(**json.loads(snapshot.executive_payload))
        content = executive_lead_to_csv_bytes(lead) if args.format == 'csv' else executive_lead_to_json_bytes(lead)
        Path(args.output).write_bytes(content)
        print(f'Exportado para {args.output}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
