from dataclasses import dataclass


@dataclass
class ProviderJobEvent:
    source_name: str
    external_id: str | None
    source_url: str | None
    title: str | None
    content: str
    company_name_raw: str | None = None
    company_website_raw: str | None = None
    city_raw: str | None = None
    state_raw: str | None = None
    confidence: float = 0.7
