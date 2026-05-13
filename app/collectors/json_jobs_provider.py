import json

from app.collectors.http_client import fetch_text
from app.collectors.provider_models import ProviderJobEvent
from app.collectors.provider_registry import register_provider


def _extract_path(data: dict, path: str | None):
    if not path:
        return None
    current = data
    for part in path.split('.'):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def fetch_jobs_from_json_feed(
    url: str,
    source_name: str,
    items_path: str,
    title_path: str,
    content_path: str,
    company_path: str | None = None,
    city_path: str | None = None,
    state_path: str | None = None,
    link_path: str | None = None,
    website_path: str | None = None,
    external_id_path: str | None = None,
    confidence: float = 0.78,
) -> list[ProviderJobEvent]:
    raw = fetch_text(url)
    payload = json.loads(raw)

    current = payload
    for part in items_path.split('.'):
        if isinstance(current, dict):
            current = current.get(part, [])
        else:
            current = []
            break

    if not isinstance(current, list):
        return []

    events: list[ProviderJobEvent] = []
    for index, item in enumerate(current, start=1):
        if not isinstance(item, dict):
            continue
        title = _extract_path(item, title_path)
        content = _extract_path(item, content_path)
        if not content:
            continue
        source_url = _extract_path(item, link_path)
        external_id = _extract_path(item, external_id_path) or source_url or f"{source_name.lower().replace(' ', '-')}-{index}"
        events.append(
            ProviderJobEvent(
                source_name=source_name,
                external_id=str(external_id) if external_id else None,
                source_url=str(source_url) if source_url else None,
                title=str(title) if title else None,
                content=str(content),
                company_name_raw=str(_extract_path(item, company_path)) if company_path and _extract_path(item, company_path) else None,
                company_website_raw=str(_extract_path(item, website_path)) if website_path and _extract_path(item, website_path) else None,
                city_raw=str(_extract_path(item, city_path)) if city_path and _extract_path(item, city_path) else None,
                state_raw=str(_extract_path(item, state_path)) if state_path and _extract_path(item, state_path) else None,
                confidence=confidence,
            )
        )
    return events


register_provider("json_jobs_feed", fetch_jobs_from_json_feed)
