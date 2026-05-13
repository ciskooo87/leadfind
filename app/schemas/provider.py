from pydantic import BaseModel, HttpUrl


class GenericHtmlJobsCollectRequest(BaseModel):
    url: HttpUrl
    source_name: str = "LinkedIn Jobs"
    listing_selector: str
    title_selector: str
    content_selector: str
    company_selector: str | None = None
    city_selector: str | None = None
    state_selector: str | None = None
    link_selector: str | None = None
    website_selector: str | None = None
    confidence: float = 0.72
    normalize_after_insert: bool = True


class JsonJobsCollectRequest(BaseModel):
    url: HttpUrl
    source_name: str = "Indeed"
    items_path: str
    title_path: str
    content_path: str
    company_path: str | None = None
    city_path: str | None = None
    state_path: str | None = None
    link_path: str | None = None
    website_path: str | None = None
    external_id_path: str | None = None
    confidence: float = 0.78
    normalize_after_insert: bool = True


class JsonLdJobsCollectRequest(BaseModel):
    url: HttpUrl
    source_name: str = "Corporate Careers"
    confidence: float = 0.84
    normalize_after_insert: bool = True
