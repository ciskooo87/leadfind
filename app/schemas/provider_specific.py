from pydantic import BaseModel, HttpUrl


class GupyJobsCollectRequest(BaseModel):
    url: HttpUrl
    source_name: str = 'Gupy'
    confidence: float = 0.84
    normalize_after_insert: bool = True


class GreenhouseJobsCollectRequest(BaseModel):
    url: HttpUrl
    source_name: str = 'Greenhouse'
    confidence: float = 0.85
    normalize_after_insert: bool = True


class LeverJobsCollectRequest(BaseModel):
    url: HttpUrl
    source_name: str = 'Lever'
    confidence: float = 0.85
    normalize_after_insert: bool = True
