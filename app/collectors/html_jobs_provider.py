from bs4 import BeautifulSoup

from app.collectors.http_client import fetch_text
from app.collectors.provider_models import ProviderJobEvent
from app.collectors.provider_registry import register_provider


def fetch_jobs_from_generic_html(
    url: str,
    source_name: str,
    listing_selector: str,
    title_selector: str,
    content_selector: str,
    company_selector: str | None = None,
    city_selector: str | None = None,
    state_selector: str | None = None,
    link_selector: str | None = None,
    website_selector: str | None = None,
    confidence: float = 0.72,
) -> list[ProviderJobEvent]:
    html = fetch_text(url)
    soup = BeautifulSoup(html, "html.parser")
    events: list[ProviderJobEvent] = []

    for index, node in enumerate(soup.select(listing_selector), start=1):
        title_node = node.select_one(title_selector)
        content_node = node.select_one(content_selector)
        company_node = node.select_one(company_selector) if company_selector else None
        city_node = node.select_one(city_selector) if city_selector else None
        state_node = node.select_one(state_selector) if state_selector else None
        link_node = node.select_one(link_selector) if link_selector else None
        website_node = node.select_one(website_selector) if website_selector else None

        title = title_node.get_text(" ", strip=True) if title_node else None
        content = content_node.get_text(" ", strip=True) if content_node else ""
        if not content:
            continue

        company_name = company_node.get_text(" ", strip=True) if company_node else None
        city = city_node.get_text(" ", strip=True) if city_node else None
        state = state_node.get_text(" ", strip=True) if state_node else None
        href = link_node.get("href") if link_node else None
        company_website = website_node.get("href") if website_node else None

        external_id = href or f"{source_name.lower().replace(' ', '-')}-{index}"
        events.append(
            ProviderJobEvent(
                source_name=source_name,
                external_id=external_id,
                source_url=href,
                title=title,
                content=content,
                company_name_raw=company_name,
                company_website_raw=company_website,
                city_raw=city,
                state_raw=state,
                confidence=confidence,
            )
        )

    return events


register_provider("generic_html_jobs", fetch_jobs_from_generic_html)
