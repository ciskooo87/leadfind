import json
from difflib import SequenceMatcher
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
    parts = [
        part
        for part in normalized.replace('/', ' ').replace('-', ' ').split()
        if part and part not in LEGAL_SUFFIXES
    ]
    return ' '.join(parts)


def _token_set(value: str) -> set[str]:
    return {part for part in value.split() if part}


def _name_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    left_tokens = _token_set(left)
    right_tokens = _token_set(right)
    if not left_tokens or not right_tokens:
        return 0.0

    overlap = len(left_tokens & right_tokens) / max(len(left_tokens | right_tokens), 1)
    ratio = SequenceMatcher(None, left, right).ratio()
    contains_bonus = 0.12 if left in right or right in left else 0.0
    return min(max(ratio, overlap) + contains_bonus, 1.0)


def _load_json_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return [item for item in parsed if isinstance(item, str) and item.strip()]


def _company_aliases(company: Company) -> list[str]:
    return _load_json_list(getattr(company, 'aliases_json', '[]'))


def _company_domains(company: Company) -> list[str]:
    domains = [normalize_domain(company.website)] if company.website else []
    domains.extend(normalize_domain(item) for item in _load_json_list(getattr(company, 'domains_json', '[]')))
    return [item for item in domains if item]


def _best_name_score(input_name: str, company: Company) -> float:
    candidates = [
        normalize_company_token(company.legal_name),
        normalize_company_token(company.trade_name),
        *[normalize_company_token(alias) for alias in _company_aliases(company)],
    ]
    return max((_name_similarity(input_name, candidate) for candidate in candidates if candidate), default=0.0)


def _location_score(company: Company, normalized_city: str, normalized_state: str) -> float:
    company_city = normalize_text(company.city)
    company_state = normalize_text(company.state)

    score = 0.0
    if normalized_city and company_city:
        if normalized_city == company_city:
            score += 0.2
        elif normalized_city in company_city or company_city in normalized_city:
            score += 0.08

    if normalized_state and company_state:
        if normalized_state == company_state:
            score += 0.1

    return score


def _domain_score(input_domain: str, company: Company) -> float:
    if not input_domain:
        return 0.0
    for company_domain in _company_domains(company):
        if input_domain == company_domain:
            return 1.0
        if input_domain.endswith(company_domain) or company_domain.endswith(input_domain):
            return 0.8
    return 0.0


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
        exact_domain_matches = [company for company in companies if _domain_score(normalized_domain, company) >= 1.0]
        if len(exact_domain_matches) == 1:
            return exact_domain_matches[0]
        if len(exact_domain_matches) > 1:
            scored = sorted(
                exact_domain_matches,
                key=lambda company: _location_score(company, normalized_city, normalized_state),
                reverse=True,
            )
            return scored[0]

    best_company: Company | None = None
    best_score = 0.0

    for company in companies:
        score = 0.0
        domain_score = _domain_score(normalized_domain, company)
        if domain_score:
            score += domain_score

        name_score = _best_name_score(normalized_name, company)
        if normalized_name:
            score += name_score

        score += _location_score(company, normalized_city, normalized_state)

        if normalized_name and name_score < 0.45 and domain_score < 0.8:
            continue

        if score > best_score:
            best_company = company
            best_score = score

    threshold = 0.75 if normalized_domain else 0.9 if normalized_name else 0.0
    if best_company and best_score >= threshold:
        return best_company

    return None
