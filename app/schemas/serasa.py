from pydantic import BaseModel, HttpUrl


class SerasaCollectRequest(BaseModel):
    url: HttpUrl
    source_name: str = 'Serasa'
    confidence: float = 0.84
    normalize_after_insert: bool = True
