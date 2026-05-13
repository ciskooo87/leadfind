import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

TEST_DB = Path('/tmp/leadfind_test.db')
os.environ['DATABASE_URL'] = f'sqlite:///{TEST_DB}'

from alembic import command
from alembic.config import Config
from app.main import app
from app.db.session import SessionLocal


@pytest.fixture(scope='session', autouse=True)
def prepare_db():
    if TEST_DB.exists():
        TEST_DB.unlink()
    cfg = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    command.upgrade(cfg, 'head')
    yield


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
