import json

from sqlalchemy.orm import Session

from app.db.models import Company, RawEvent
from app.services.company_resolution import normalize_company_token, normalize_domain


def _load_json_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return [item for item in parsed if isinstance(item, str) and item.strip()]


def _dump_json_list(items: list[str]) -> str:
    return json.dumps(items, ensure_ascii=False)


def enrich_company_from_raw_event(db: Session, company: Company, raw_event: RawEvent) -> bool:
    changed = False

    aliases = _load_json_list(company.aliases_json)
    domains = _load_json_list(company.domains_json)

    known_name_tokens = {
        normalize_company_token(company.legal_name),
        normalize_company_token(company.trade_name),
        *[normalize_company_token(alias) for alias in aliases],
    }
    known_domains = {normalize_domain(company.website), *[normalize_domain(domain) for domain in domains]}

    candidate_aliases = [raw_event.company_name_raw]
    for alias in candidate_aliases:
        if not alias or not alias.strip():
            continue
        normalized = normalize_company_token(alias)
        if not normalized or normalized in known_name_tokens:
            continue
        aliases.append(alias.strip())
        known_name_tokens.add(normalized)
        changed = True

    candidate_domains = [raw_event.company_website_raw, raw_event.source_url]
    for domain_candidate in candidate_domains:
        normalized_domain = normalize_domain(domain_candidate)
        if not normalized_domain or normalized_domain in known_domains:
            continue
        if company.website and normalized_domain == normalize_domain(company.website):
            continue
        domains.append(normalized_domain)
        known_domains.add(normalized_domain)
        changed = True

    if changed:
        company.aliases_json = _dump_json_list(aliases)
        company.domains_json = _dump_json_list(domains)
        db.add(company)

    return changed
