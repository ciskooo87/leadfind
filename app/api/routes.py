import json
from html import escape
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Company, LeadSnapshot, RawEvent, Signal, Source, Watchlist, WebhookTarget
from app.schemas.company import CompanyCreate, CompanyMatchRequest, CompanyRead
from app.schemas.discovery import DiscoveryRunRequest, DiscoveryRunResponse
from app.schemas.external_signal import ExternalMarketSignalCreate, ExternalMarketSignalRead
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
from app.schemas.strategy import StrategyAnalysisRequest, StrategyAnalysisResponse
from app.schemas.strategy_run import StrategyAnalysisRunCreate, StrategyAnalysisRunDetail, StrategyAnalysisRunRead
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
    strategy_run_to_json_bytes,
    strategy_run_to_markdown_bytes,
)
from app.services.external_signals import create_external_signal, external_signal_context, list_external_signals
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
from app.services.strategy_engine import MARKET_SIGNALS, analyze_strategy, infer_market_signals
from app.services.strategy_runs import create_strategy_run, get_strategy_run, list_strategy_runs
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
    capital: float = Query(default=2500, ge=0),
    target: float = Query(default=20000, ge=1000),
    hours: float = Query(default=2, gt=0, le=24),
    market_scope: str = Query(default='Brasil + global'),
    profile: str = Query(default='executor solo orientado a ativos'),
    market_signals: list[str] = Query(default=[]),
    db: Session = Depends(get_db),
):
    request = StrategyAnalysisRequest(
        available_capital_brl=capital,
        target_brl=target,
        max_hours_per_day=hours,
        market_scope=market_scope,
        profile=profile,
        market_signals=market_signals,
        external_context=external_signal_context(db),
    )
    analysis = analyze_strategy(request)
    recent_runs = list_strategy_runs(db)[:8]
    external_signals = list_external_signals(db, active_only=True)[:8]
    available_signal_keys = list(MARKET_SIGNALS.keys())
    applied_signals = list(dict.fromkeys((market_signals or []) + infer_market_signals(request)))

    def badge(text: str) -> str:
        return f'<span class="badge">{escape(text)}</span>'

    ideas_html = []
    for item in analysis.ideas:
        status = '<span class="pill bad">eliminar</span>' if item.eliminate_reason else '<span class="pill good">manter</span>'
        note = f'<p class="muted">{escape(item.eliminate_reason)}</p>' if item.eliminate_reason else f'<p class="muted">{escape(item.execution_hint)}</p>'
        ideas_html.append(f"""
        <article class="idea-card">
          <div class="idea-head"><strong>{escape(item.name)}</strong>{status}</div>
          <p>{escape(item.summary)}</p>
          <div class="metric-grid">
            <span>retorno <b>{item.speed_of_return}/10</b></span>
            <span>operação <b>{item.operational_ease}/10</b></span>
            <span>escala <b>{item.scale_potential}/10</b></span>
            <span>risco <b>{item.risk_level}/10</b></span>
            <span>automação <b>{item.automation_fit}/10</b></span>
            <span>chance 20k <b>{item.realistic_20k_score}/10</b></span>
          </div>
          <div class="chips">{badge(item.category)}{badge('nicho oculto' if item.hidden else 'mais visível')}{badge(f'assimetria {item.asymmetry_score}')}</div>
          <p class="why-now">{escape(item.why_now)}</p>
          {note}
        </article>
        """)

    top5_html = []
    for item in analysis.top5:
        top5_html.append(f"""
        <section class="deep-card">
          <div class="deep-rank">Top {item.rank}</div>
          <h3>{escape(item.name)}</h3>
          <p>{escape(item.thesis)}</p>
          <p><b>Onde está o dinheiro:</b> {escape(item.where_the_money_is)}</p>
          <p><b>Como escala:</b> {escape(item.how_to_scale)}</p>
          <div class="split">
            <div>
              <h4>Começo com R$2.500</h4>
              <ul>{''.join(f'<li>{escape(x)}</li>' for x in item.how_to_start_with_2500)}</ul>
              <h4>Estrutura</h4>
              <ul>{''.join(f'<li>{escape(x)}</li>' for x in item.structure_needed)}</ul>
              <h4>Ferramentas</h4>
              <ul>{''.join(f'<li>{escape(x)}</li>' for x in item.tools)}</ul>
            </div>
            <div>
              <h4>Primeiros clientes</h4>
              <ul>{''.join(f'<li>{escape(x)}</li>' for x in item.first_customers)}</ul>
              <h4>Riscos</h4>
              <ul>{''.join(f'<li>{escape(x)}</li>' for x in item.main_risks)}</ul>
              <h4>Redução de risco</h4>
              <ul>{''.join(f'<li>{escape(x)}</li>' for x in item.risk_reduction)}</ul>
            </div>
          </div>
          <div class="forecast">
            <span>30d <b>{escape(item.revenue_30d)}</b></span>
            <span>60d <b>{escape(item.revenue_60d)}</b></span>
            <span>90d <b>{escape(item.revenue_90d)}</b></span>
            <span>180d <b>{escape(item.revenue_180d)}</b></span>
          </div>
          <p><b>Automatizar primeiro:</b> {escape(', '.join(item.automate_first))}</p>
          <p><b>Matar rápido se:</b> {escape(' | '.join(item.kill_fast_if))}</p>
          <p><b>Tempo diário real:</b> {escape(item.daily_time_real)}</p>
        </section>
        """)

    matrix = analysis.matrix
    winner = analysis.winner
    runs_html = ''.join(
        f'<li><a href="/strategy/runs/{run.id}">{escape(run.title)}</a> · {escape(run.winner_name)} · {run.created_at.strftime("%d/%m %H:%M")} · sinais: {escape(", ".join(run.applied_signals) or "nenhum")}</li>'
        for run in recent_runs
    ) or '<li class="muted">Nenhuma análise salva ainda.</li>'
    signal_inputs = ''.join(
        f'<label><input type="checkbox" name="market_signals" value="{key}"{" checked" if key in applied_signals else ""} /> {escape(MARKET_SIGNALS[key].label)}</label>'
        for key in available_signal_keys
    )
    external_signals_html = ''.join(
        f'<li><strong>{escape(item.title)}</strong> · {escape(item.signal_key)} · peso {item.relevance_weight}<br><span class="muted">{escape(item.source_name)} — {escape(item.summary)}</span></li>'
        for item in external_signals
    ) or '<li class="muted">Nenhum sinal externo ativo.</li>'
    html = f"""
    <!doctype html>
    <html lang="pt-BR">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Leadfind · Opportunity Intelligence Engine</title>
        <style>
          :root {{ color-scheme: dark; --bg:#08111f; --panel:#0e1828; --line:rgba(148,163,184,.16); --text:#e9f0fa; --muted:#91a4c0; --cyan:#61dafb; --green:#54d39a; --red:#ff8585; }}
          * {{ box-sizing:border-box; }} body {{ margin:0; font-family:Inter,system-ui,sans-serif; background:radial-gradient(circle at top,#12345b 0%,#08111f 45%); color:var(--text); }}
          .shell {{ max-width:1440px; margin:0 auto; padding:28px 20px 56px; }} .hero,.panel,.idea-card,.deep-card,.matrix-card,.form-card {{ background:rgba(14,24,40,.92); border:1px solid var(--line); border-radius:24px; box-shadow:0 24px 70px rgba(0,0,0,.28); }}
          .hero {{ padding:28px; display:grid; gap:16px; }} .hero h1 {{ margin:0; font-size:clamp(2rem,4vw,4rem); line-height:1; }} .hero p {{ margin:0; color:var(--muted); max-width:980px; line-height:1.6; }}
          .layout-top,.hero-actions,.chips,.forecast,.metric-grid {{ display:flex; gap:10px; flex-wrap:wrap; }} .layout-top {{ align-items:start; justify-content:space-between; }}
          .cta,button {{ display:inline-flex; padding:12px 16px; border-radius:14px; background:linear-gradient(135deg,#1fc8ff,#2a6cff); color:white; font-weight:700; text-decoration:none; border:0; cursor:pointer; }}
          .panel {{ margin-top:18px; padding:22px; }} .section-title {{ margin:0 0 14px; font-size:1.2rem; }} .grid-ideas {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; }} .idea-card,.deep-card,.matrix-card,.form-card {{ padding:18px; }}
          .idea-head {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; margin-bottom:10px; }} .idea-card p,.deep-card p, li,label {{ color:#dbe5f4; line-height:1.55; }} .muted,.why-now {{ color:var(--muted); }}
          .pill {{ display:inline-flex; padding:6px 10px; border-radius:999px; font-size:.78rem; font-weight:700; }} .pill.good {{ background:rgba(84,211,154,.16); color:#c3f7df; }} .pill.bad {{ background:rgba(255,133,133,.16); color:#ffd3d3; }}
          .badge {{ display:inline-flex; padding:6px 10px; border-radius:999px; background:rgba(97,218,251,.12); color:#c7f3ff; font-size:.78rem; }} .metric-grid span,.forecast span {{ border:1px solid var(--line); padding:8px 10px; border-radius:12px; color:var(--muted); }}
          .topbar {{ display:grid; grid-template-columns: minmax(0,1.35fr) minmax(320px,.65fr); gap:18px; }} .top5 {{ display:grid; gap:16px; }} .deep-rank {{ color:#8ccfff; font-size:.85rem; font-weight:800; text-transform:uppercase; letter-spacing:.08em; }}
          .split,.matrix-grid,form {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }} input,textarea {{ width:100%; padding:12px 14px; border-radius:14px; border:1px solid var(--line); background:#0a1424; color:var(--text); }} textarea {{ min-height:84px; resize:vertical; }} ul {{ margin:8px 0 14px; padding-left:18px; }} .winner {{ border:1px solid rgba(97,218,251,.24); background:linear-gradient(135deg,rgba(97,218,251,.11),rgba(14,24,40,.95)); }}
          a {{ color:#9adfff; text-decoration:none; }} @media (max-width: 980px) {{ .grid-ideas,.split,.matrix-grid,.topbar,form {{ grid-template-columns:1fr; }} }}
        </style>
      </head>
      <body>
        <div class="shell">
          <section class="hero">
            <div class="chips">{badge('2h por dia')}{badge('R$2.500 → R$20.000')}{badge('ativos + automação + recorrência')}{''.join(badge('sinal: ' + MARKET_SIGNALS[key].label) for key in applied_signals if key in MARKET_SIGNALS)}</div>
            <div class="layout-top"><div><h1>Leadfind pivotado para opportunity intelligence</h1><p>{escape(analysis.framing)}</p><p>Agora com formulário real, histórico salvo e API persistente para analisar teses de negócio em vez de só expor uma resposta estática.</p></div><div class="hero-actions"><a class="cta" href="/docs">Abrir API</a><a class="cta" href="/strategy/ui">Modo análise</a></div></div>
          </section>
          <section class="panel topbar">
            <div class="form-card">
              <h2 class="section-title">Configurar análise</h2>
              <form method="get" action="/strategy/ui">
                <label>Capital disponível (R$)<input name="capital" type="number" step="100" value="{capital}" /></label>
                <label>Meta (R$)<input name="target" type="number" step="1000" value="{target}" /></label>
                <label>Horas por dia<input name="hours" type="number" step="0.5" value="{hours}" /></label>
                <label>Escopo de mercado<input name="market_scope" value="{escape(market_scope)}" /></label>
                <label style="grid-column:1/-1;">Perfil<textarea name="profile">{escape(profile)}</textarea></label>
                <div style="grid-column:1/-1;"><div class="chips">{signal_inputs}</div></div>
                <div><button type="submit">Recalcular</button></div>
              </form>
              <p class="muted">Para persistir via API: <code>POST /strategy/runs</code>.</p>
            </div>
            <div class="form-card">
              <h2 class="section-title">Histórico salvo</h2>
              <ul>{runs_html}</ul>
            </div>
          </section>
          <section class="panel context-grid"><div class="form-card"><h2 class="section-title">Contexto externo ativo</h2><ul>{external_signals_html}</ul></div><div class="form-card"><h2 class="section-title">Adicionar sinal externo</h2><form method="get" action="/strategy/signals/external/add"><label>Signal key<input name="signal_key" value="doc_generation" /></label><label>Título<input name="title" value="Novo sinal" /></label><label>Fonte<input name="source_name" value="manual" /></label><label>URL<input name="source_url" value="https://example.com/signal" /></label><label>Peso<input name="relevance_weight" type="number" min="1" max="10" value="3" /></label><label style="grid-column:1/-1;">Resumo<textarea name="summary">Contexto externo relevante para reordenar a análise.</textarea></label><div><button type="submit">Salvar sinal</button></div></form></div></section>
          <section class="panel"><h2 class="section-title">Parte 1 · 20 oportunidades resumidas</h2><div class="grid-ideas">{''.join(ideas_html)}</div></section>
          <section class="panel"><h2 class="section-title">Parte 2 e 3 · Top 5 com análise profunda</h2><div class="top5">{''.join(top5_html)}</div></section>
          <section class="panel"><h2 class="section-title">Parte 4 · Matriz</h2><div class="matrix-grid"><article class="matrix-card"><h3>Baixo risco + alta escala</h3><ul>{''.join(f'<li>{escape(x)}</li>' for x in matrix.low_risk_high_scale)}</ul></article><article class="matrix-card"><h3>Baixo risco + baixa escala</h3><ul>{''.join(f'<li>{escape(x)}</li>' for x in matrix.low_risk_low_scale)}</ul></article><article class="matrix-card"><h3>Alto risco + alta escala</h3><ul>{''.join(f'<li>{escape(x)}</li>' for x in matrix.high_risk_high_scale)}</ul></article><article class="matrix-card"><h3>Oportunidades escondidas</h3><ul>{''.join(f'<li>{escape(x)}</li>' for x in matrix.hidden_opportunities)}</ul></article></div></section>
          <section class="panel winner"><h2 class="section-title">Parte 5 · Melhor assimetria entre risco, tempo e potencial</h2><h3>{escape(winner.name)}</h3><p><b>Por que vence:</b> {escape(winner.why_it_wins)}</p><p><b>Gargalo real:</b> {escape(winner.real_bottleneck)}</p><p><b>Como operar em 2h/dia:</b> {escape(' | '.join(winner.operating_in_2h))}</p><h4>Por que as outras perdem</h4><ul>{''.join(f'<li>{escape(x)}</li>' for x in winner.why_others_lose)}</ul><h4>Maior chance estatística de funcionar</h4><ul>{''.join(f'<li>{escape(x)}</li>' for x in winner.best_execution_path)}</ul><h4>Onde quase todo mundo erra</h4><ul>{''.join(f'<li>{escape(x)}</li>' for x in winner.common_mistakes)}</ul></section>
        </div>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.get('/strategy/ui', response_class=HTMLResponse)
def strategy_ui(
    capital: float = Query(default=2500, ge=0),
    target: float = Query(default=20000, ge=1000),
    hours: float = Query(default=2, gt=0, le=24),
    market_scope: str = Query(default='Brasil + global'),
    profile: str = Query(default='executor solo orientado a ativos'),
    market_signals: list[str] = Query(default=[]),
    db: Session = Depends(get_db),
):
    return home(capital=capital, target=target, hours=hours, market_scope=market_scope, profile=profile, market_signals=market_signals, db=db)


@router.post('/strategy/analyze', response_model=StrategyAnalysisResponse)
def strategy_analyze(request: StrategyAnalysisRequest, db: Session = Depends(get_db)):
    enriched = request.model_copy(update={'external_context': request.external_context or external_signal_context(db)})
    return analyze_strategy(enriched)


@router.get('/strategy/signals/external', response_model=list[ExternalMarketSignalRead])
def get_external_strategy_signals(active_only: bool = Query(default=False), db: Session = Depends(get_db)):
    return list_external_signals(db, active_only=active_only)


@router.post('/strategy/signals/external', response_model=ExternalMarketSignalRead)
def create_external_strategy_signal(payload: ExternalMarketSignalCreate, db: Session = Depends(get_db)):
    return create_external_signal(db, payload)


@router.get('/strategy/signals/external/add')
def create_external_strategy_signal_form(
    signal_key: str = Query(...),
    title: str = Query(...),
    source_name: str = Query(...),
    source_url: str = Query(default=''),
    summary: str = Query(...),
    relevance_weight: int = Query(default=1, ge=1, le=10),
    db: Session = Depends(get_db),
):
    create_external_signal(
        db,
        ExternalMarketSignalCreate(
            signal_key=signal_key,
            title=title,
            source_name=source_name,
            source_url=source_url or None,
            summary=summary,
            relevance_weight=relevance_weight,
            active=True,
        ),
    )
    return RedirectResponse(url='/strategy/ui', status_code=303)


@router.get('/strategy/runs', response_model=list[StrategyAnalysisRunRead])
def strategy_runs(db: Session = Depends(get_db)):
    return list_strategy_runs(db)


@router.post('/strategy/runs', response_model=StrategyAnalysisRunDetail)
def create_strategy_run_route(payload: StrategyAnalysisRunCreate, db: Session = Depends(get_db)):
    return create_strategy_run(db, payload)


@router.get('/strategy/runs/{run_id}', response_model=StrategyAnalysisRunDetail)
def get_strategy_run_route(run_id: int, db: Session = Depends(get_db)):
    run = get_strategy_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail='Strategy run not found')
    return run


@router.get('/strategy/runs/{run_id}/export')
def export_strategy_run_route(
    run_id: int,
    format: str = Query(default='json', pattern='^(json|md)$'),
    db: Session = Depends(get_db),
):
    run = get_strategy_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail='Strategy run not found')
    if format == 'md':
        return Response(
            content=strategy_run_to_markdown_bytes(run),
            media_type='text/markdown',
            headers={'Content-Disposition': f'attachment; filename=strategy-run-{run_id}.md'},
        )
    return Response(
        content=strategy_run_to_json_bytes(run),
        media_type='application/json',
        headers={'Content-Disposition': f'attachment; filename=strategy-run-{run_id}.json'},
    )


@router.get('/strategy/compare')
def compare_strategy_runs(
    run_ids: list[int] = Query(default=[]),
    db: Session = Depends(get_db),
):
    runs = [run for run_id in run_ids if (run := get_strategy_run(db, run_id))]
    return {
        'items': [
            {
                'id': run.id,
                'title': run.title,
                'winner_name': run.winner_name,
                'capital': run.request.available_capital_brl,
                'target': run.request.target_brl,
                'hours_per_day': run.request.max_hours_per_day,
                'top5': [item.name for item in run.response.top5],
                'best_execution_path': run.response.winner.best_execution_path,
                'created_at': run.created_at,
            }
            for run in runs
        ]
    }


@router.get('/strategy/compare/ui', response_class=HTMLResponse)
def compare_strategy_runs_ui(
    run_ids: list[int] = Query(default=[]),
    db: Session = Depends(get_db),
):
    all_runs = list_strategy_runs(db)
    selected = [run for run_id in run_ids if (run := get_strategy_run(db, run_id))]
    options = ''.join(
        f'<label><input type="checkbox" name="run_ids" value="{run.id}"{" checked" if run.id in run_ids else ""}> #{run.id} · {escape(run.title)} · {escape(run.winner_name)}</label>'
        for run in all_runs[:20]
    ) or '<p class="muted">Nenhuma análise salva.</p>'
    columns = ''.join(
        f"""
        <article class="compare-card">
          <h3>#{run.id} · {escape(run.title)}</h3>
          <p><b>Winner:</b> {escape(run.winner_name)}</p>
          <p><b>Capital:</b> R${run.request.available_capital_brl:,.0f}</p>
          <p><b>Meta:</b> R${run.request.target_brl:,.0f}</p>
          <p><b>Horas/dia:</b> {run.request.max_hours_per_day:g}</p>
          <p><b>Top 5:</b> {escape(' | '.join(item.name for item in run.response.top5))}</p>
          <p><b>Gargalo:</b> {escape(run.response.winner.real_bottleneck)}</p>
          <p><b>Execução:</b> {escape(' | '.join(run.response.winner.best_execution_path))}</p>
          <div class="chips"><a href="/strategy/runs/{run.id}/export?format=json">JSON</a><a href="/strategy/runs/{run.id}/export?format=md">Markdown</a></div>
        </article>
        """
        for run in selected
    ) or '<article class="compare-card"><p class="muted">Selecione 2 ou mais análises para comparar.</p></article>'
    html = f"""
    <!doctype html>
    <html lang="pt-BR"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Leadfind · Comparador</title>
    <style>
    body {{ margin:0; font-family:Inter,system-ui,sans-serif; background:#08111f; color:#e9f0fa; }}
    .shell {{ max-width:1400px; margin:0 auto; padding:24px; }} .panel,.compare-card {{ background:#0e1828; border:1px solid rgba(148,163,184,.16); border-radius:20px; padding:18px; }}
    form,.grid,.chips {{ display:flex; gap:12px; flex-wrap:wrap; }} .grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; align-items:start; }}
    label,a,p {{ color:#dbe5f4; }} a {{ color:#98e2ff; text-decoration:none; }} .muted {{ color:#91a4c0; }} button {{ padding:10px 14px; border:0; border-radius:12px; background:linear-gradient(135deg,#1fc8ff,#2a6cff); color:white; font-weight:700; cursor:pointer; }}
    @media (max-width: 1000px) {{ .grid {{ grid-template-columns:1fr; }} }}
    </style></head><body><div class="shell"><section class="panel"><h1>Comparador de análises</h1><form method="get" action="/strategy/compare/ui">{options}<div style="width:100%;"><button type="submit">Comparar</button></div></form></section><section class="grid" style="margin-top:16px;">{columns}</section></div></body></html>
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
