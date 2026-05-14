from datetime import datetime
from pydantic import BaseModel


class LeadRankingItem(BaseModel):
    company_id: int
    empresa: str
    setor: str | None = None
    localizacao: str | None = None
    score: float
    probabilidade_conversao: str
    lead_tier: str
    produto_mais_indicado: str
    qualidade_match: str | None = None
    fontes_utilizadas: list[str]
    principais_sinais_detectados: list[str]
    atualizado_em: datetime


class LeadRankingResponse(BaseModel):
    total: int
    items: list[LeadRankingItem]
