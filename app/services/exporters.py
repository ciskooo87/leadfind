import csv
import io
import json

from app.schemas.lead import LeadExecutiveRead
from app.schemas.ranking import LeadRankingResponse


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
