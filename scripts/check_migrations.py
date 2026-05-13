import sqlite3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / 'leadfind.db'

EXPECTED_TABLES = {
    'alembic_version',
    'companies',
    'sources',
    'watchlists',
    'watchlist_run_logs',
    'raw_events',
    'signals',
    'lead_snapshots',
    'webhook_targets',
    'webhook_deliveries',
}


def main():
    if not DB_PATH.exists():
        raise SystemExit('Banco não encontrado; rode as migrações primeiro')

    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        found = {row[0] for row in rows}
        missing = sorted(EXPECTED_TABLES - found)
        if missing:
            raise SystemExit(f'Tabelas ausentes: {", ".join(missing)}')
        print('Schema validado com sucesso')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
