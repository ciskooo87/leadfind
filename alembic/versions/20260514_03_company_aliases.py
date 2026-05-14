"""add company aliases

Revision ID: 20260514_03
Revises: 20260513_02
Create Date: 2026-05-14 13:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = '20260514_03'
down_revision = '20260513_02'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('companies', sa.Column('aliases_json', sa.Text(), nullable=False, server_default='[]'))


def downgrade() -> None:
    op.drop_column('companies', 'aliases_json')
