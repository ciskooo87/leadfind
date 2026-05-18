import csv
import io
import json

from app.schemas.lead import LeadExecutiveRead
from app.schemas.ranking import LeadRankingResponse
from app.schemas.strategy_run import StrategyAnalysisRunDetail


def ranking_to_csv_bytes(ranking: LeadRankingResponse) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        'company_id',
        'empresa',
        'setor',
        'localizacao',
        'score',
        'probabilidade_conversao',
        'lead_tier',
        'produto_mais_indicado',
        'fontes_utilizadas',
        'principais_sinais_detectados',
        'atualizado_em',
    ])
    for item in ranking.items:
        writer.writerow([
            item.company_id,
            item.empresa,
            item.setor or '',
            item.localizacao or '',
            item.score,
            item.probabilidade_conversao,
            item.lead_tier,
            item.produto_mais_indicado,
            ' | '.join(item.fontes_utilizadas),
            ' | '.join(item.principais_sinais_detectados),
            item.atualizado_em.isoformat(),
        ])
    return buffer.getvalue().encode('utf-8')


def executive_lead_to_csv_bytes(lead: LeadExecutiveRead) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['campo', 'valor'])
    payload = lead.model_dump()
    for key, value in payload.items():
        if isinstance(value, list):
            value = ' | '.join(str(item) for item in value)
        writer.writerow([key, value])
    return buffer.getvalue().encode('utf-8')


def executive_lead_to_json_bytes(lead: LeadExecutiveRead) -> bytes:
    return json.dumps(lead.model_dump(mode='json'), ensure_ascii=False, indent=2).encode('utf-8')


def ranking_to_json_bytes(ranking: LeadRankingResponse) -> bytes:
    return json.dumps(ranking.model_dump(mode='json'), ensure_ascii=False, indent=2).encode('utf-8')


def strategy_run_to_json_bytes(run: StrategyAnalysisRunDetail) -> bytes:
    return json.dumps(run.model_dump(mode='json'), ensure_ascii=False, indent=2).encode('utf-8')


def strategy_run_to_markdown_bytes(run: StrategyAnalysisRunDetail) -> bytes:
    lines = [
        f"# {run.title}",
        '',
        f"- ID: {run.id}",
        f"- Criado em: {run.created_at.isoformat()}",
        f"- Vencedora: {run.winner_name}",
        '',
        '## Request',
        f"- Capital: R${run.request.available_capital_brl:,.0f}".replace(',', '.'),
        f"- Meta: R${run.request.target_brl:,.0f}".replace(',', '.'),
        f"- Horas/dia: {run.request.max_hours_per_day:g}",
        f"- Escopo: {run.request.market_scope}",
        f"- Perfil: {run.request.profile}",
        '',
        '## Framing',
        run.response.framing,
        '',
        '## Top 5',
    ]
    for item in run.response.top5:
        lines.extend([
            f"### Top {item.rank} — {item.name}",
            item.thesis,
            f"- Onde está o dinheiro: {item.where_the_money_is}",
            f"- Como escala: {item.how_to_scale}",
            f"- Receita 30/60/90/180d: {item.revenue_30d} | {item.revenue_60d} | {item.revenue_90d} | {item.revenue_180d}",
            '',
        ])
    lines.extend([
        '## Melhor assimetria',
        f"### {run.response.winner.name}",
        run.response.winner.why_it_wins,
        '',
        '## Plano de implementação',
    ])
    lines.extend([f"- {step}" for step in run.response.implementation_plan])
    return '\n'.join(lines).encode('utf-8')
