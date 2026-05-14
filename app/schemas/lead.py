from datetime import datetime
from pydantic import BaseModel


class LeadRead(BaseModel):
    company_id: int
    score: float
    conversion_probability: str
    lead_tier: str
    summary: str
    hypothesis_of_pain: str
    best_approach: str
    recommended_product: str
    timing: str
    risk: str
    score_explanation: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LeadExecutiveRead(BaseModel):
    company_id: int
    empresa: str
    setor: str | None = None
    localizacao: str | None = None
    porte_estimado: str | None = None
    score_necessidade_capital: float
    probabilidade_conversao: str
    score_bucket: str
    qualidade_match: str | None = None
    principais_sinais_detectados: list[str]
    eixos_de_evidencia: list[str]
    motivos_do_score: list[str]
    contexto_operacional: str
    hipotese_de_dor: str
    melhor_abordagem_comercial: str
    produto_mais_indicado: str
    timing_ideal_de_abordagem: str
    risco: str
    contatos_encontrados: list[str]
    fontes_utilizadas: list[str]
    confianca_do_lead: str
    evidencias: list[str]
    resumo_executivo: str
    criado_em: datetime
