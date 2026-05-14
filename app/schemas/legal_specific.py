from pydantic import BaseModel, HttpUrl


class JusBrasilCollectRequest(BaseModel):
    url: HttpUrl
    source_name: str = 'JusBrasil'
    confidence: float = 0.84
    normalize_after_insert: bool = True
