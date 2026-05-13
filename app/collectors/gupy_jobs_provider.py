import re

from bs4 import BeautifulSoup

from app.collectors.http_client import fetch_text
from app.collectors.provider_models import ProviderJobEvent
from app.collectors.provider_registry import register_provider


def fetch_jobs_from_gupy_html(url: str, source_name: str = 'Gupy', confidence: float = 0.84) -> list[ProviderJobEvent]:
    html = fetch_text(url)
    soup = BeautifulSoup(html, 'html.parser')
    events: list[ProviderJobEvent] = []

    cards = soup.select('[data-testid="job-list-item"], .job-list__listitem, .sc-')
    if not cards:
        cards = soup.find_all(['a', 'div'], href=True)

    for index, node in enumerate(cards, start=1):
        text = node.get_text(' ', strip=True)
        href = node.get('href') if hasattr(node, 'get') else None
        if not text or not href:
            continue
        if 'vaga' not in text.lower() and len(text.split()) < 3:
            continue
        title = text[:180]
        external_id_match = re.search(r'/jobs/(\d+)', href)
        external_id = external_id_match.group(1) if external_id_match else href
        events.append(ProviderJobEvent(
            source_name=source_name,
            external_id=external_id,
            source_url=href,
            title=title,
            content=text,
            confidence=confidence,
        ))
    return events


register_provider('gupy_jobs', fetch_jobs_from_gupy_html)
