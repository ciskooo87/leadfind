from datetime import datetime
from pydantic import BaseModel, HttpUrl


class RawEventCreate(BaseModel):
    source_name: str
    external_id: str | None = None
    source_url: HttpUrl | None = None
    title: str | None = None
    content: str
    company_name_raw: str | None = None
    city_raw: str | None = None
    state_raw: str | None = None
    occurred_at: datetime | None = None
    confidence: float = 0.7


class RawEventBatchCreate(BaseModel):
    events: list[RawEventCreate]
    normalize_after_insert: bool = True


class RawEventRead(BaseModel):
    id: int
    source_id: int
    company_id: int | None = None
    external_id: str | None = None
    source_url: str | None = None
    title: str | None = None
    content: str
    company_name_raw: str | None = None
    city_raw: str | None = None
    state_raw: str | None = None
    occurred_at: datetime
    normalized_status: str
    normalized_signal_type: str | None = None
    confidence: float

    model_config = {"from_attributes": True}
