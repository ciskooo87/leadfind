import json
from html import escape
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Company, LeadSnapshot, RawEvent, Signal, Source, Watchlist, WebhookTarget
from app.schemas.company import CompanyCreate, CompanyMatchRequest, CompanyRead
from app.schemas.discovery import DiscoveryRunRequest, DiscoveryRunResponse
from app.schemas.formal import FormalActsCollectRequest
from app.schemas.lead import LeadExecutiveRead, LeadRead
from app.schemas.legal import GenericHtmlLegalCollectRequest
from app.schemas.legal_specific import JusBrasilCollectRequest
from app.schemas.news import GenericHtmlNewsCollectRequest
from app.schemas.news_specific import RegionalNewsCollectRequest
from app.schemas.provider import GenericHtmlJobsCollectRequest, JsonJobsCollectRequest, JsonLdJobsCollectRequest
from app.schemas.provider_specific import (
    GreenhouseJobsCollectRequest,
    GupyJobsCollectRequest,
    LeverJobsCollectRequest,
    WorkdayJobsCollectRequest,
)
from app.schemas.ranking import LeadRankingResponse
from app.schemas.raw_event import RawEventBatchCreate, RawEventCreate, RawEventRead
from app.schemas.reputation import GenericHtmlReputationCollectRequest
from app.schemas.reputation_specific import ReclameAquiCollectRequest
from app.schemas.serasa import SerasaCollectRequest
from app.schemas.signal import SignalCreate, SignalRead
from app.schemas.source import SourceRead
from app.schemas.watchlist import (
    WatchlistCreate,
    WatchlistRead,
    WatchlistRunLogRead,
    WatchlistRunResult,
    WatchlistSchedulerRunResponse,
)
from app.schemas.webhook import WebhookDeliveryRead, WebhookTargetCreate, WebhookTargetRead
from app.services.bootstrap import seed_sources
from app.services.company_resolution import match_company
from app.services.discovery import run_discovery
from app.services.exporters import (
    executive_lead_to_csv_bytes,
    executive_lead_to_json_bytes,
    ranking_to_csv_bytes,
    ranking_to_json_bytes,
)
from app.services.formal_ingestion import collect_formal_acts_like
from app.services.ingestion import ingest_raw_events
from app.services.lead_formatter import format_executive_lead
from app.services.lead_generation import generate_lead_snapshot
from app.services.lead_ranking import rank_latest_leads
from app.services.legal_ingestion import collect_generic_html_legal, collect_jusbrasil_like
from app.services.news_ingestion import collect_generic_html_news, collect_regional_news_like
from app.services.normalization import normalize_raw_event
from app.services.payloads import to_db_payload
from app.services.provider_ingestion import (
    collect_generic_html_jobs,
    collect_greenhouse_jobs,
    collect_gupy_jobs,
    collect_json_jobs,
    collect_jsonld_jobs,
    collect_lever_jobs,
    collect_workday_jobs,
)
from app.services.reputation_ingestion import collect_generic_html_reputation, collect_reclame_aqui_like
from app.services.scoring import score_company
from app.services.serasa_ingestion import collect_serasa_like
from app.services.watchlists import create_watchlist, list_watchlist_runs, list_watchlists, run_due_watchlists, run_watchlist
from app.services.webhooks import create_webhook_target, deliver_lead_snapshot, dispatch_latest_leads, list_webhook_deliveries, list_webhook_targets

router = APIRouter()


def _company_aliases(company: Company) -> list[str]:
    raw = company.aliases_json or '[]'
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return [alias for alias in parsed if isinstance(alias, str)]


def _company_domains(company: Company) -> list[str]:
    raw = company.domains_json or '[]'
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return [domain for domain in parsed if isinstance(domain, str)]


def _build_company_read(company: Company) -> CompanyRead:
    return CompanyRead(
        id=company.id,
        legal_name=company.legal_name,
        trade_name=company.trade_name,
        cnpj_root=company.cnpj_root,
        sector=company.sector,
        city=company.city,
        state=company.state,
        estimated_size=company.estimated_size,
        website=company.website,
        linkedin_url=company.linkedin_url,
        aliases=_company_aliases(company),
        domains=_company_domains(company),
    )


def _build_lead_read(snapshot: LeadSnapshot) -> LeadRead:
    return LeadRead(
        company_id=snapshot.company_id,
        score=snapshot.score,
        conversion_probability=snapshot.conversion_probability,
        lead_tier=snapshot.lead_tier,
        summary=snapshot.summary,
        hypothesis_of_pain=snapshot.hypothesis_of_pain,
        best_approach=snapshot.best_approach,
        recommended_product=snapshot.recommended_product,
        timing=snapshot.timing,
        risk=snapshot.risk,
        score_explanation=snapshot.score_explanation,
        created_at=snapshot.created_at,
    )


def _get_latest_executive_snapshot(db: Session, company_id: int) -> LeadExecutiveRead:
    snapshot = (
        db.query(LeadSnapshot)
        .filter(LeadSnapshot.company_id == company_id)
        .order_by(LeadSnapshot.created_at.desc())
        .first()
    )
    if not snapshot:
        raise HTTPException(status_code=404, detail='Lead not found')

    if snapshot.executive_payload:
        try:
            payload = json.loads(snapshot.executive_payload)
            payload.setdefault('eixos_de_evidencia', [])
            payload.setdefault('motivos_do_score', [])
            payload.setdefault('qualidade_match', 'desconhecida')
            return LeadExecutiveRead(**payload)
        except (json.JSONDecodeError, ValidationError, TypeError):
            pass

    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail='Company not found')

    signals = db.query(Signal).filter(Signal.company_id == company_id).order_by(Signal.detected_at.desc()).all()
    result = score_company(company, signals)
    return format_executive_lead(company, signals, result)


def _format_dt(value) -> str:
    if value is None:
        return '—'
    return value.strftime('%d/%m/%Y %H:%M')


def _tier_badge_class(tier: str | None) -> str:
    normalized = (tier or '').upper()
    return {
        'A': 'tier-a',
        'B': 'tier-b',
        'C': 'tier-c',
    }.get(normalized, 'tier-d')


@router.get('/', response_class=HTMLResponse)
def home(
    limit: int = Query(default=12, ge=1, le=50),
    min_score: float | None = Query(default=None, ge=0, le=100),
    tier: str | None = Query(default=None),
    sector: str | None = Query(default=None),
    match_quality: str | None = Query(default=None),
    company_query: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    seed_sources(db)
    ranking = rank_latest_leads(
        db,
        limit=limit,
        min_score=min_score,
        tier=tier,
        sector=sector,
        match_quality=match_quality,
        company_query=company_query,
    )

    total_companies = db.query(func.count(Company.id)).scalar() or 0
    total_signals = db.query(func.count(Signal.id)).scalar() or 0
    active_watchlists = db.query(func.count(Watchlist.id)).filter(Watchlist.active.is_(True)).scalar() or 0
    latest_snapshot = db.query(LeadSnapshot).order_by(LeadSnapshot.created_at.desc()).first()
    top_score = max((item.score for item in ranking.items), default=0)

    sectors = [
        value for (value,) in db.query(Company.sector).filter(Company.sector.isnot(None)).distinct().order_by(Company.sector.asc()).all()
        if value
    ]
    tiers = ['A', 'B', 'C', 'D']
    match_options = ['alta', 'media', 'baixa', 'desconhecida']

    def selected(value: str | None, current: str | None) -> str:
        return ' selected' if (value or '') == (current or '') else ''

    tier_options = ''.join([f"<option value=\"\"{selected('', tier)}>Todos</option>"] + [
        f"<option value=\"{item}\"{selected(item, tier)}>{item}</option>" for item in tiers
    ])
    sector_options = ''.join([f"<option value=\"\"{selected('', sector)}>Todos</option>"] + [
        f"<option value=\"{escape(item)}\"{selected(item, sector)}>{escape(item)}</option>" for item in sectors
    ])
    match_options_html = ''.join([f"<option value=\"\"{selected('', match_quality)}>Todos</option>"] + [
        f"<option value=\"{item}\"{selected(item, match_quality)}>{item.title()}</option>" for item in match_options
    ])

    rows = []
    for item in ranking.items:
        company_name = escape(item.empresa)
        sector_label = escape(item.setor or '—')
        localizacao = escape(item.localizacao or '—')
        match_label = escape((item.qualidade_match or 'desconhecida').title())
        fontes = ''.join(f'<span class="chip subtle">{escape(source)}</span>' for source in item.fontes_utilizadas[:4]) or '<span class="muted">—</span>'
        sinais = ''.join(f'<li>{escape(signal)}</li>' for signal in item.principais_sinais_detectados[:3]) or '<li class="muted">Sem sinais destacados</li>'
        detail_href = f"/leads/{item.company_id}/executive/export?format=json"
        rows.append(
            f"""
            <tr>
              <td>
                <div class=\"company-cell\"> 
                  <strong>{company_name}</strong>
                  <span class=\"muted\">#{item.company_id} · {sector_label}</span>
                </div>
              </td>
              <td><span class=\"score-pill\">{item.score:.1f}</span></td>
              <td><span class=\"badge {_tier_badge_class(item.lead_tier)}\">Tier {escape(item.lead_tier)}</span></td>
              <td><span class=\"badge badge-match\">{match_label}</span></td>
              <td>{escape(item.probabilidade_conversao)}</td>
              <td>{escape(item.produto_mais_indicado)}</td>
              <td><div class=\"chips\">{fontes}</div></td>
              <td><ul class=\"signal-list\">{sinais}</ul></td>
              <td>{localizacao}</td>
              <td>{_format_dt(item.atualizado_em)}</td>
              <td><a class=\"table-link\" href=\"{detail_href}\">Exportar JSON</a></td>
            </tr>
            """
        )

    query_params = urlencode({
        key: value for key, value in {
            'limit': limit,
            'min_score': min_score,
            'tier': tier,
            'sector': sector,
            'match_quality': match_quality,
            'company_query': company_query,
        }.items() if value not in (None, '')
    })
    export_json_href = f"/leads/ranking/export?format=json&{query_params}" if query_params else '/leads/ranking/export?format=json'
    export_csv_href = f"/leads/ranking/export?format=csv&{query_params}" if query_params else '/leads/ranking/export?format=csv'

    html = f"""
    <!doctype html>
    <html lang=\"pt-BR\">
      <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>Leadfind · Executive Radar</title>
        <style>
          :root {{ color-scheme: dark; --bg:#07111f; --panel:#0d1728; --panel-2:#13213a; --line:rgba(148,163,184,.18); --text:#e5eefb; --muted:#8ba0bf; --cyan:#55d6ff; --green:#46d39a; --yellow:#f5c451; --red:#ff7b7b; --shadow:0 24px 80px rgba(0,0,0,.35); }}
          * {{ box-sizing:border-box; }}
          body {{ margin:0; font-family:Inter, ui-sans-serif, system-ui, -apple-system, sans-serif; background:radial-gradient(circle at top, #123055 0%, var(--bg) 48%); color:var(--text); }}
          a {{ color:inherit; text-decoration:none; }}
          .shell {{ max-width: 1480px; margin: 0 auto; padding: 32px 24px 56px; }}
          .hero {{ display:flex; justify-content:space-between; gap:24px; align-items:flex-start; padding:28px; border:1px solid var(--line); border-radius:28px; background:linear-gradient(135deg, rgba(85,214,255,.16), rgba(19,33,58,.9)); box-shadow:var(--shadow); }}
          .hero h1 {{ margin:0 0 10px; font-size:clamp(2rem, 3vw, 3.4rem); line-height:1.02; }}
          .hero p {{ margin:0; max-width:780px; color:var(--muted); font-size:1rem; line-height:1.6; }}
          .hero-actions {{ display:flex; gap:12px; flex-wrap:wrap; justify-content:flex-end; }}
          .button {{ display:inline-flex; align-items:center; justify-content:center; padding:12px 16px; border-radius:14px; border:1px solid var(--line); background:rgba(13,23,40,.8); color:var(--text); font-weight:600; }}
          .button.primary {{ background:linear-gradient(135deg, #19b9ff, #2176ff); border-color:transparent; }}
          .stats {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px; margin:22px 0; }}
          .card {{ padding:20px; border-radius:22px; background:rgba(13,23,40,.92); border:1px solid var(--line); box-shadow:var(--shadow); }}
          .kpi-label {{ display:block; font-size:.8rem; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); margin-bottom:10px; }}
          .kpi-value {{ font-size:2.1rem; font-weight:800; }}
          .kpi-foot {{ margin-top:10px; color:var(--muted); font-size:.92rem; }}
          .layout {{ display:grid; grid-template-columns: minmax(0, 1.9fr) minmax(320px, .9fr); gap:18px; align-items:start; }}
          .toolbar {{ display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:12px; margin-bottom:18px; }}
          label {{ display:flex; flex-direction:column; gap:8px; font-size:.85rem; color:var(--muted); }}
          input, select {{ width:100%; border:1px solid var(--line); border-radius:14px; background:rgba(7,17,31,.88); color:var(--text); padding:12px 14px; outline:none; }}
          .toolbar-actions {{ display:flex; gap:10px; align-items:flex-end; }}
          .table-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:22px; background:rgba(13,23,40,.96); }}
          table {{ width:100%; border-collapse:collapse; min-width:1180px; }}
          thead th {{ position:sticky; top:0; z-index:1; background:#122033; color:#9fb5d5; text-align:left; font-size:.78rem; letter-spacing:.05em; text-transform:uppercase; padding:14px 16px; border-bottom:1px solid var(--line); }}
          tbody td {{ padding:16px; border-bottom:1px solid rgba(148,163,184,.08); vertical-align:top; }}
          tbody tr:nth-child(even) {{ background:rgba(255,255,255,.018); }}
          tbody tr:hover {{ background:rgba(85,214,255,.06); }}
          .company-cell {{ display:flex; flex-direction:column; gap:4px; }}
          .muted {{ color:var(--muted); }}
          .score-pill {{ display:inline-flex; min-width:64px; justify-content:center; padding:8px 12px; border-radius:999px; background:rgba(70,211,154,.14); border:1px solid rgba(70,211,154,.3); color:#bdf6dd; font-weight:800; }}
          .badge {{ display:inline-flex; padding:7px 10px; border-radius:999px; font-size:.82rem; font-weight:700; }}
          .tier-a {{ background:rgba(70,211,154,.16); color:#bdf6dd; }} .tier-b {{ background:rgba(85,214,255,.14); color:#b6efff; }} .tier-c {{ background:rgba(245,196,81,.14); color:#ffe6a5; }} .tier-d {{ background:rgba(255,123,123,.14); color:#ffc1c1; }}
          .badge-match {{ background:rgba(139,160,191,.12); color:#d9e7f8; }}
          .chips {{ display:flex; gap:8px; flex-wrap:wrap; }}
          .chip {{ padding:6px 10px; border-radius:999px; background:rgba(85,214,255,.12); color:#b9f1ff; font-size:.78rem; }}
          .chip.subtle {{ background:rgba(139,160,191,.12); color:#dce8f8; }}
          .signal-list {{ margin:0; padding-left:18px; color:#d6e1f0; display:grid; gap:6px; }}
          .table-link {{ color:#8ddcff; font-weight:700; }}
          .side-stack {{ display:grid; gap:18px; }}
          .side-card h3, .main-card h2 {{ margin:0 0 14px; font-size:1.05rem; }}
          .side-card p, .side-card li {{ color:var(--muted); line-height:1.55; }}
          .list-clean {{ list-style:none; padding:0; margin:0; display:grid; gap:12px; }}
          .list-clean li {{ padding:12px 0; border-bottom:1px solid rgba(148,163,184,.09); }}
          .list-clean li:last-child {{ border-bottom:0; padding-bottom:0; }}
          .mini-title {{ display:block; color:var(--text); font-weight:700; margin-bottom:4px; }}
          @media (max-width: 1180px) {{ .stats, .toolbar, .layout {{ grid-template-columns:1fr 1fr; }} .layout {{ grid-template-columns:1fr; }} .hero {{ flex-direction:column; }} .hero-actions {{ justify-content:flex-start; }} }}
          @media (max-width: 720px) {{ .shell {{ padding:18px 14px 34px; }} .stats, .toolbar {{ grid-template-columns:1fr; }} .toolbar-actions {{ flex-direction:column; align-items:stretch; }} .button {{ width:100%; }} }}
        </style>
      </head>
      <body>
        <div class=\"shell\">
          <section class=\"hero\">
            <div>
              <span class=\"chip\">Executive lead intelligence</span>
              <h1>Leadfind Radar</h1>
              <p>Painel executivo para discovery, priorização e operação de watchlists. Leitura rápida de score, tier, qualidade de match, sinais e fontes em uma interface decente — em vez de parecer debug em produção.</p>
            </div>
            <div class=\"hero-actions\">
              <a class=\"button primary\" href=\"/docs\">Abrir API Docs</a>
              <a class=\"button\" href=\"{export_csv_href}\">Exportar CSV</a>
              <a class=\"button\" href=\"{export_json_href}\">Exportar JSON</a>
            </div>
          </section>

          <section class=\"stats\">
            <article class=\"card\"><span class=\"kpi-label\">Empresas mapeadas</span><div class=\"kpi-value\">{total_companies}</div><div class=\"kpi-foot\">Base consolidada para geração de lead.</div></article>
            <article class=\"card\"><span class=\"kpi-label\">Sinais capturados</span><div class=\"kpi-value\">{total_signals}</div><div class=\"kpi-foot\">Evidências úteis para score e abordagem.</div></article>
            <article class=\"card\"><span class=\"kpi-label\">Top score atual</span><div class=\"kpi-value\">{top_score:.1f}</div><div class=\"kpi-foot\">Melhor oportunidade dentro do recorte atual.</div></article>
            <article class=\"card\"><span class=\"kpi-label\">Watchlists ativas</span><div class=\"kpi-value\">{active_watchlists}</div><div class=\"kpi-foot\">Último snapshot: {_format_dt(latest_snapshot.created_at if latest_snapshot else None)}</div></article>
          </section>

          <div class=\"layout\">
            <section class=\"main-card\">
              <form class=\"card\" method=\"get\">
                <h2>Ranking executivo</h2>
                <div class=\"toolbar\">
                  <label>Empresa<input type=\"text\" name=\"company_query\" value=\"{escape(company_query or '')}\" placeholder=\"Buscar por nome\" /></label>
                  <label>Score mínimo<input type=\"number\" name=\"min_score\" min=\"0\" max=\"100\" step=\"1\" value=\"{'' if min_score is None else min_score}\" placeholder=\"0-100\" /></label>
                  <label>Tier<select name=\"tier\">{tier_options}</select></label>
                  <label>Setor<select name=\"sector\">{sector_options}</select></label>
                  <label>Qualidade do match<select name=\"match_quality\">{match_options_html}</select></label>
                  <label>Limite<input type=\"number\" name=\"limit\" min=\"1\" max=\"50\" value=\"{limit}\" /></label>
                </div>
                <div class=\"toolbar-actions\">
                  <button class=\"button primary\" type=\"submit\">Aplicar filtros</button>
                  <a class=\"button\" href=\"/\">Limpar</a>
                </div>
              </form>

              <div class=\"table-wrap\">
                <table>
                  <thead>
                    <tr>
                      <th>Empresa</th><th>Score</th><th>Tier</th><th>Match</th><th>Conversão</th><th>Produto</th><th>Fontes</th><th>Sinais</th><th>Localização</th><th>Atualizado</th><th>Ação</th>
                    </tr>
                  </thead>
                  <tbody>
                    {''.join(rows) if rows else '<tr><td colspan="11" class="muted">Nenhum lead encontrado para esse recorte.</td></tr>'}
                  </tbody>
                </table>
              </div>
            </section>

            <aside class=\"side-stack\">
              <section class=\"card side-card\">
                <h3>Discovery</h3>
                <p>O fluxo de discovery continua pela API. Use os providers para puxar vagas, notícias, jurídico, reputação e fontes formais; depois gere os leads e volte aqui para priorizar.</p>
                <div class=\"chips\">
                  <span class=\"chip\">Jobs</span><span class=\"chip\">News</span><span class=\"chip\">Legal</span><span class=\"chip\">Reputation</span><span class=\"chip\">Formal acts</span><span class=\"chip\">Serasa</span>
                </div>
              </section>
              <section class=\"card side-card\">
                <h3>Fontes e operação</h3>
                <ul class=\"list-clean\">
                  <li><span class=\"mini-title\">/sources</span> catálogo das fontes com confiabilidade.</li>
                  <li><span class=\"mini-title\">/watchlists</span> automação recorrente para ingestão.</li>
                  <li><span class=\"mini-title\">/webhooks</span> entrega outbound dos leads qualificados.</li>
                </ul>
              </section>
              <section class=\"card side-card\">
                <h3>Leitura rápida</h3>
                <ul class=\"list-clean\">
                  <li><span class=\"mini-title\">Score</span> mede urgência/oportunidade consolidada.</li>
                  <li><span class=\"mini-title\">Tier</span> facilita corte executivo e SLA comercial.</li>
                  <li><span class=\"mini-title\">Qualidade do match</span> evita falso positivo travestido de lead quente.</li>
                </ul>
              </section>
            </aside>
          </div>
        </div>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.get('/health')
def health(db: Session = Depends(get_db)):
    seed_sources(db)
    return {'status': 'ok', 'service': 'leadfind'}


@router.get('/sources', response_model=list[SourceRead])
def list_sources(db: Session = Depends(get_db)):
    seed_sources(db)
    return db.query(Source).order_by(Source.name.asc()).all()


@router.post('/discovery/run', response_model=DiscoveryRunResponse)
def run_discovery_route(payload: DiscoveryRunRequest, db: Session = Depends(get_db)):
    try:
        return run_discovery(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/leads/ranking', response_model=LeadRankingResponse)
def get_leads_ranking(
    limit: int = Query(default=20, ge=1, le=100),
    min_score: float | None = Query(default=None, ge=0, le=100),
    tier: str | None = Query(default=None),
    sector: str | None = Query(default=None),
    match_quality: str | None = Query(default=None),
    company_query: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return rank_latest_leads(
        db,
        limit=limit,
        min_score=min_score,
        tier=tier,
        sector=sector,
        match_quality=match_quality,
        company_query=company_query,
    )


@router.get('/leads/ranking/export')
def export_leads_ranking(
    format: str = Query(default='json', pattern='^(json|csv)$'),
    limit: int = Query(default=20, ge=1, le=100),
    min_score: float | None = Query(default=None, ge=0, le=100),
    tier: str | None = Query(default=None),
    sector: str | None = Query(default=None),
    match_quality: str | None = Query(default=None),
    company_query: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    ranking = rank_latest_leads(
        db,
        limit=limit,
        min_score=min_score,
        tier=tier,
        sector=sector,
        match_quality=match_quality,
        company_query=company_query,
    )
    if format == 'csv':
        return Response(
            content=ranking_to_csv_bytes(ranking),
            media_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename=lead-ranking.csv'},
        )
    return Response(
        content=ranking_to_json_bytes(ranking),
        media_type='application/json',
        headers={'Content-Disposition': 'attachment; filename=lead-ranking.json'},
    )


@router.get('/watchlists', response_model=list[WatchlistRead])
def get_watchlists(active_only: bool = Query(default=False), db: Session = Depends(get_db)):
    return list_watchlists(db, active_only=active_only)


@router.get('/watchlists/{watchlist_id}/runs', response_model=list[WatchlistRunLogRead])
def get_watchlist_runs(watchlist_id: int, db: Session = Depends(get_db)):
    watchlist = db.get(Watchlist, watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail='Watchlist not found')
    return list_watchlist_runs(db, watchlist_id)


@router.post('/watchlists', response_model=WatchlistRead)
def create_watchlist_route(payload: WatchlistCreate, db: Session = Depends(get_db)):
    return create_watchlist(db, payload)


@router.post('/watchlists/run-due', response_model=WatchlistSchedulerRunResponse)
def run_due_watchlists_route(db: Session = Depends(get_db)):
    return run_due_watchlists(db)


@router.post('/watchlists/{watchlist_id}/run', response_model=WatchlistRunResult)
def run_watchlist_route(watchlist_id: int, db: Session = Depends(get_db)):
    watchlist = db.get(Watchlist, watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail='Watchlist not found')
    try:
        return run_watchlist(db, watchlist)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/webhooks', response_model=list[WebhookTargetRead])
def get_webhook_targets(active_only: bool = Query(default=False), db: Session = Depends(get_db)):
    return list_webhook_targets(db, active_only=active_only)


@router.get('/webhooks/{target_id}/deliveries', response_model=list[WebhookDeliveryRead])
def get_webhook_deliveries(target_id: int, db: Session = Depends(get_db)):
    target = db.get(WebhookTarget, target_id)
    if not target:
        raise HTTPException(status_code=404, detail='Webhook target not found')
    return list_webhook_deliveries(db, target_id)


@router.post('/webhooks', response_model=WebhookTargetRead)
def create_webhook_target_route(payload: WebhookTargetCreate, db: Session = Depends(get_db)):
    return create_webhook_target(db, payload)


@router.post('/webhooks/{target_id}/dispatch-latest', response_model=list[WebhookDeliveryRead])
def dispatch_latest_to_webhook(target_id: int, limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)):
    target = db.get(WebhookTarget, target_id)
    if not target:
        raise HTTPException(status_code=404, detail='Webhook target not found')
    return dispatch_latest_leads(db, target, limit=limit)


@router.post('/webhooks/{target_id}/dispatch/{company_id}', response_model=WebhookDeliveryRead)
def dispatch_company_to_webhook(target_id: int, company_id: int, db: Session = Depends(get_db)):
    target = db.get(WebhookTarget, target_id)
    if not target:
        raise HTTPException(status_code=404, detail='Webhook target not found')

    snapshot = (
        db.query(LeadSnapshot)
        .filter(LeadSnapshot.company_id == company_id)
        .order_by(LeadSnapshot.created_at.desc())
        .first()
    )
    if not snapshot:
        raise HTTPException(status_code=404, detail='Lead snapshot not found')
    return deliver_lead_snapshot(db, target, snapshot)


@router.post('/companies', response_model=CompanyRead)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    data = to_db_payload(payload.model_dump(mode='python'))
    aliases = data.pop('aliases', [])
    domains = data.pop('domains', [])
    data['aliases_json'] = json.dumps(aliases, ensure_ascii=False)
    data['domains_json'] = json.dumps(domains, ensure_ascii=False)
    company = Company(**data)
    db.add(company)
    db.commit()
    db.refresh(company)
    return _build_company_read(company)


@router.post('/companies/match', response_model=CompanyRead | None)
def resolve_company_match(payload: CompanyMatchRequest, db: Session = Depends(get_db)):
    company = match_company(
        db,
        company_name=payload.company_name,
        website=str(payload.website) if payload.website else None,
        city=payload.city,
        state=payload.state,
        cnpj_root=payload.cnpj_root,
    )
    return _build_company_read(company) if company else None


@router.post('/signals', response_model=SignalRead)
def create_signal(payload: SignalCreate, db: Session = Depends(get_db)):
    company = db.get(Company, payload.company_id)
    if not company:
        raise HTTPException(status_code=404, detail='Company not found')
    data = to_db_payload(payload.model_dump(mode='python'))
    signal = Signal(**data)
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return signal


@router.post('/raw-events', response_model=RawEventRead)
def create_raw_event(payload: RawEventCreate, db: Session = Depends(get_db)):
    seed_sources(db)
    source = db.query(Source).filter(Source.name == payload.source_name).first()
    if not source:
        raise HTTPException(status_code=404, detail='Source not found')

    if payload.external_id:
        existing = (
            db.query(RawEvent)
            .filter(RawEvent.source_id == source.id, RawEvent.external_id == payload.external_id)
            .first()
        )
        if existing:
            return existing

    data = to_db_payload(payload.model_dump(mode='python'))
    data.pop('source_name')
    raw_event = RawEvent(source_id=source.id, **data)
    db.add(raw_event)
    db.commit()
    db.refresh(raw_event)
    return raw_event


@router.post('/raw-events/batch', response_model=list[RawEventRead])
def create_raw_events_batch(payload: RawEventBatchCreate, db: Session = Depends(get_db)):
    try:
        return ingest_raw_events(db, payload.events, normalize_after_insert=payload.normalize_after_insert)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/raw-events/{raw_event_id}/normalize', response_model=RawEventRead)
def normalize_event(raw_event_id: int, db: Session = Depends(get_db)):
    raw_event = db.get(RawEvent, raw_event_id)
    if not raw_event:
        raise HTTPException(status_code=404, detail='Raw event not found')
    return normalize_raw_event(db, raw_event)


@router.post('/providers/generic-html-jobs/collect', response_model=list[RawEventRead])
def collect_jobs_from_generic_html(payload: GenericHtmlJobsCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_generic_html_jobs(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/providers/gupy-jobs/collect', response_model=list[RawEventRead])
def collect_jobs_from_gupy(payload: GupyJobsCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_gupy_jobs(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/providers/greenhouse-jobs/collect', response_model=list[RawEventRead])
def collect_jobs_from_greenhouse(payload: GreenhouseJobsCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_greenhouse_jobs(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/providers/lever-jobs/collect', response_model=list[RawEventRead])
def collect_jobs_from_lever(payload: LeverJobsCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_lever_jobs(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/providers/workday-jobs/collect', response_model=list[RawEventRead])
def collect_jobs_from_workday(payload: WorkdayJobsCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_workday_jobs(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/providers/json-jobs/collect', response_model=list[RawEventRead])
def collect_jobs_from_json(payload: JsonJobsCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_json_jobs(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/providers/jsonld-jobs/collect', response_model=list[RawEventRead])
def collect_jobs_from_jsonld(payload: JsonLdJobsCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_jsonld_jobs(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/providers/generic-html-news/collect', response_model=list[RawEventRead])
def collect_news_from_generic_html(payload: GenericHtmlNewsCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_generic_html_news(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/providers/regional-news/collect', response_model=list[RawEventRead])
def collect_regional_news(payload: RegionalNewsCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_regional_news_like(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/providers/generic-html-legal/collect', response_model=list[RawEventRead])
def collect_legal_from_generic_html(payload: GenericHtmlLegalCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_generic_html_legal(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/providers/jusbrasil/collect', response_model=list[RawEventRead])
def collect_jusbrasil(payload: JusBrasilCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_jusbrasil_like(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/providers/formal-acts/collect', response_model=list[RawEventRead])
def collect_formal_acts(payload: FormalActsCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_formal_acts_like(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/providers/generic-html-reputation/collect', response_model=list[RawEventRead])
def collect_reputation_from_generic_html(payload: GenericHtmlReputationCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_generic_html_reputation(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/providers/reclame-aqui/collect', response_model=list[RawEventRead])
def collect_reclame_aqui(payload: ReclameAquiCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_reclame_aqui_like(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/providers/serasa/collect', response_model=list[RawEventRead])
def collect_serasa(payload: SerasaCollectRequest, db: Session = Depends(get_db)):
    try:
        return collect_serasa_like(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/leads/generate/{company_id}', response_model=LeadRead)
def generate_lead(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail='Company not found')
    snapshot = generate_lead_snapshot(db, company_id)
    return _build_lead_read(snapshot)


@router.get('/leads/{company_id}', response_model=list[LeadRead])
def list_leads(company_id: int, db: Session = Depends(get_db)):
    snapshots = (
        db.query(LeadSnapshot)
        .filter(LeadSnapshot.company_id == company_id)
        .order_by(LeadSnapshot.created_at.desc())
        .all()
    )
    return [_build_lead_read(snapshot) for snapshot in snapshots]


@router.get('/leads/{company_id}/executive', response_model=LeadExecutiveRead)
def get_latest_executive_lead(company_id: int, db: Session = Depends(get_db)):
    return _get_latest_executive_snapshot(db, company_id)


@router.get('/leads/{company_id}/executive/export')
def export_executive_lead(
    company_id: int,
    format: str = Query(default='json', pattern='^(json|csv)$'),
    db: Session = Depends(get_db),
):
    lead = _get_latest_executive_snapshot(db, company_id)
    if format == 'csv':
        return Response(
            content=executive_lead_to_csv_bytes(lead),
            media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename=lead-{company_id}.csv'},
        )
    return Response(
        content=executive_lead_to_json_bytes(lead),
        media_type='application/json',
        headers={'Content-Disposition': f'attachment; filename=lead-{company_id}.json'},
    )
