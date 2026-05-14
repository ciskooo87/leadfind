from collections import OrderedDict

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.schemas.discovery import (
    DiscoveryProviderResult,
    DiscoveryRunRequest,
    DiscoveryRunResponse,
)
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
from app.schemas.serasa import SerasaCollectRequest
from app.services.formal_ingestion import collect_formal_acts_like
from app.services.lead_generation import generate_lead_snapshot
from app.services.lead_ranking import rank_latest_leads
from app.services.legal_ingestion import collect_generic_html_legal, collect_jusbrasil_like
from app.services.news_ingestion import collect_generic_html_news, collect_regional_news_like
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
from app.services.serasa_ingestion import collect_serasa_like


PROVIDER_HANDLERS = {
    'generic_html_jobs': (GenericHtmlJobsCollectRequest, collect_generic_html_jobs),
    'json_jobs': (JsonJobsCollectRequest, collect_json_jobs),
    'jsonld_jobs': (JsonLdJobsCollectRequest, collect_jsonld_jobs),
    'gupy_jobs': (GupyJobsCollectRequest, collect_gupy_jobs),
    'greenhouse_jobs': (GreenhouseJobsCollectRequest, collect_greenhouse_jobs),
    'lever_jobs': (LeverJobsCollectRequest, collect_lever_jobs),
    'workday_jobs': (WorkdayJobsCollectRequest, collect_workday_jobs),
    'generic_html_news': (GenericHtmlNewsCollectRequest, collect_generic_html_news),
    'regional_news': (RegionalNewsCollectRequest, collect_regional_news_like),
    'generic_html_legal': (GenericHtmlLegalCollectRequest, collect_generic_html_legal),
    'jusbrasil': (JusBrasilCollectRequest, collect_jusbrasil_like),
    'generic_html_reputation': (GenericHtmlReputationCollectRequest, collect_generic_html_reputation),
    'reclame_aqui': (ReclameAquiCollectRequest, collect_reclame_aqui_like),
    'formal_acts': (FormalActsCollectRequest, collect_formal_acts_like),
    'serasa': (SerasaCollectRequest, collect_serasa_like),
}


def run_discovery(db: Session, payload: DiscoveryRunRequest) -> DiscoveryRunResponse:
    provider_results: list[DiscoveryProviderResult] = []
    impacted_ids: list[int] = []

    for provider in payload.providers:
        handler_info = PROVIDER_HANDLERS.get(provider.kind)
        if not handler_info:
            raise ValueError(f'Unsupported discovery provider kind: {provider.kind}')

        schema_cls, handler = handler_info
        try:
            schema_payload = schema_cls(**provider.payload)
        except ValidationError as exc:
            raise ValueError(f'Invalid payload for {provider.kind}: {exc}') from exc

        raw_events = handler(db, schema_payload)
        company_ids = [event.company_id for event in raw_events if event.company_id is not None]
        impacted_ids.extend(company_ids)
        provider_results.append(
            DiscoveryProviderResult(
                kind=provider.kind,
                created_events=len(raw_events),
                impacted_company_ids=sorted(set(company_ids)),
                raw_events=raw_events,
            )
        )

    unique_impacted_ids = list(OrderedDict.fromkeys(impacted_ids).keys())
    generated_leads = 0
    if payload.generate_leads:
        for company_id in unique_impacted_ids:
            generate_lead_snapshot(db, company_id)
            generated_leads += 1

    ranking = rank_latest_leads(db, limit=payload.ranking_limit)
    return DiscoveryRunResponse(
        providers=provider_results,
        impacted_company_ids=unique_impacted_ids,
        generated_leads=generated_leads,
        ranking=ranking,
    )
