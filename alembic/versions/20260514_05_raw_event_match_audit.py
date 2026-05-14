"""add raw event match audit fields

Revision ID: 20260514_05
Revises: 20260514_04
Create Date: 2026-05-14 13:25:00
"""

from alembic import op
import sqlalchemy as sa


revision = '20260514_05'
down_revision = '20260514_04'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('raw_events', sa.Column('match_confidence', sa.Float(), nullable=True))
    op.add_column('raw_events', sa.Column('match_explanation', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('raw_events', 'match_explanation')
    op.drop_column('raw_events', 'match_confidence')
