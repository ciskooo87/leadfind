import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models import Watchlist, WatchlistRunLog
from app.schemas.legal import GenericHtmlLegalCollectRequest
from app.schemas.news import GenericHtmlNewsCollectRequest
from app.schemas.provider import GenericHtmlJobsCollectRequest, JsonJobsCollectRequest, JsonLdJobsCollectRequest
from app.schemas.watchlist import WatchlistCreate, WatchlistRunResult, WatchlistSchedulerRunResponse
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


def list_watchlist_runs(db: Session, watchlist_id: int) -> list[WatchlistRunLog]:
    return (
        db.query(WatchlistRunLog)
        .filter(WatchlistRunLog.watchlist_id == watchlist_id)
        .order_by(WatchlistRunLog.started_at.desc())
        .all()
    )


def _execute_watchlist(db: Session, watchlist: Watchlist) -> WatchlistRunResult:
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


def run_watchlist(db: Session, watchlist: Watchlist) -> WatchlistRunResult:
    run_log = WatchlistRunLog(
        watchlist_id=watchlist.id,
        status='running',
        detail=f'Iniciando execução da watchlist {watchlist.name}'
    )
    db.add(run_log)
    db.commit()
    db.refresh(run_log)

    try:
        result = _execute_watchlist(db, watchlist)
        run_log.status = 'success'
        run_log.created_events = result.created_events
        run_log.generated_leads = result.generated_leads
        run_log.impacted_company_ids_json = json.dumps(result.impacted_company_ids)
        run_log.detail = result.detail
        run_log.finished_at = datetime.utcnow()
        db.add(run_log)
        db.commit()
        return result
    except Exception as exc:
        run_log.status = 'error'
        run_log.detail = str(exc)
        run_log.finished_at = datetime.utcnow()
        db.add(run_log)
        db.commit()
        raise


def run_due_watchlists(db: Session) -> WatchlistSchedulerRunResponse:
    watchlists = db.query(Watchlist).filter(Watchlist.active.is_(True)).order_by(Watchlist.created_at.asc()).all()
    results: list[WatchlistRunResult] = []
    skipped = 0
    now = datetime.utcnow()

    for watchlist in watchlists:
        if not watchlist.schedule_minutes:
            skipped += 1
            continue
        if watchlist.last_run_at and now - watchlist.last_run_at < timedelta(minutes=watchlist.schedule_minutes):
            skipped += 1
            continue
        results.append(run_watchlist(db, watchlist))

    return WatchlistSchedulerRunResponse(
        executed_watchlists=len(results),
        skipped_watchlists=skipped,
        results=results,
    )
