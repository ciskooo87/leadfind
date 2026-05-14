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
        if first and first not in {'en-us', 'careers', 'job'}:
            return first.replace('-', ' ') or None
    if host:
        subdomain = host.split('.')[0]
        if subdomain not in {'wd3', 'wd5', 'wd1', 'careers'}:
            return subdomain.replace('-', ' ').strip() or None
    return None


def fetch_jobs_from_workday_html(url: str, source_name: str = 'Workday', confidence: float = 0.85) -> list[ProviderJobEvent]:
    html = fetch_text(url)
    soup = BeautifulSoup(html, 'html.parser')
    events: list[ProviderJobEvent] = []
    seen_urls: set[str] = set()

    selectors = [
        'a[href*="/job/"]',
        '[data-automation-id="jobTitle"]',
        'a[data-automation-id="jobTitle"]',
    ]

    for selector in selectors:
        for node in soup.select(selector):
            href = _absolute_url(url, node.get('href') if hasattr(node, 'get') else None)
            text = node.get_text(' ', strip=True)
            if not href or not text or href in seen_urls:
                continue
            if '/job/' not in href:
                continue
            seen_urls.add(href)

            container = node.find_parent(['li', 'div', 'section', 'article']) if hasattr(node, 'find_parent') else None
            container_text = container.get_text(' ', strip=True) if container else text
            location_match = re.search(r'([A-ZÁÂÃÉÊÍÓÔÕÚÇ][\wÁÂÃÉÊÍÓÔÕÚÇáâãéêíóôõúç-]+),\s*([A-Z]{2})', container_text)
            city = location_match.group(1).strip() if location_match else None
            state = location_match.group(2).strip() if location_match else None
            external_id = href.rstrip('/').split('/')[-1]

            events.append(ProviderJobEvent(
                source_name=source_name,
                external_id=external_id,
                source_url=href,
                title=text[:180],
                content=container_text[:2000],
                company_name_raw=_extract_company_from_url(url),
                city_raw=city,
                state_raw=state,
                confidence=confidence,
            ))

    return events


register_provider('workday_jobs', fetch_jobs_from_workday_html)
