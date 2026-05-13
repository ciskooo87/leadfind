from sqlalchemy.orm import Session

from app.collectors.html_jobs_provider import fetch_jobs_from_generic_html
from app.collectors.jobs_importer import provider_event_to_raw_event
from app.schemas.provider import GenericHtmlJobsCollectRequest
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
