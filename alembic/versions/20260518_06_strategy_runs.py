"""add strategy analysis runs

Revision ID: 20260518_06
Revises: 20260514_05
Create Date: 2026-05-18 14:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = '20260518_06'
down_revision = '20260514_05'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'strategy_analysis_runs',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('request_payload', sa.Text(), nullable=False),
        sa.Column('response_payload', sa.Text(), nullable=False),
        sa.Column('winner_name', sa.String(length=255), nullable=False),
        sa.Column('top_opportunity_names', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_strategy_analysis_runs_id', 'strategy_analysis_runs', ['id'])
    op.create_index('ix_strategy_analysis_runs_winner_name', 'strategy_analysis_runs', ['winner_name'])
    op.create_index('ix_strategy_analysis_runs_created_at', 'strategy_analysis_runs', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_strategy_analysis_runs_created_at', table_name='strategy_analysis_runs')
    op.drop_index('ix_strategy_analysis_runs_winner_name', table_name='strategy_analysis_runs')
    op.drop_index('ix_strategy_analysis_runs_id', table_name='strategy_analysis_runs')
    op.drop_table('strategy_analysis_runs')
