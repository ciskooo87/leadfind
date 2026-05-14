from pydantic import BaseModel

from app.schemas.formal import FormalActsCollectRequest
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
from app.schemas.reputation import GenericHtmlReputationCollectRequest
from app.schemas.reputation_specific import ReclameAquiCollectRequest
from app.schemas.ranking import LeadRankingResponse
from app.schemas.raw_event import RawEventRead
from app.schemas.serasa import SerasaCollectRequest


class DiscoveryProviderRun(BaseModel):
    kind: str
    payload: dict


class DiscoveryRunRequest(BaseModel):
    providers: list[DiscoveryProviderRun]
    generate_leads: bool = True
    ranking_limit: int = 20


class DiscoveryProviderResult(BaseModel):
    kind: str
    created_events: int
    impacted_company_ids: list[int]
    raw_events: list[RawEventRead]


class DiscoveryRunResponse(BaseModel):
    providers: list[DiscoveryProviderResult]
    impacted_company_ids: list[int]
    generated_leads: int
    ranking: LeadRankingResponse
