import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import RawEvent, Watchlist
from app.schemas.legal import GenericHtmlLegalCollectRequest
from app.schemas.news import GenericHtmlNewsCollectRequest
from app.schemas.provider import GenericHtmlJobsCollectRequest, JsonJobsCollectRequest, JsonLdJobsCollectRequest
from app.schemas.watchlist import WatchlistCreate, WatchlistRunResult
from app.services.lead_generation import generate_lead_snapshot
from app.services.legal_ingestion import collect_generic_html_legal
from app.services.news_ingestion import collect_generic_html_news
from app.services.provider_ingestion import collect_generic_html_jobs, collect_json_jobs, collect_jsonld_jobs


def create_watchlist(db: Session, payload: WatchlistCreate) -> Watchlist:
    watchlist = Watchlist(**payload.model_dump())
    db.add(watchlist)
    db.commit()
    db.refresh(watchlist)
    return watchlist


def list_watchlists(db: Session, active_only: bool = False) -> list[Watchlist]:
    query = db.query(Watchlist).order_by(Watchlist.created_at.desc())
    if active_only:
        query = query.filter(Watchlist.active.is_(True))
    return query.all()


def run_watchlist(db: Session, watchlist: Watchlist) -> WatchlistRunResult:
    config = json.loads(watchlist.config_json)
    created_events = []

    if watchlist.source_kind == 'generic_html_jobs':
        created_events = collect_generic_html_jobs(db, GenericHtmlJobsCollectRequest(**config))
    elif watchlist.source_kind == 'json_jobs':
        created_events = collect_json_jobs(db, JsonJobsCollectRequest(**config))
    elif watchlist.source_kind == 'jsonld_jobs':
        created_events = collect_jsonld_jobs(db, JsonLdJobsCollectRequest(**config))
    elif watchlist.source_kind == 'generic_html_news':
        created_events = collect_generic_html_news(db, GenericHtmlNewsCollectRequest(**config))
    elif watchlist.source_kind == 'generic_html_legal':
        created_events = collect_generic_html_legal(db, GenericHtmlLegalCollectRequest(**config))
    else:
        raise ValueError(f'Tipo de watchlist não suportado: {watchlist.source_kind}')

    impacted_company_ids = sorted({event.company_id for event in created_events if event.company_id})
    generated_leads = 0
    for company_id in impacted_company_ids:
        generate_lead_snapshot(db, company_id)
        generated_leads += 1

    watchlist.last_run_at = datetime.utcnow()
    db.add(watchlist)
    db.commit()
    db.refresh(watchlist)

    return WatchlistRunResult(
        watchlist_id=watchlist.id,
        created_events=len(created_events),
        generated_leads=generated_leads,
        impacted_company_ids=impacted_company_ids,
        detail=f'Watchlist {watchlist.name} executada com sucesso',
    )
