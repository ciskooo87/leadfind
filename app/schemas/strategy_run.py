from datetime import datetime

from pydantic import BaseModel

from app.schemas.strategy import StrategyAnalysisRequest, StrategyAnalysisResponse


class StrategyAnalysisRunCreate(BaseModel):
    title: str = 'Análise estratégica'
    request: StrategyAnalysisRequest


class StrategyAnalysisRunRead(BaseModel):
    id: int
    title: str
    winner_name: str
    top_opportunity_names: list[str]
    created_at: datetime


class StrategyAnalysisRunDetail(StrategyAnalysisRunRead):
    request: StrategyAnalysisRequest
    response: StrategyAnalysisResponse
