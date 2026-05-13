from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.db.models import Company
from app.services.text_utils import normalize_text


LEGAL_SUFFIXES = {
    'ltda', 'sa', 's.a', 's/a', 'me', 'epp', 'eireli', 'holding', 'participacoes', 'participações'
}


def normalize_domain(url: str | None) -> str:
    if not url:
        return ''
    parsed = urlparse(url if '://' in url else f'https://{url}')
    host = (parsed.netloc or parsed.path).lower().strip()
    if host.startswith('www.'):
        host = host[4:]
    return host.rstrip('/')


def normalize_company_token(name: str | None) -> str:
    normalized = normalize_text(name)
    parts = [part for part in normalized.replace('/', ' ').replace('-', ' ').split() if part and part not in LEGAL_SUFFIXES]
    return ' '.join(parts)


def match_company(
    db: Session,
    company_name: str | None = None,
    website: str | None = None,
    city: str | None = None,
    state: str | None = None,
    cnpj_root: str | None = None,
) -> Company | None:
    normalized_domain = normalize_domain(website)
    normalized_name = normalize_company_token(company_name)
    normalized_city = normalize_text(city)
    normalized_state = normalize_text(state)

    companies = db.query(Company).all()

    if cnpj_root:
        for company in companies:
            if company.cnpj_root and company.cnpj_root == cnpj_root:
                return company

    if normalized_domain:
        for company in companies:
            if normalize_domain(company.website) == normalized_domain:
                return company

    if normalized_name:
        exact_candidates: list[Company] = []
        partial_candidates: list[Company] = []
        for company in companies:
            legal = normalize_company_token(company.legal_name)
            trade = normalize_company_token(company.trade_name)
            names = {legal, trade}
            if normalized_name in names:
                exact_candidates.append(company)
                continue
            if normalized_name and any(normalized_name in candidate or candidate in normalized_name for candidate in names if candidate):
                partial_candidates.append(company)

        for candidate in exact_candidates + partial_candidates:
            company_city = normalize_text(candidate.city)
            company_state = normalize_text(candidate.state)
            city_ok = not normalized_city or normalized_city == company_city
            state_ok = not normalized_state or normalized_state == company_state
            if city_ok and state_ok:
                return candidate

        if exact_candidates:
            return exact_candidates[0]
        if partial_candidates:
            return partial_candidates[0]

    return None
