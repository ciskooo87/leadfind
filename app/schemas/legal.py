from pydantic import BaseModel, HttpUrl


class GenericHtmlLegalCollectRequest(BaseModel):
    url: HttpUrl
    source_name: str = 'JusBrasil'
    item_selector: str
    title_selector: str
    content_selector: str
    company_selector: str | None = None
    city_selector: str | None = None
    state_selector: str | None = None
    link_selector: str | None = None
    website_selector: str | None = None
    confidence: float = 0.82
    normalize_after_insert: bool = True
