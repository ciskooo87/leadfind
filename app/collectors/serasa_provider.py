from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.collectors.http_client import fetch_text
from app.collectors.provider_registry import register_provider


def fetch_serasa_like_html(url: str) -> list[dict]:
    html = fetch_text(url)
    soup = BeautifulSoup(html, 'html.parser')
    items: list[dict] = []
    selectors = ['[data-testid="credit-card"]', '.credit-card', 'article', '.financial-card']
    seen_links: set[str] = set()

    for selector in selectors:
        for index, node in enumerate(soup.select(selector), start=1):
            title_node = node.select_one('h1, h2, h3, [data-testid="credit-title"]')
            content_node = node.select_one('p, .description, .content, [data-testid="credit-description"]')
            company_node = node.select_one('.company, .brand-name, [data-testid="company-name"]')
            city_node = node.select_one('.city, [data-testid="city"]')
            state_node = node.select_one('.state, [data-testid="state"]')
            link_node = node.select_one('a[href]')
            website_node = node.select_one('.company-site, [data-testid="company-site"]')

            title = title_node.get_text(' ', strip=True) if title_node else None
            content = content_node.get_text(' ', strip=True) if content_node else ''
            company = company_node.get_text(' ', strip=True) if company_node else None
            city = city_node.get_text(' ', strip=True) if city_node else None
            state = state_node.get_text(' ', strip=True) if state_node else None
            href = urljoin(url, link_node.get('href')) if link_node else None
            website = urljoin(url, website_node.get('href')) if website_node and website_node.get('href') else None

            if not content:
                continue
            if href and href in seen_links:
                continue
            if href:
                seen_links.add(href)

            items.append({
                'external_id': href or f'serasa-{index}',
                'source_url': href,
                'title': title,
                'content': content,
                'company_name_raw': company,
                'company_website_raw': website,
                'city_raw': city,
                'state_raw': state,
            })
        if items:
            break

    return items


register_provider('serasa_like', fetch_serasa_like_html)
