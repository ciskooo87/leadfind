from datetime import datetime
from pydantic import BaseModel, HttpUrl


class SignalCreate(BaseModel):
    company_id: int
    category: str
    signal_type: str
    source_name: str
    source_url: HttpUrl | None = None
    excerpt: str
    detected_at: datetime | None = None
    confidence: float = 0.7
    weight_override: float | None = None


class SignalRead(BaseModel):
    id: int
    company_id: int
    category: str
    signal_type: str
    source_name: str
    source_url: str | None = None
    excerpt: str
    detected_at: datetime
    confidence: float
    weight_override: float | None = None

    model_config = {"from_attributes": True}
