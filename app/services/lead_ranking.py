import json
from collections import OrderedDict

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.models import Company, LeadSnapshot
from app.schemas.lead import LeadExecutiveRead
from app.schemas.ranking import LeadRankingItem, LeadRankingResponse


def _payload_or_none(snapshot: LeadSnapshot) -> LeadExecutiveRead | None:
    if not snapshot.executive_payload:
        return None
    try:
        data = json.loads(snapshot.executive_payload)
        data.setdefault('eixos_de_evidencia', [])
        data.setdefault('motivos_do_score', [])
        data.setdefault('qualidade_match', 'desconhecida')
        return LeadExecutiveRead(**data)
    except (json.JSONDecodeError, ValidationError, TypeError):
        return None


def _to_item(snapshot: LeadSnapshot) -> LeadRankingItem:
    payload = _payload_or_none(snapshot)
    if payload:
        return LeadRankingItem(
            company_id=snapshot.company_id,
            empresa=payload.empresa,
            setor=payload.setor,
            localizacao=payload.localizacao,
            score=snapshot.score,
            probabilidade_conversao=snapshot.conversion_probability,
            lead_tier=snapshot.lead_tier,
            produto_mais_indicado=payload.produto_mais_indicado,
            qualidade_match=payload.qualidade_match,
            fontes_utilizadas=payload.fontes_utilizadas,
            principais_sinais_detectados=payload.principais_sinais_detectados,
            atualizado_em=snapshot.created_at,
        )

    return LeadRankingItem(
        company_id=snapshot.company_id,
        empresa=f'Empresa {snapshot.company_id}',
        setor=None,
        localizacao=None,
        score=snapshot.score,
        probabilidade_conversao=snapshot.conversion_probability,
        lead_tier=snapshot.lead_tier,
        produto_mais_indicado=snapshot.recommended_product,
        qualidade_match='desconhecida',
        fontes_utilizadas=[],
        principais_sinais_detectados=[],
        atualizado_em=snapshot.created_at,
    )


def rank_latest_leads(
    db: Session,
    limit: int = 20,
    min_score: float | None = None,
    tier: str | None = None,
    sector: str | None = None,
    match_quality: str | None = None,
    company_query: str | None = None,
) -> LeadRankingResponse:
    snapshots = db.query(LeadSnapshot).order_by(LeadSnapshot.created_at.desc()).all()

    latest_by_company: OrderedDict[int, LeadSnapshot] = OrderedDict()
    for snapshot in snapshots:
        if snapshot.company_id not in latest_by_company:
            latest_by_company[snapshot.company_id] = snapshot

    normalized_query = (company_query or '').strip().lower()
    normalized_match_quality = (match_quality or '').strip().lower()

    items: list[LeadRankingItem] = []
    for snapshot in latest_by_company.values():
        company = db.get(Company, snapshot.company_id)
        if not company:
            continue
        if min_score is not None and snapshot.score < min_score:
            continue
        if tier and snapshot.lead_tier != tier:
            continue
        if sector and (company.sector or '').lower() != sector.lower():
            continue

        item = _to_item(snapshot)
        if normalized_match_quality and (item.qualidade_match or '').lower() != normalized_match_quality:
            continue
        if normalized_query:
            haystack = ' '.join(filter(None, [item.empresa, item.setor, item.localizacao])).lower()
            if normalized_query not in haystack:
                continue
        items.append(item)

    items.sort(key=lambda item: (item.score, item.atualizado_em), reverse=True)
    items = items[:limit]
    return LeadRankingResponse(total=len(items), items=items)
