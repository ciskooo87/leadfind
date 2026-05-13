from bs4 import BeautifulSoup

from app.collectors.http_client import fetch_text
from app.collectors.provider_registry import register_provider


def fetch_news_from_generic_html(
    url: str,
    item_selector: str,
    title_selector: str,
    content_selector: str,
    company_selector: str | None = None,
    city_selector: str | None = None,
    state_selector: str | None = None,
    link_selector: str | None = None,
    website_selector: str | None = None,
) -> list[dict]:
    html = fetch_text(url)
    soup = BeautifulSoup(html, 'html.parser')
    items: list[dict] = []

    for index, node in enumerate(soup.select(item_selector), start=1):
        title_node = node.select_one(title_selector)
        content_node = node.select_one(content_selector)
        company_node = node.select_one(company_selector) if company_selector else None
        city_node = node.select_one(city_selector) if city_selector else None
        state_node = node.select_one(state_selector) if state_selector else None
        link_node = node.select_one(link_selector) if link_selector else None
        website_node = node.select_one(website_selector) if website_selector else None

        title = title_node.get_text(' ', strip=True) if title_node else None
        content = content_node.get_text(' ', strip=True) if content_node else ''
        if not content:
            continue

        items.append({
            'external_id': (link_node.get('href') if link_node else None) or f'news-{index}',
            'source_url': link_node.get('href') if link_node else None,
            'title': title,
            'content': content,
            'company_name_raw': company_node.get_text(' ', strip=True) if company_node else None,
            'company_website_raw': website_node.get('href') if website_node else None,
            'city_raw': city_node.get_text(' ', strip=True) if city_node else None,
            'state_raw': state_node.get_text(' ', strip=True) if state_node else None,
        })

    return items


register_provider('generic_html_news', fetch_news_from_generic_html)
