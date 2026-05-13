import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.session import SessionLocal
from app.services.watchlists import run_due_watchlists


def main():
    db = SessionLocal()
    try:
        result = run_due_watchlists(db)
        print(json.dumps(result.model_dump(mode='json'), ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == '__main__':
    main()
