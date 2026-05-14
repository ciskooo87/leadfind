from sqlalchemy.orm import Session

from app.collectors.greenhouse_jobs_provider import fetch_jobs_from_greenhouse_html
from app.collectors.gupy_jobs_provider import fetch_jobs_from_gupy_html
from app.collectors.html_jobs_provider import fetch_jobs_from_generic_html
from app.collectors.jobs_importer import provider_event_to_raw_event
from app.collectors.json_jobs_provider import fetch_jobs_from_json_feed
from app.collectors.jsonld_jobs_provider import fetch_jobs_from_jsonld
from app.collectors.lever_jobs_provider import fetch_jobs_from_lever_html
from app.schemas.provider import GenericHtmlJobsCollectRequest, JsonJobsCollectRequest, JsonLdJobsCollectRequest
from app.schemas.provider_specific import GreenhouseJobsCollectRequest, GupyJobsCollectRequest, LeverJobsCollectRequest
from app.services.ingestion import ingest_raw_events


def collect_generic_html_jobs(db: Session, payload: GenericHtmlJobsCollectRequest):
    provider_events = fetch_jobs_from_generic_html(
        url=str(payload.url),
        source_name=payload.source_name,
        listing_selector=payload.listing_selector,
        title_selector=payload.title_selector,
        content_selector=payload.content_selector,
        company_selector=payload.company_selector,
        city_selector=payload.city_selector,
        state_selector=payload.state_selector,
        link_selector=payload.link_selector,
        website_selector=payload.website_selector,
        confidence=payload.confidence,
    )
    raw_events = [provider_event_to_raw_event(event) for event in provider_events]
    return ingest_raw_events(db, raw_events, normalize_after_insert=payload.normalize_after_insert)


def collect_json_jobs(db: Session, payload: JsonJobsCollectRequest):
    provider_events = fetch_jobs_from_json_feed(
        url=str(payload.url),
        source_name=payload.source_name,
        items_path=payload.items_path,
        title_path=payload.title_path,
        content_path=payload.content_path,
        company_path=payload.company_path,
        city_path=payload.city_path,
        state_path=payload.state_path,
        link_path=payload.link_path,
        website_path=payload.website_path,
        external_id_path=payload.external_id_path,
        confidence=payload.confidence,
    )
    raw_events = [provider_event_to_raw_event(event) for event in provider_events]
    return ingest_raw_events(db, raw_events, normalize_after_insert=payload.normalize_after_insert)


def collect_jsonld_jobs(db: Session, payload: JsonLdJobsCollectRequest):
    provider_events = fetch_jobs_from_jsonld(
        url=str(payload.url),
        source_name=payload.source_name,
        confidence=payload.confidence,
    )
    raw_events = [provider_event_to_raw_event(event) for event in provider_events]
    return ingest_raw_events(db, raw_events, normalize_after_insert=payload.normalize_after_insert)


def collect_gupy_jobs(db: Session, payload: GupyJobsCollectRequest):
    provider_events = fetch_jobs_from_gupy_html(
        url=str(payload.url),
        source_name=payload.source_name,
        confidence=payload.confidence,
    )
    raw_events = [provider_event_to_raw_event(event) for event in provider_events]
    return ingest_raw_events(db, raw_events, normalize_after_insert=payload.normalize_after_insert)


def collect_greenhouse_jobs(db: Session, payload: GreenhouseJobsCollectRequest):
    provider_events = fetch_jobs_from_greenhouse_html(
        url=str(payload.url),
        source_name=payload.source_name,
        confidence=payload.confidence,
    )
    raw_events = [provider_event_to_raw_event(event) for event in provider_events]
    return ingest_raw_events(db, raw_events, normalize_after_insert=payload.normalize_after_insert)


def collect_lever_jobs(db: Session, payload: LeverJobsCollectRequest):
    provider_events = fetch_jobs_from_lever_html(
        url=str(payload.url),
        source_name=payload.source_name,
        confidence=payload.confidence,
    )
    raw_events = [provider_event_to_raw_event(event) for event in provider_events]
    return ingest_raw_events(db, raw_events, normalize_after_insert=payload.normalize_after_insert)
