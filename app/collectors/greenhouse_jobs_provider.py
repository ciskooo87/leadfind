import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.collectors.http_client import fetch_text
from app.collectors.provider_models import ProviderJobEvent
from app.collectors.provider_registry import register_provider


def _absolute_url(base_url: str, href: str | None) -> str | None:
    if not href:
        return None
    return urljoin(base_url, href)


def _extract_company_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.lower().replace('www.', '')
    path_parts = [part for part in parsed.path.split('/') if part]
    if path_parts:
        first = path_parts[0].strip()
        if first and first not in {'jobs', 'boards', 'job-boards'}:
            return first.replace('-', ' ') or None
    if not host:
        return None
    subdomain = host.split('.')[0]
    if subdomain in {'boards', 'job-boards', 'jobs'}:
        return None
    return subdomain.replace('-', ' ').strip() or None


def fetch_jobs_from_greenhouse_html(url: str, source_name: str = 'Greenhouse', confidence: float = 0.85) -> list[ProviderJobEvent]:
    html = fetch_text(url)
    soup = BeautifulSoup(html, 'html.parser')
    events: list[ProviderJobEvent] = []
    seen_urls: set[str] = set()

    selectors = [
        'section.opening a',
        '.opening a',
        'a[href*="/jobs/"]',
    ]

    for selector in selectors:
        for node in soup.select(selector):
            href = _absolute_url(url, node.get('href') if hasattr(node, 'get') else None)
            text = node.get_text(' ', strip=True)
            if not href or not text or href in seen_urls:
                continue
            seen_urls.add(href)
            location_node = node.find_next(['span', 'div'], class_=re.compile('location', re.I)) if hasattr(node, 'find_next') else None
            location_text = location_node.get_text(' ', strip=True) if location_node else ''
            city = None
            state = None
            location_match = re.search(r'([^,]+),\s*([A-Z]{2})', location_text)
            if location_match:
                city = location_match.group(1).strip()
                state = location_match.group(2).strip()
            external_id_match = re.search(r'/jobs/(\d+)', href)
            external_id = external_id_match.group(1) if external_id_match else href
            events.append(ProviderJobEvent(
                source_name=source_name,
                external_id=external_id,
                source_url=href,
                title=text[:180],
                content=' '.join(part for part in [text, location_text] if part),
                company_name_raw=_extract_company_from_url(url),
                city_raw=city,
                state_raw=state,
                confidence=confidence,
            ))

    return events


register_provider('greenhouse_jobs', fetch_jobs_from_greenhouse_html)
