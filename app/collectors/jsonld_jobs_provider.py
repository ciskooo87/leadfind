import json
from collections.abc import Iterable

from bs4 import BeautifulSoup

from app.collectors.http_client import fetch_text
from app.collectors.provider_models import ProviderJobEvent
from app.collectors.provider_registry import register_provider


def _ensure_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _extract_jobposting_nodes(payload) -> Iterable[dict]:
    if isinstance(payload, dict):
        payload_type = payload.get('@type')
        if payload_type == 'JobPosting':
            yield payload
        for key in ('@graph', 'graph', 'itemListElement'):
            nested = payload.get(key)
            for item in _ensure_list(nested):
                yield from _extract_jobposting_nodes(item)
    elif isinstance(payload, list):
        for item in payload:
            yield from _extract_jobposting_nodes(item)


def _text(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, dict):
        return value.get('name') or value.get('value')
    return str(value).strip() or None


def fetch_jobs_from_jsonld(url: str, source_name: str = 'Corporate Careers', confidence: float = 0.84) -> list[ProviderJobEvent]:
    html = fetch_text(url)
    soup = BeautifulSoup(html, 'html.parser')
    events: list[ProviderJobEvent] = []

    for index, script in enumerate(soup.select('script[type="application/ld+json"]'), start=1):
        raw = script.string or script.get_text('\n', strip=True)
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue

        for job_index, node in enumerate(_extract_jobposting_nodes(payload), start=1):
            hiring_org = node.get('hiringOrganization') or {}
            job_location = node.get('jobLocation') or {}
            address = job_location.get('address') if isinstance(job_location, dict) else {}
            city = _text(address.get('addressLocality')) if isinstance(address, dict) else None
            state = _text(address.get('addressRegion')) if isinstance(address, dict) else None
            description = _text(node.get('description'))
            if not description:
                continue

            source_url = _text(node.get('url')) or url
            external_id = _text(node.get('identifier')) or f'jsonld-{index}-{job_index}'
            events.append(
                ProviderJobEvent(
                    source_name=source_name,
                    external_id=external_id,
                    source_url=source_url,
                    title=_text(node.get('title')),
                    content=description,
                    company_name_raw=_text(hiring_org.get('name')) if isinstance(hiring_org, dict) else None,
                    company_website_raw=_text(hiring_org.get('sameAs')) if isinstance(hiring_org, dict) else None,
                    city_raw=city,
                    state_raw=state,
                    confidence=confidence,
                )
            )

    return events


register_provider('jsonld_jobs', fetch_jobs_from_jsonld)
