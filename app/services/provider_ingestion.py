from sqlalchemy.orm import Session

from app.collectors.html_jobs_provider import fetch_jobs_from_generic_html
from app.collectors.jobs_importer import provider_event_to_raw_event
from app.collectors.json_jobs_provider import fetch_jobs_from_json_feed
from app.schemas.provider import GenericHtmlJobsCollectRequest, JsonJobsCollectRequest
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
