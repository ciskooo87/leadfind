from pydantic import BaseModel, HttpUrl


class RegionalNewsCollectRequest(BaseModel):
    url: HttpUrl
    source_name: str = 'Notícias Regionais'
    confidence: float = 0.78
    normalize_after_insert: bool = True
