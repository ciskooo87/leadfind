"""add company alternate domains

Revision ID: 20260514_04
Revises: 20260514_03
Create Date: 2026-05-14 13:15:00
"""

from alembic import op
import sqlalchemy as sa


revision = '20260514_04'
down_revision = '20260514_03'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('companies', sa.Column('domains_json', sa.Text(), nullable=False, server_default='[]'))


def downgrade() -> None:
    op.drop_column('companies', 'domains_json')
