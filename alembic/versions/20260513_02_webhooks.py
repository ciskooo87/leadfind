"""add webhook tables

Revision ID: 20260513_02
Revises: 20260513_01
Create Date: 2026-05-13 22:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = '20260513_02'
down_revision = '20260513_01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'webhook_targets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('target_url', sa.String(length=1000), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('min_score', sa.Float(), nullable=False),
        sa.Column('lead_tiers', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_webhook_targets_id', 'webhook_targets', ['id'])
    op.create_index('ix_webhook_targets_name', 'webhook_targets', ['name'], unique=True)

    op.create_table(
        'webhook_deliveries',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('webhook_target_id', sa.Integer(), sa.ForeignKey('webhook_targets.id'), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_webhook_deliveries_id', 'webhook_deliveries', ['id'])
    op.create_index('ix_webhook_deliveries_webhook_target_id', 'webhook_deliveries', ['webhook_target_id'])
    op.create_index('ix_webhook_deliveries_company_id', 'webhook_deliveries', ['company_id'])
    op.create_index('ix_webhook_deliveries_status', 'webhook_deliveries', ['status'])


def downgrade() -> None:
    op.drop_index('ix_webhook_deliveries_status', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_company_id', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_webhook_target_id', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_id', table_name='webhook_deliveries')
    op.drop_table('webhook_deliveries')

    op.drop_index('ix_webhook_targets_name', table_name='webhook_targets')
    op.drop_index('ix_webhook_targets_id', table_name='webhook_targets')
    op.drop_table('webhook_targets')
