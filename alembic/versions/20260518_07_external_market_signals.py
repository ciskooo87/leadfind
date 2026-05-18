"""add external market signals

Revision ID: 20260518_07
Revises: 20260518_06
Create Date: 2026-05-18 15:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = '20260518_07'
down_revision = '20260518_06'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'external_market_signals',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('signal_key', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('source_name', sa.String(length=100), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('relevance_weight', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_external_market_signals_id', 'external_market_signals', ['id'])
    op.create_index('ix_external_market_signals_signal_key', 'external_market_signals', ['signal_key'])
    op.create_index('ix_external_market_signals_source_name', 'external_market_signals', ['source_name'])
    op.create_index('ix_external_market_signals_created_at', 'external_market_signals', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_external_market_signals_created_at', table_name='external_market_signals')
    op.drop_index('ix_external_market_signals_source_name', table_name='external_market_signals')
    op.drop_index('ix_external_market_signals_signal_key', table_name='external_market_signals')
    op.drop_index('ix_external_market_signals_id', table_name='external_market_signals')
    op.drop_table('external_market_signals')
