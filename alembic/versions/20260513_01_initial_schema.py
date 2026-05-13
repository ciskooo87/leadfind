"""initial schema

Revision ID: 20260513_01
Revises: None
Create Date: 2026-05-13 21:50:00
"""

from alembic import op
import sqlalchemy as sa


revision = '20260513_01'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('legal_name', sa.String(length=255), nullable=False),
        sa.Column('trade_name', sa.String(length=255), nullable=True),
        sa.Column('cnpj_root', sa.String(length=20), nullable=True),
        sa.Column('sector', sa.String(length=120), nullable=True),
        sa.Column('city', sa.String(length=120), nullable=True),
        sa.Column('state', sa.String(length=2), nullable=True),
        sa.Column('estimated_size', sa.String(length=50), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('linkedin_url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_companies_id', 'companies', ['id'])
    op.create_index('ix_companies_cnpj_root', 'companies', ['cnpj_root'])
    op.create_index('ix_companies_sector', 'companies', ['sector'])
    op.create_index('ix_companies_website', 'companies', ['website'])

    op.create_table(
        'sources',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('reliability_score', sa.Float(), nullable=False),
        sa.Column('active', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_sources_id', 'sources', ['id'])
    op.create_index('ix_sources_name', 'sources', ['name'], unique=True)
    op.create_index('ix_sources_source_type', 'sources', ['source_type'])

    op.create_table(
        'watchlists',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('source_kind', sa.String(length=50), nullable=False),
        sa.Column('source_name', sa.String(length=100), nullable=False),
        sa.Column('config_json', sa.Text(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('schedule_minutes', sa.Integer(), nullable=True),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_watchlists_id', 'watchlists', ['id'])
    op.create_index('ix_watchlists_name', 'watchlists', ['name'], unique=True)
    op.create_index('ix_watchlists_source_kind', 'watchlists', ['source_kind'])
    op.create_index('ix_watchlists_source_name', 'watchlists', ['source_name'])

    op.create_table(
        'lead_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('conversion_probability', sa.String(length=20), nullable=False),
        sa.Column('lead_tier', sa.String(length=20), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('hypothesis_of_pain', sa.Text(), nullable=False),
        sa.Column('best_approach', sa.Text(), nullable=False),
        sa.Column('recommended_product', sa.String(length=120), nullable=False),
        sa.Column('timing', sa.String(length=120), nullable=False),
        sa.Column('risk', sa.String(length=120), nullable=False),
        sa.Column('score_explanation', sa.Text(), nullable=False),
        sa.Column('executive_payload', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_lead_snapshots_id', 'lead_snapshots', ['id'])
    op.create_index('ix_lead_snapshots_company_id', 'lead_snapshots', ['company_id'])

    op.create_table(
        'raw_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source_id', sa.Integer(), sa.ForeignKey('sources.id'), nullable=False),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=True),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('company_name_raw', sa.String(length=255), nullable=True),
        sa.Column('company_website_raw', sa.String(length=255), nullable=True),
        sa.Column('city_raw', sa.String(length=120), nullable=True),
        sa.Column('state_raw', sa.String(length=10), nullable=True),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.Column('normalized_status', sa.String(length=20), nullable=False),
        sa.Column('normalized_signal_type', sa.String(length=255), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('source_id', 'external_id', name='uq_raw_event_source_external'),
    )
    op.create_index('ix_raw_events_id', 'raw_events', ['id'])
    op.create_index('ix_raw_events_source_id', 'raw_events', ['source_id'])
    op.create_index('ix_raw_events_company_id', 'raw_events', ['company_id'])
    op.create_index('ix_raw_events_external_id', 'raw_events', ['external_id'])
    op.create_index('ix_raw_events_company_name_raw', 'raw_events', ['company_name_raw'])
    op.create_index('ix_raw_events_company_website_raw', 'raw_events', ['company_website_raw'])
    op.create_index('ix_raw_events_occurred_at', 'raw_events', ['occurred_at'])
    op.create_index('ix_raw_events_normalized_status', 'raw_events', ['normalized_status'])
    op.create_index('ix_raw_events_normalized_signal_type', 'raw_events', ['normalized_signal_type'])

    op.create_table(
        'signals',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('signal_type', sa.String(length=100), nullable=False),
        sa.Column('source_name', sa.String(length=100), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('excerpt', sa.Text(), nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('weight_override', sa.Float(), nullable=True),
        sa.UniqueConstraint('company_id', 'signal_type', 'source_name', 'source_url', name='uq_signal_dedupe'),
    )
    op.create_index('ix_signals_id', 'signals', ['id'])
    op.create_index('ix_signals_company_id', 'signals', ['company_id'])
    op.create_index('ix_signals_category', 'signals', ['category'])
    op.create_index('ix_signals_signal_type', 'signals', ['signal_type'])
    op.create_index('ix_signals_detected_at', 'signals', ['detected_at'])

    op.create_table(
        'watchlist_run_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('watchlist_id', sa.Integer(), sa.ForeignKey('watchlists.id'), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_events', sa.Integer(), nullable=False),
        sa.Column('generated_leads', sa.Integer(), nullable=False),
        sa.Column('impacted_company_ids_json', sa.Text(), nullable=False),
        sa.Column('detail', sa.Text(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_watchlist_run_logs_id', 'watchlist_run_logs', ['id'])
    op.create_index('ix_watchlist_run_logs_watchlist_id', 'watchlist_run_logs', ['watchlist_id'])
    op.create_index('ix_watchlist_run_logs_status', 'watchlist_run_logs', ['status'])


def downgrade() -> None:
    op.drop_index('ix_watchlist_run_logs_status', table_name='watchlist_run_logs')
    op.drop_index('ix_watchlist_run_logs_watchlist_id', table_name='watchlist_run_logs')
    op.drop_index('ix_watchlist_run_logs_id', table_name='watchlist_run_logs')
    op.drop_table('watchlist_run_logs')

    op.drop_index('ix_signals_detected_at', table_name='signals')
    op.drop_index('ix_signals_signal_type', table_name='signals')
    op.drop_index('ix_signals_category', table_name='signals')
    op.drop_index('ix_signals_company_id', table_name='signals')
    op.drop_index('ix_signals_id', table_name='signals')
    op.drop_table('signals')

    op.drop_index('ix_raw_events_normalized_signal_type', table_name='raw_events')
    op.drop_index('ix_raw_events_normalized_status', table_name='raw_events')
    op.drop_index('ix_raw_events_occurred_at', table_name='raw_events')
    op.drop_index('ix_raw_events_company_website_raw', table_name='raw_events')
    op.drop_index('ix_raw_events_company_name_raw', table_name='raw_events')
    op.drop_index('ix_raw_events_external_id', table_name='raw_events')
    op.drop_index('ix_raw_events_company_id', table_name='raw_events')
    op.drop_index('ix_raw_events_source_id', table_name='raw_events')
    op.drop_index('ix_raw_events_id', table_name='raw_events')
    op.drop_table('raw_events')

    op.drop_index('ix_lead_snapshots_company_id', table_name='lead_snapshots')
    op.drop_index('ix_lead_snapshots_id', table_name='lead_snapshots')
    op.drop_table('lead_snapshots')

    op.drop_index('ix_watchlists_source_name', table_name='watchlists')
    op.drop_index('ix_watchlists_source_kind', table_name='watchlists')
    op.drop_index('ix_watchlists_name', table_name='watchlists')
    op.drop_index('ix_watchlists_id', table_name='watchlists')
    op.drop_table('watchlists')

    op.drop_index('ix_sources_source_type', table_name='sources')
    op.drop_index('ix_sources_name', table_name='sources')
    op.drop_index('ix_sources_id', table_name='sources')
    op.drop_table('sources')

    op.drop_index('ix_companies_website', table_name='companies')
    op.drop_index('ix_companies_sector', table_name='companies')
    op.drop_index('ix_companies_cnpj_root', table_name='companies')
    op.drop_index('ix_companies_id', table_name='companies')
    op.drop_table('companies')
