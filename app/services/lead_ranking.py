import json
from collections import OrderedDict

from sqlalchemy.orm import Session

from app.db.models import Company, LeadSnapshot
from app.schemas.lead import LeadExecutiveRead
from app.schemas.ranking import LeadRankingItem, LeadRankingResponse


def _to_item(snapshot: LeadSnapshot) -> LeadRankingItem:
    payload = LeadExecutiveRead(**json.loads(snapshot.executive_payload)) if snapshot.executive_payload else None
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
        qualidade_match=None,
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
) -> LeadRankingResponse:
    snapshots = db.query(LeadSnapshot).order_by(LeadSnapshot.created_at.desc()).all()

    latest_by_company: OrderedDict[int, LeadSnapshot] = OrderedDict()
    for snapshot in snapshots:
        if snapshot.company_id not in latest_by_company:
            latest_by_company[snapshot.company_id] = snapshot

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
        items.append(_to_item(snapshot))

    items.sort(key=lambda item: (item.score, item.atualizado_em), reverse=True)
    items = items[:limit]
    return LeadRankingResponse(total=len(items), items=items)
