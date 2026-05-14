from pydantic import BaseModel, HttpUrl


class ReclameAquiCollectRequest(BaseModel):
    url: HttpUrl
    source_name: str = 'Reclamações Operacionais'
    confidence: float = 0.8
    normalize_after_insert: bool = True
