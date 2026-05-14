import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

TEST_DB_DIR = Path(__file__).resolve().parents[1] / '.testdata'
TEST_DB_DIR.mkdir(exist_ok=True)
TEST_DB = TEST_DB_DIR / f'leadfind_test_{os.getpid()}.db'
os.environ['DATABASE_URL'] = f'sqlite:///{TEST_DB}'

from alembic import command
from alembic.config import Config
from app.main import app
from app.db.session import SessionLocal, engine


@pytest.fixture(scope='session', autouse=True)
def prepare_db():
    engine.dispose()
    for suffix in ['', '-shm', '-wal']:
        path = Path(f'{TEST_DB}{suffix}')
        if path.exists():
            path.unlink()

    cfg = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    cfg.set_main_option('sqlalchemy.url', f'sqlite:///{TEST_DB}')
    command.upgrade(cfg, 'head')
    yield

    engine.dispose()
    for suffix in ['', '-shm', '-wal']:
        path = Path(f'{TEST_DB}{suffix}')
        if path.exists():
            path.unlink()


@pytest.fixture(autouse=True)
def reset_tables():
    db = SessionLocal()
    try:
        db.execute(text('PRAGMA foreign_keys=OFF'))
        for table in [
            'webhook_deliveries',
            'webhook_targets',
            'watchlist_run_logs',
            'watchlists',
            'lead_snapshots',
            'signals',
            'raw_events',
            'sources',
            'companies',
        ]:
            db.execute(text(f'DELETE FROM {table}'))
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture()
def client():
    return TestClient(app)
