from pydantic import BaseModel, HttpUrl


class FormalActsCollectRequest(BaseModel):
    url: HttpUrl
    source_name: str = 'Atos Formais'
    confidence: float = 0.82
    normalize_after_insert: bool = True
